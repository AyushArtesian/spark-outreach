"""
Apollo API integration for prospect discovery.

This client intentionally uses only endpoint families that are available for the
current scoped API key:
- POST /organizations/search
- GET /organizations/enrich
- GET /organizations/{organization_id}/job_postings
- POST /contacts/search
- POST /accounts/search
"""

import asyncio
import json
import re
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urlparse

import aiohttp

from app.config import settings
from app.services.web_scraper import _normalize_location_text


DEFAULT_CONTACT_TITLES = [
    "Founder",
    "Co-Founder",
    "CEO",
    "CTO",
    "VP Engineering",
    "Head of Engineering",
    "Engineering Manager",
    "Product Manager",
    "IT Manager",
    "Digital Transformation Manager",
]

DEFAULT_CONTACT_SENIORITIES = [
    "owner",
    "founder",
    "c_suite",
    "vp",
    "head",
    "director",
    "manager",
]


def _safe_str(value: Any) -> str:
    return str(value or "").strip()


def _canonical_domain(value: str) -> str:
    raw = _safe_str(value).lower()
    if not raw:
        return ""

    if "://" in raw:
        host = (urlparse(raw).netloc or "").lower()
    else:
        host = raw.split("/", 1)[0]

    host = host.split(":", 1)[0].replace("www.", "").replace("m.", "")
    if not host:
        return ""

    parts = [p for p in host.split(".") if p]
    if len(parts) <= 2:
        return host

    if parts[-2] == "co" and parts[-1] in {"in", "uk", "au", "nz", "jp"}:
        return ".".join(parts[-3:])

    return ".".join(parts[-2:])


def _clean_search_keywords(value: str) -> str:
    text = _safe_str(value).lower()
    if not text:
        return ""

    # Remove common filter scaffolding phrases that pollute Apollo q_keywords.
    text = re.sub(r"\bin\s+all\s+industries\b", " ", text)
    text = re.sub(r"\bwith\s+size\s+all\s+sizes\b", " ", text)
    text = re.sub(r"\ball\s+industries\b", " ", text)
    text = re.sub(r"\ball\s+sizes\b", " ", text)

    text = re.sub(r"\b(find|search|companies|people|contacts|located|near|around|that|need)\b", " ", text)
    text = re.sub(r"[^a-z0-9\s]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _map_company_sizes(company_sizes: Optional[List[str]]) -> List[str]:
    mapping = {
        "1-10": "1,10",
        "11-50": "11,50",
        "51-200": "51,200",
        "200-1000": "200,1000",
        "1000+": "1000,100000",
    }
    ranges: List[str] = []
    for item in company_sizes or []:
        normalized = _safe_str(item)
        if normalized in mapping:
            ranges.append(mapping[normalized])
    return list(dict.fromkeys(ranges))


def _dedupe_key(prospect: Dict[str, Any]) -> str:
    person_id = _safe_str(prospect.get("apollo_person_id"))
    if person_id:
        return f"person:{person_id}"

    email = _safe_str(prospect.get("email")).lower()
    if email:
        return f"email:{email}"

    domain = _safe_str(prospect.get("domain")).lower()
    if domain:
        return f"domain:{domain}"

    name = _safe_str(prospect.get("name")).lower()
    company = _safe_str(prospect.get("company")).lower()
    if name or company:
        return f"identity:{company}|{name}"

    return ""


class ApolloService:
    """Client wrapper for Apollo organization/contact discovery."""

    def __init__(self) -> None:
        self.base_url = settings.APOLLO_BASE_URL.rstrip("/")
        self.access_blocked_reason = ""
        self.access_blocked_logged = False
        self.credits_exhausted_reason = ""
        self.credits_exhausted_logged = False
        self.last_run_credit_exhausted = False

    @property
    def enabled(self) -> bool:
        return bool(_safe_str(settings.APOLLO_API_KEY))

    def _headers(self, include_json_content: bool = True) -> Dict[str, str]:
        headers = {
            "x-api-key": str(settings.APOLLO_API_KEY),
            "Accept": "application/json",
            "Cache-Control": "no-cache",
        }
        if include_json_content:
            headers["Content-Type"] = "application/json"
        return headers

    @staticmethod
    def _strip_empty(payload: Dict[str, Any]) -> Dict[str, Any]:
        return {
            key: value
            for key, value in payload.items()
            if value not in (None, "", [], {})
        }

    async def _request_json(
        self,
        session: aiohttp.ClientSession,
        method: str,
        path: str,
        payload: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        timeout_seconds: int = 20,
        retries: int = 2,
    ) -> Optional[Dict[str, Any]]:
        url = f"{self.base_url}{path}"
        timeout_cfg = aiohttp.ClientTimeout(total=timeout_seconds)
        method_name = method.upper()

        for attempt in range(retries + 1):
            try:
                async with session.request(
                    method_name,
                    url,
                    headers=self._headers(include_json_content=(method_name != "GET")),
                    json=payload if method_name != "GET" else None,
                    params=params,
                    timeout=timeout_cfg,
                ) as response:
                    if response.status == 429:
                        wait = 1.2 * (2 ** attempt)
                        print(f"[APOLLO] Rate limited (429). retry_in={wait:.1f}s path={path}")
                        await asyncio.sleep(wait)
                        continue

                    if response.status in (401, 403):
                        preview = await response.text()
                        error_code = ""
                        lowered_preview = preview.lower()
                        try:
                            parsed = json.loads(preview)
                            error_code = str(parsed.get("error_code") or "").strip()
                        except Exception:
                            error_code = ""

                        if "insufficient credits" in lowered_preview or "lead credits" in lowered_preview:
                            self.credits_exhausted_reason = "Apollo credits exhausted."
                            self.last_run_credit_exhausted = True
                            if not self.credits_exhausted_logged:
                                print("[APOLLO] Credits exhausted. Falling back to non-Apollo discovery sources.")
                                self.credits_exhausted_logged = True
                            return None

                        if response.status == 403 and error_code == "API_INACCESSIBLE":
                            self.access_blocked_reason = f"Apollo plan cannot access endpoint {path}."
                            print(
                                "[APOLLO] Endpoint blocked by plan access. "
                                f"path={path} error_code={error_code}"
                            )
                        else:
                            print(
                                f"[APOLLO] Auth error status={response.status} "
                                f"path={path} body={preview[:220]}"
                            )
                        return None

                    if response.status == 422:
                        preview = await response.text()
                        lowered_preview = preview.lower()
                        if "insufficient credits" in lowered_preview or "lead credits" in lowered_preview:
                            self.credits_exhausted_reason = "Apollo credits exhausted."
                            self.last_run_credit_exhausted = True
                            if not self.credits_exhausted_logged:
                                print("[APOLLO] Credits exhausted. Falling back to non-Apollo discovery sources.")
                                self.credits_exhausted_logged = True
                            return None
                        print(f"[APOLLO] Validation error path={path} body={preview[:260]}")
                        return None

                    if response.status < 200 or response.status >= 300:
                        preview = await response.text()
                        print(
                            f"[APOLLO] Request failed status={response.status} "
                            f"path={path} body={preview[:220]}"
                        )
                        return None

                    data = await response.json(content_type=None)
                    if isinstance(data, dict):
                        return data
                    return None
            except asyncio.TimeoutError:
                if attempt < retries:
                    wait = 1.0 * (2 ** attempt)
                    print(f"[APOLLO] Timeout path={path}. retry_in={wait:.1f}s")
                    await asyncio.sleep(wait)
                    continue
            except Exception as e:
                print(f"[APOLLO] Request error path={path}: {e}")
                if attempt < retries:
                    await asyncio.sleep(0.8 * (2 ** attempt))
                    continue
                return None

        return None

    async def _post_json(
        self,
        session: aiohttp.ClientSession,
        path: str,
        payload: Dict[str, Any],
        timeout_seconds: int = 20,
        retries: int = 2,
    ) -> Optional[Dict[str, Any]]:
        return await self._request_json(
            session=session,
            method="POST",
            path=path,
            payload=payload,
            timeout_seconds=timeout_seconds,
            retries=retries,
        )

    async def _get_json(
        self,
        session: aiohttp.ClientSession,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        timeout_seconds: int = 20,
        retries: int = 2,
    ) -> Optional[Dict[str, Any]]:
        return await self._request_json(
            session=session,
            method="GET",
            path=path,
            params=params,
            timeout_seconds=timeout_seconds,
            retries=retries,
        )

    @staticmethod
    def _location_from_parts(parts: List[str]) -> str:
        joined = ", ".join([p for p in parts if p])
        return _normalize_location_text(joined.lower()) if joined else ""

    @staticmethod
    def _extract_org_phone(organization: Dict[str, Any]) -> str:
        primary_phone = organization.get("primary_phone")
        if isinstance(primary_phone, dict):
            number = _safe_str(primary_phone.get("number") or primary_phone.get("sanitized_number"))
            if number:
                return number
        return _safe_str(organization.get("phone") or organization.get("sanitized_phone"))

    def _extract_org_location(self, organization: Dict[str, Any]) -> str:
        return self._location_from_parts(
            [
                _safe_str(organization.get("city")),
                _safe_str(organization.get("state")),
                _safe_str(organization.get("country")),
            ]
        )

    def _extract_contact_location(
        self,
        contact: Dict[str, Any],
        organization: Dict[str, Any],
    ) -> str:
        return self._location_from_parts(
            [
                _safe_str(contact.get("city")),
                _safe_str(contact.get("state")),
                _safe_str(contact.get("country")),
                _safe_str(contact.get("present_raw_address")),
                _safe_str(organization.get("city")),
                _safe_str(organization.get("state")),
                _safe_str(organization.get("country")),
            ]
        )

    @staticmethod
    def _posting_summary(job_postings: List[Dict[str, Any]]) -> str:
        if not job_postings:
            return ""
        titles = [
            _safe_str(item.get("title"))
            for item in job_postings
            if isinstance(item, dict) and _safe_str(item.get("title"))
        ]
        if not titles:
            return ""

        unique_titles = list(dict.fromkeys(titles))
        preview = "; ".join(unique_titles[:2])
        return f"Hiring signals: {len(titles)} recent job postings ({preview})"

    def _search_keywords(
        self,
        query: str,
        industry: Optional[str],
        service_focus: Optional[List[str]],
    ) -> str:
        normalized_industry = _safe_str(industry).lower()
        service_tokens = [_safe_str(item).lower() for item in (service_focus or []) if _safe_str(item)]
        parts = [
            _clean_search_keywords(query),
            normalized_industry if normalized_industry and normalized_industry != "all" else "",
            " ".join(service_tokens[:4]),
        ]
        result = " ".join([p for p in parts if p]).strip()
        
        # Apollo's q_keywords field has a 255-character limit; truncate if needed
        max_length = 200
        if len(result) > max_length:
            # Try to truncate at word boundary
            truncated = result[:max_length]
            last_space = truncated.rfind(' ')
            if last_space > 50:
                result = truncated[:last_space]
            else:
                result = truncated
            print(f"[APOLLO] Query truncated to {max_length}c: '{result}'")
        
        return result

    def _build_organizations_payload(
        self,
        query: str,
        location: Optional[str],
        industry: Optional[str],
        service_focus: Optional[List[str]],
        company_sizes: Optional[List[str]],
        page: int,
        per_page: int,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "q_keywords": self._search_keywords(query, industry, service_focus),
            "organization_locations": [
                _normalize_location_text(_safe_str(location).lower())
            ]
            if _safe_str(location)
            else None,
            "organization_num_employees_ranges": _map_company_sizes(company_sizes),
            "page": page,
            "per_page": per_page,
            "sort_ascending": False,
        }
        return self._strip_empty(payload)

    def _build_contacts_payload(
        self,
        query: str,
        location: Optional[str],
        organization_id: Optional[str],
        page: int,
        per_page: int,
    ) -> Dict[str, Any]:
        normalized_location = _normalize_location_text(_safe_str(location).lower())
        payload: Dict[str, Any] = {
            "q_keywords": _clean_search_keywords(query),
            "organization_ids": [_safe_str(organization_id)] if _safe_str(organization_id) else None,
            "organization_locations": [normalized_location] if normalized_location else None,
            "person_titles": DEFAULT_CONTACT_TITLES,
            "person_seniorities": DEFAULT_CONTACT_SENIORITIES,
            "page": page,
            "per_page": per_page,
            "sort_ascending": False,
        }
        # Restricting by q_keywords and title is less useful once organization_ids are set.
        if _safe_str(organization_id):
            payload.pop("q_keywords", None)
            payload.pop("person_titles", None)
            payload.pop("person_seniorities", None)
        return self._strip_empty(payload)

    def _build_accounts_payload(self, query: str, page: int, per_page: int) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "q_organization_name": _clean_search_keywords(query),
            "page": page,
            "per_page": per_page,
            "sort_ascending": False,
        }
        return self._strip_empty(payload)

    def _prospect_from_organization(
        self,
        organization: Dict[str, Any],
        query: str,
        job_postings: Optional[List[Dict[str, Any]]] = None,
        enriched_organization: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        primary = enriched_organization if isinstance(enriched_organization, dict) else organization
        fallback = organization if isinstance(organization, dict) else {}

        company_name = _safe_str(primary.get("name") or fallback.get("name"))
        website_url = _safe_str(primary.get("website_url") or fallback.get("website_url"))
        domain = _canonical_domain(
            _safe_str(primary.get("primary_domain") or fallback.get("primary_domain") or primary.get("domain") or fallback.get("domain"))
            or website_url
        )
        if not company_name and not domain:
            return None

        industry = _safe_str(primary.get("industry") or fallback.get("industry"))
        location = self._extract_org_location(primary or fallback)
        posting_hint = self._posting_summary(job_postings or [])
        snippet_parts = [
            f"Company profile: {company_name}" if company_name else "",
            _clean_search_keywords(query),
            f"Industry: {industry}" if industry else "",
            f"Location: {location}" if location else "",
            posting_hint,
        ]

        return {
            "source": "apollo_organization_search",
            "name": company_name or domain or "Unknown",
            "email": "",
            "phone": self._extract_org_phone(primary) or self._extract_org_phone(fallback),
            "job_title": "Hiring Team",
            "company": company_name or domain,
            "industry": industry,
            "url": website_url or (f"https://{domain}" if domain else ""),
            "domain": domain,
            "title": company_name,
            "snippet": " | ".join([p for p in snippet_parts if p])[:450],
            "location": location,
            "apollo_person_id": "",
            "apollo_organization_id": _safe_str(primary.get("id") or fallback.get("id")),
            "linkedin_url": _safe_str(primary.get("linkedin_url") or fallback.get("linkedin_url")),
            "email_status": "",
        }

    def _prospect_from_contact(
        self,
        contact: Dict[str, Any],
        query: str,
        organization_fallback: Optional[Dict[str, Any]] = None,
        job_postings: Optional[List[Dict[str, Any]]] = None,
    ) -> Optional[Dict[str, Any]]:
        organization = contact.get("organization") if isinstance(contact.get("organization"), dict) else {}
        account = contact.get("account") if isinstance(contact.get("account"), dict) else {}
        fallback = organization_fallback if isinstance(organization_fallback, dict) else {}

        company_name = _safe_str(
            contact.get("organization_name")
            or organization.get("name")
            or fallback.get("name")
            or account.get("name")
        )
        website_url = _safe_str(
            organization.get("website_url")
            or fallback.get("website_url")
            or account.get("website_url")
        )
        domain = _canonical_domain(
            _safe_str(
                organization.get("primary_domain")
                or fallback.get("primary_domain")
                or account.get("domain")
            )
            or website_url
        )

        full_name = _safe_str(contact.get("name"))
        if not full_name:
            first_name = _safe_str(contact.get("first_name"))
            last_name = _safe_str(contact.get("last_name"))
            full_name = " ".join([p for p in [first_name, last_name] if p]).strip()

        if not full_name and not company_name and not domain:
            return None

        title = _safe_str(contact.get("title"))
        industry = _safe_str(organization.get("industry") or fallback.get("industry"))
        location = self._extract_contact_location(contact, organization or fallback)
        posting_hint = self._posting_summary(job_postings or [])
        snippet_parts = [
            f"{title} at {company_name}" if title and company_name else "",
            _clean_search_keywords(query),
            f"Industry: {industry}" if industry else "",
            f"Location: {location}" if location else "",
            posting_hint,
        ]

        return {
            "source": "apollo_contact_search",
            "name": full_name or company_name or "Unknown",
            "email": _safe_str(contact.get("email")),
            "phone": _safe_str(contact.get("phone") or contact.get("sanitized_phone")),
            "job_title": title,
            "company": company_name,
            "industry": industry,
            "url": website_url or (f"https://{domain}" if domain else _safe_str(contact.get("linkedin_url"))),
            "domain": domain,
            "title": title,
            "snippet": " | ".join([p for p in snippet_parts if p])[:450],
            "location": location,
            "apollo_person_id": _safe_str(contact.get("id") or contact.get("person_id")),
            "apollo_organization_id": _safe_str(contact.get("organization_id") or organization.get("id") or fallback.get("id")),
            "linkedin_url": _safe_str(contact.get("linkedin_url")),
            "email_status": _safe_str(contact.get("email_status")),
        }

    def _prospect_from_account(self, account: Dict[str, Any], query: str) -> Optional[Dict[str, Any]]:
        company_name = _safe_str(account.get("name"))
        domain = _canonical_domain(_safe_str(account.get("domain")))
        if not company_name and not domain:
            return None

        snippet_parts = [
            f"Team account: {company_name}" if company_name else "",
            _clean_search_keywords(query),
            "Apollo account search match",
        ]

        return {
            "source": "apollo_accounts_search",
            "name": company_name or domain or "Unknown",
            "email": "",
            "phone": _safe_str(account.get("phone") or account.get("sanitized_phone")),
            "job_title": "Buying Team",
            "company": company_name or domain,
            "industry": "",
            "url": f"https://{domain}" if domain else _safe_str(account.get("linkedin_url")),
            "domain": domain,
            "title": company_name,
            "snippet": " | ".join([p for p in snippet_parts if p])[:450],
            "location": "",
            "apollo_person_id": "",
            "apollo_organization_id": _safe_str(account.get("organization_id") or account.get("id")),
            "linkedin_url": _safe_str(account.get("linkedin_url")),
            "email_status": "",
        }

    @staticmethod
    def _add_unique(
        prospects: List[Dict[str, Any]],
        seen_keys: Set[str],
        prospect: Optional[Dict[str, Any]],
        max_results: int,
    ) -> bool:
        if not prospect or len(prospects) >= max_results:
            return False

        key = _dedupe_key(prospect)
        if not key or key in seen_keys:
            return False

        seen_keys.add(key)
        prospects.append(prospect)
        return True

    async def search_people(
        self,
        query: str,
        location: Optional[str] = None,
        industry: Optional[str] = None,
        service_focus: Optional[List[str]] = None,
        company_sizes: Optional[List[str]] = None,
        max_results: int = 20,
    ) -> List[Dict[str, Any]]:
        """Search Apollo entities and return lead-like prospects."""
        self.last_run_credit_exhausted = False

        if not self.enabled:
            print("[APOLLO] Skipped: APOLLO_API_KEY is not configured.")
            return []

        if self.credits_exhausted_reason:
            self.last_run_credit_exhausted = True
            if not self.credits_exhausted_logged:
                print("[APOLLO] Skipped: Apollo credits exhausted. Falling back to non-Apollo discovery sources.")
                self.credits_exhausted_logged = True
            return []

        if self.access_blocked_reason:
            if not self.access_blocked_logged:
                print(f"[APOLLO] Skipped: {self.access_blocked_reason}")
                self.access_blocked_logged = True
            return []

        max_results = max(1, min(100, int(max_results or 20)))
        org_page_size = min(12, max(5, max_results))
        max_pages = max(1, min(settings.APOLLO_MAX_PAGES, ((max_results - 1) // org_page_size) + 1))

        prospects: List[Dict[str, Any]] = []
        seen_keys: Set[str] = set()
        contacts_empty_streak = 0
        skip_contacts_for_run = False

        async with aiohttp.ClientSession() as session:
            for page in range(1, max_pages + 1):
                org_payload = self._build_organizations_payload(
                    query=query,
                    location=location,
                    industry=industry,
                    service_focus=service_focus,
                    company_sizes=company_sizes,
                    page=page,
                    per_page=org_page_size,
                )
                org_data = await self._post_json(
                    session,
                    "/organizations/search",
                    org_payload,
                    timeout_seconds=25,
                    retries=2,
                )
                if not org_data:
                    break

                organizations = org_data.get("organizations") if isinstance(org_data, dict) else None
                if not isinstance(organizations, list) or not organizations:
                    break

                for organization in organizations:
                    if not isinstance(organization, dict):
                        continue

                    org_id = _safe_str(organization.get("id"))
                    org_domain = _canonical_domain(
                        _safe_str(organization.get("primary_domain") or organization.get("website_url") or organization.get("domain"))
                    )

                    enriched_org: Dict[str, Any] = {}
                    if settings.APOLLO_ENRICHMENT_ENABLED and org_domain:
                        enrich_data = await self._get_json(
                            session,
                            "/organizations/enrich",
                            params={"domain": org_domain},
                            timeout_seconds=20,
                            retries=1,
                        )
                        if isinstance(enrich_data, dict) and isinstance(enrich_data.get("organization"), dict):
                            enriched_org = enrich_data.get("organization") or {}

                    job_postings: List[Dict[str, Any]] = []
                    if settings.APOLLO_ENRICHMENT_ENABLED and org_id:
                        jobs_data = await self._get_json(
                            session,
                            f"/organizations/{org_id}/job_postings",
                            params={"page": 1, "per_page": 3},
                            timeout_seconds=20,
                            retries=1,
                        )
                        if isinstance(jobs_data, dict) and isinstance(jobs_data.get("organization_job_postings"), list):
                            job_postings = jobs_data.get("organization_job_postings") or []

                    contacts_found_for_org = False
                    if not skip_contacts_for_run:
                        contacts_payload = self._build_contacts_payload(
                            query=query,
                            location=location,
                            organization_id=org_id,
                            page=1,
                            per_page=4,
                        )
                        contacts_data = await self._post_json(
                            session,
                            "/contacts/search",
                            contacts_payload,
                            timeout_seconds=20,
                            retries=1,
                        )
                        contacts = contacts_data.get("contacts") if isinstance(contacts_data, dict) else None
                        if isinstance(contacts, list) and contacts:
                            contacts_empty_streak = 0
                            for contact in contacts:
                                if not isinstance(contact, dict):
                                    continue
                                prospect = self._prospect_from_contact(
                                    contact=contact,
                                    query=query,
                                    organization_fallback=enriched_org or organization,
                                    job_postings=job_postings,
                                )
                                if self._add_unique(prospects, seen_keys, prospect, max_results):
                                    contacts_found_for_org = True
                                if len(prospects) >= max_results:
                                    break
                        else:
                            contacts_empty_streak += 1
                            if contacts_empty_streak >= 4:
                                skip_contacts_for_run = True
                                print(
                                    "[APOLLO] contacts/search returned empty repeatedly; "
                                    "skipping contact lookup for remaining organizations in this run."
                                )

                    if len(prospects) >= max_results:
                        break

                    if not contacts_found_for_org:
                        org_prospect = self._prospect_from_organization(
                            organization=organization,
                            query=query,
                            job_postings=job_postings,
                            enriched_organization=enriched_org,
                        )
                        self._add_unique(prospects, seen_keys, org_prospect, max_results)

                    if len(prospects) >= max_results:
                        break

                if len(prospects) >= max_results:
                    break
                if len(organizations) < org_page_size:
                    break

            # Optional fallback: include team account records if still under target.
            if len(prospects) < max_results:
                remaining = max_results - len(prospects)
                accounts_payload = self._build_accounts_payload(
                    query=query,
                    page=1,
                    per_page=min(25, max(5, remaining)),
                )
                accounts_data = await self._post_json(
                    session,
                    "/accounts/search",
                    accounts_payload,
                    timeout_seconds=20,
                    retries=1,
                )
                accounts = accounts_data.get("accounts") if isinstance(accounts_data, dict) else None
                if isinstance(accounts, list):
                    for account in accounts:
                        if not isinstance(account, dict):
                            continue
                        account_prospect = self._prospect_from_account(account=account, query=query)
                        self._add_unique(prospects, seen_keys, account_prospect, max_results)
                        if len(prospects) >= max_results:
                            break

        print(
            "[APOLLO] "
            f"query='{_clean_search_keywords(query)[:60]}' "
            f"location='{_safe_str(location)}' "
            f"results={len(prospects)}"
        )
        return prospects[:max_results]


apollo_service = ApolloService()
