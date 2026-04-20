"""Async job board intent discovery service."""

import asyncio
import json
import random
import re
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs, quote_plus, unquote, urlparse

import aiohttp
from bs4 import BeautifulSoup  # type: ignore[import-not-found]

from app.config import settings
from app.services.service_catalog import build_job_keywords


USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
]


class JobBoardService:
    """Discover high-intent buyer companies via active hiring signals."""

    def __init__(self) -> None:
        self.request_timeout = aiohttp.ClientTimeout(total=18)

    @staticmethod
    def _clean_text(value: Any) -> str:
        return re.sub(r"\s+", " ", str(value or "").strip())

    @staticmethod
    def _slugify(value: str) -> str:
        cleaned = re.sub(r"[^a-z0-9]+", "-", str(value or "").strip().lower())
        return cleaned.strip("-")

    @staticmethod
    def _looks_like_website(value: str) -> bool:
        text = str(value or "").strip().lower()
        return bool(text and ("." in text or text.startswith("http")))

    @staticmethod
    def _normalize_website(value: str) -> str:
        website = JobBoardService._clean_text(value)
        if not website:
            return ""
        if website.startswith("/"):
            return ""
        if not website.startswith(("http://", "https://")):
            website = f"https://{website}"
        parsed = urlparse(website)
        if not parsed.netloc:
            return ""
        return f"{parsed.scheme}://{parsed.netloc}".rstrip("/")

    @staticmethod
    def _normalize_company_key(company_name: str) -> str:
        normalized = re.sub(r"[^a-z0-9]+", " ", str(company_name or "").strip().lower())
        normalized = re.sub(
            r"\b(inc|llc|ltd|limited|pvt|private|technologies|technology|solutions|systems|services|corp|co|company)\b",
            " ",
            normalized,
        )
        return re.sub(r"\s+", " ", normalized).strip()

    def _build_headers(self) -> Dict[str, str]:
        return {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Referer": "https://www.google.com/",
        }

    async def _fetch_html(self, session: aiohttp.ClientSession, url: str) -> str:
        await asyncio.sleep(random.uniform(1.0, 3.0))
        for attempt in range(3):
            try:
                async with session.get(url, headers=self._build_headers(), timeout=self.request_timeout) as response:
                    if response.status == 429:
                        await asyncio.sleep(1.5 * (attempt + 1))
                        continue
                    if response.status >= 400:
                        return ""
                    return await response.text(errors="ignore")
            except Exception as exc:
                if attempt == 2:
                    print(f"[JOBBOARD] fetch failed for {url}: {exc}")
                await asyncio.sleep(0.8 * (attempt + 1))
        return ""

    def _buyer_intent_keywords(self, service: str) -> List[str]:
        """Generate search keywords to find BUYERS of this service (not job postings)"""
        normalized_service = self._clean_text(service)
        if not normalized_service:
            return []

        keywords: List[str] = [
            normalized_service,
            f"{normalized_service} implementation partner",
            f"looking for {normalized_service}",
            f"{normalized_service} vendor",
            f"{normalized_service} consulting",
            f"hire {normalized_service} firm",
        ]

        # Add a few deterministic job-derived variants to improve board hit rates.
        for item in build_job_keywords(normalized_service, max_keywords=4):
            cleaned = self._clean_text(item)
            if cleaned:
                keywords.append(cleaned)

        deduped: List[str] = []
        seen = set()
        for item in keywords:
            key = item.lower()
            if key in seen:
                continue
            seen.add(key)
            deduped.append(item)
        return deduped[:8]

    @staticmethod
    def _extract_domain(url_or_host: str) -> str:
        raw = str(url_or_host or "").strip().lower()
        if not raw:
            return ""
        if raw.startswith(("http://", "https://")):
            host = (urlparse(raw).netloc or "").lower()
        else:
            host = raw.split("/", 1)[0].lower()
        return host.replace("www.", "")

    @staticmethod
    def _is_blocked_discovery_domain(domain: str) -> bool:
        blocked = (
            "indeed.",
            "naukri.",
            "linkedin.",
            "glassdoor.",
            "monster.",
            "shine.",
            "ambitionbox.",
            "facebook.",
            "instagram.",
            "x.com",
            "twitter.",
            "youtube.",
            "wikipedia.",
            "github.",
            "medium.",
            "quora.",
            "reddit.",
            "pinterest.",
            "justdial.",
            "indiamart.",
            "sulekha.",
            "clutch.",
            "g2.",
            "internshala.",
            "timesjobs.",
            "freshersworld.",
            "foundit.",
            "bebee.",
            "tendersontime.",
            "tenderdetail.",
            "tendernews.",
            "tenderwizard.",
            "bidassist.",
            "instantmarkets.",
            "globaltenders.",
            "tendertiger.",
            "rfpmart.",
            "tender247.",
            "tenderdekho.",
            "policycommons.",
            "scribd.",
            "researchgate.",
        )
        return any(token in domain for token in blocked)

    @staticmethod
    def _domain_to_company_name(domain: str) -> str:
        core = (domain or "").replace("www.", "").split(".")[0].strip()
        core = re.sub(r"[^a-z0-9]+", " ", core)
        core = re.sub(r"\s+", " ", core).strip()
        return " ".join(word.capitalize() for word in core.split())[:120] if core else ""

    @staticmethod
    def _is_generic_result_title(title: str) -> bool:
        text = re.sub(r"\s+", " ", str(title or "").strip().lower())
        if not text:
            return True

        noise_tokens = (
            "job",
            "jobs",
            "hiring",
            "hire",
            "career",
            "careers",
            "vacancy",
            "work from home",
            "salary",
            "freshers",
            "openings",
            "latest",
            "in india",
            "2025",
            "2026",
            "how to",
            "top ",
            "best ",
            "request for proposal",
            "rfp",
            "request for quotation",
            "rfq",
            "request for information",
            "rfi",
            "tender",
            "invites bids",
            "bid document",
        )
        if any(token in text for token in noise_tokens):
            return True

        if len(text.split()) >= 6:
            return True

        return False

    @staticmethod
    def _is_noise_discovery_result(title: str, snippet: str) -> bool:
        text = f"{title} {snippet}".lower()
        hard_noise = (
            "jobs in",
            "job details",
            "job description",
            "walk in",
            "resume",
            "interview questions",
            "courses",
            "training",
            "tutorial",
            "freelance gig",
            "upwork",
            "fiverr",
            "eprocurement",
            "corrigendum",
        )
        return any(token in text for token in hard_noise)

    @staticmethod
    def _is_likely_buyer_intent_result(title: str, snippet: str, url: str) -> bool:
        """Keep only pages that indicate a buyer is seeking services/vendors."""
        text = f"{title} {snippet} {url}".lower()
        parsed_url = urlparse(str(url or ""))
        path = (parsed_url.path or "").lower()

        buyer_procurement_signals = (
            "request for proposal",
            "rfp",
            "request for quotation",
            "rfq",
            "request for information",
            "rfi",
            "invites bids",
            "issued by",
            "bid submission",
            "tender notice",
            "expression of interest",
            "eoi",
            "last date",
            "proposal due",
            "scope of work",
        )
        buyer_need_signals = (
            "seeking vendor",
            "looking for vendor",
            "looking for implementation partner",
            "seeking implementation partner",
            "looking for development partner",
            "seeking development partner",
            "need web development",
            "need software development",
        )
        has_positive = any(token in text for token in buyer_procurement_signals) or any(
            token in text for token in buyer_need_signals
        )

        service_provider_tokens = (
            "web development company",
            "software development company",
            "development agency",
            "digital agency",
            "consulting firm",
            "solution provider",
            "outsourcing company",
            "it outsourcing company",
            "hire dedicated developers",
            "offshore development",
            "staff augmentation",
            "freelance service",
            "we provide",
            "seo company",
            "web solutions",
            "digital marketing",
        )
        if any(token in text for token in service_provider_tokens):
            return False

        vendor_marketing_tokens = (
            "our services",
            "we offer",
            "development services",
            "solutions provider",
            "custom technology solutions",
            "top 10",
            "top 5",
            "best ",
            "company in india",
            "companies in india",
            "agency",
            "hire us",
            "why choose us",
            "right place",
            "rfp partner",
            "respond to your request for proposal",
            "if you're seeking",
            "/blog/",
            "/blogs/",
            "/case-study",
            "/portfolio",
            "submit rfp",
            "attach your rfp",
            "fill out the form",
            "contact us",
            "request a quote",
            "we'll get back to you",
            "outsource web development",
            "outsourcing company",
            "offshore outsourcing",
            "outsourcing development",
            "it outsourcing company",
            "web design india",
            "complete guide",
            "ideal destination for",
            "get quote",
            "request quotation",
            "quotation request",
            "request for quotation -",
            "rfq form",
        )
        has_vendor_marketing = any(token in text for token in vendor_marketing_tokens)

        hard_vendor_marketing = (
            "custom technology solutions",
            "rfp partner",
            "respond to your request for proposal",
            "if you're seeking",
            "at the right place",
            "submit rfp",
            "attach your rfp",
            "we'll get back to you with a proposal",
            "request for proposal - submit rfp",
            "rfi rfp rfq",
            "outsource web development",
            "it outsourcing company",
            "offshore outsourcing partner",
            "outsourcing company india",
            "get quote",
            "request for quotation -",
            "quotation request form",
        )
        if any(token in text for token in hard_vendor_marketing):
            return False

        strict_procurement_signals = (
            "invites bids",
            "issued by",
            "bid submission",
            "tender notice",
            "expression of interest",
            "last date",
            "proposal due",
            "deadline",
        )
        has_strict_procurement = any(token in text for token in strict_procurement_signals)
        if any(token in text for token in ("outsource", "outsourcing", "offshore")) and not has_strict_procurement:
            return False

        if "/contact/" in path:
            return False

        if any(part in path for part in ("/services/", "/solutions/", "/portfolio/", "/case-study/", "/blog/", "/blogs/")):
            if not any(token in text for token in buyer_procurement_signals):
                return False

        if has_vendor_marketing:
            return False

        return has_positive

    @staticmethod
    def _is_likely_growth_buyer_result(title: str, snippet: str, url: str) -> bool:
        """Relaxed fallback: growth-demand pages from non-provider companies."""
        text = f"{title} {snippet} {url}".lower()
        parsed_url = urlparse(str(url or ""))
        path = (parsed_url.path or "").lower()

        growth_signals = (
            "hiring",
            "recruiting",
            "careers",
            "open positions",
            "engineering team",
            "product engineering",
            "digital transformation",
            "platform revamp",
            "modernization",
        )
        if not any(token in text for token in growth_signals):
            return False

        service_provider_tokens = (
            "web development company",
            "software development company",
            "development agency",
            "digital agency",
            "consulting firm",
            "solution provider",
            "outsourcing company",
            "it outsourcing company",
            "hire dedicated developers",
            "offshore development",
            "staff augmentation",
            "freelance service",
            "seo company",
            "web solutions",
            "digital marketing",
            "request a quote",
            "get quote",
        )
        if any(token in text for token in service_provider_tokens):
            return False

        job_board_noise = (
            "jobs in",
            "job portal",
            "salary",
            "walk in",
            "job description",
            "resume",
            "freshers",
            "internship",
            "be bee",
        )
        if any(token in text for token in job_board_noise):
            return False

        if any(part in path for part in ("/jobs", "/job", "/vacancy", "/salary")):
            return False

        return True

    @classmethod
    def _extract_company_name_from_result(cls, title: str, domain: str) -> str:
        """Derive company name from result title/domain with generic-title fallback."""
        title_text = re.sub(r"\s+", " ", str(title or "").strip())
        if title_text:
            for sep in ("|", "-", "::", "—"):
                if sep in title_text:
                    title_text = title_text.split(sep, 1)[0].strip()
                    break

        if title_text and len(title_text) >= 2 and not cls._is_generic_result_title(title_text):
            return title_text[:120]

        return cls._domain_to_company_name(domain)

    @staticmethod
    def _infer_buyer_signal_type(title: str, snippet: str) -> str:
        text = f"{title} {snippet}".lower()
        if "rfp" in text or "request for proposal" in text:
            return "rfp_posted"
        if "digital transformation" in text or "modernization" in text:
            return "digital_transformation"
        if "series a" in text or "series b" in text or "funded" in text or "funding" in text:
            return "funding"
        if "expansion" in text or "scaling" in text or "growing" in text or "growth" in text:
            return "expansion"
        if "partner" in text or "vendor" in text or "implementation" in text or "consulting" in text:
            return "seeking_partner"
        return "hiring_technical"

    @staticmethod
    def _resolve_duckduckgo_redirect(raw_link: str) -> str:
        """Resolve DuckDuckGo redirect link to final URL when possible."""
        href = str(raw_link or "").strip()
        if not href:
            return ""
        parsed = urlparse(href)
        if "duckduckgo.com" in parsed.netloc and parsed.path.startswith("/l/"):
            params = parse_qs(parsed.query)
            target = params.get("uddg", [])
            if target:
                return unquote(target[0])
        return href

    async def _discover_buyer_intent_with_serper(self, service: str, location: str) -> List[Dict[str, Any]]:
        """Discover buyer-intent companies from Serper web search snippets."""
        key = str(settings.SERPER_API_KEY or "").strip()
        if not key:
            return []

        queries = [
            f'"{service}" ("RFP" OR "request for proposal" OR "RFQ" OR "invites bids") "{location}"',
            f'"{service}" ("tender notice" OR "bid submission" OR "issued by") "{location}"',
            f'"{service}" ("looking for vendor" OR "seeking development partner" OR "outsourcing partner") "{location}"',
            f'"{service}" ("website redesign project" OR "platform revamp" OR "digital transformation project") "{location}"',
            f'"{service}" ("seeking proposals" OR "vendor selection" OR "request for quotation") "{location}"',
        ]

        results: List[Dict[str, Any]] = []
        headers = {
            "X-API-KEY": key,
            "Content-Type": "application/json",
            "User-Agent": random.choice(USER_AGENTS),
        }

        async with aiohttp.ClientSession(timeout=self.request_timeout) as session:
            for query in queries:
                try:
                    payload = {"q": query, "num": 10}
                    async with session.post("https://google.serper.dev/search", json=payload, headers=headers) as response:
                        if response.status >= 400:
                            continue
                        data = await response.json(content_type=None)
                except Exception as exc:
                    print(f"[JOBBOARD] Serper intent discovery failed for query '{query}': {exc}")
                    continue

                for item in data.get("organic", [])[:10]:
                    raw_link = str(item.get("link", "") or "").strip()
                    if raw_link.lower().endswith(".pdf"):
                        continue
                    link = self._normalize_website(raw_link)
                    if not link:
                        continue

                    domain = self._extract_domain(link)
                    if not domain or self._is_blocked_discovery_domain(domain):
                        continue

                    title = self._clean_text(item.get("title", ""))
                    snippet = self._clean_text(item.get("snippet", ""))
                    if self._is_noise_discovery_result(title, snippet):
                        continue
                    if not self._is_likely_buyer_intent_result(title, snippet, raw_link):
                        continue
                    company_name = self._extract_company_name_from_result(title, domain)
                    if not company_name:
                        continue

                    signal_type = self._infer_buyer_signal_type(title, snippet)
                    results.append(
                        {
                            "company_name": company_name,
                            "company_website": link,
                            "job_url": raw_link,
                            "job_title": title or f"{service} opportunity",
                            "buyer_signal": snippet or title,
                            "location": location,
                            "source": "web",
                            "posted_date": "",
                            "signal_type": signal_type,
                            "service": service,
                            "details": snippet,
                            "discovered_at": datetime.utcnow().isoformat(),
                        }
                    )

        return results

    async def _discover_growth_buyer_intent_with_serper(self, service: str, location: str) -> List[Dict[str, Any]]:
        """Fallback discovery when strict procurement/vendor-intent yields sparse results."""
        key = str(settings.SERPER_API_KEY or "").strip()
        if not key:
            return []

        queries = [
            f'"{service}" ("hiring" OR "recruiting" OR "careers") "{location}" "in-house team"',
            f'"{service}" ("platform revamp" OR "digital transformation" OR "modernization") "{location}" "product company"',
        ]

        results: List[Dict[str, Any]] = []
        headers = {
            "X-API-KEY": key,
            "Content-Type": "application/json",
            "User-Agent": random.choice(USER_AGENTS),
        }

        async with aiohttp.ClientSession(timeout=self.request_timeout) as session:
            for query in queries:
                try:
                    payload = {"q": query, "num": 10}
                    async with session.post("https://google.serper.dev/search", json=payload, headers=headers) as response:
                        if response.status >= 400:
                            continue
                        data = await response.json(content_type=None)
                except Exception as exc:
                    print(f"[JOBBOARD] Serper relaxed discovery failed for query '{query}': {exc}")
                    continue

                for item in data.get("organic", [])[:10]:
                    raw_link = str(item.get("link", "") or "").strip()
                    if raw_link.lower().endswith(".pdf"):
                        continue
                    link = self._normalize_website(raw_link)
                    if not link:
                        continue

                    domain = self._extract_domain(link)
                    if not domain or self._is_blocked_discovery_domain(domain):
                        continue

                    title = self._clean_text(item.get("title", ""))
                    snippet = self._clean_text(item.get("snippet", ""))
                    if self._is_noise_discovery_result(title, snippet):
                        continue
                    if not self._is_likely_growth_buyer_result(title, snippet, raw_link):
                        continue
                    company_name = self._extract_company_name_from_result(title, domain)
                    if not company_name:
                        continue

                    signal_type = self._infer_buyer_signal_type(title, snippet)
                    results.append(
                        {
                            "company_name": company_name,
                            "company_website": link,
                            "job_url": raw_link,
                            "job_title": title or f"{service} growth signal",
                            "buyer_signal": snippet or title,
                            "location": location,
                            "source": "web",
                            "posted_date": "",
                            "signal_type": signal_type,
                            "service": service,
                            "details": snippet,
                            "discovered_at": datetime.utcnow().isoformat(),
                        }
                    )

        return results

    async def _discover_buyer_intent_with_duckduckgo(self, service: str, location: str) -> List[Dict[str, Any]]:
        """Discover buyer-intent companies from DuckDuckGo HTML search without API key."""
        query = f'{service} "RFP" OR "looking for vendor" OR "outsourcing partner" OR "website redesign" {location}'
        url = f"https://duckduckgo.com/html/?q={quote_plus(query)}"

        results: List[Dict[str, Any]] = []
        try:
            async with aiohttp.ClientSession(timeout=self.request_timeout) as session:
                html = await self._fetch_html(session, url)
        except Exception as exc:
            print(f"[JOBBOARD] DuckDuckGo intent discovery failed for '{query}': {exc}")
            return results

        if not html:
            return results

        soup = BeautifulSoup(html, "html.parser")
        cards = soup.select("div.result")
        for card in cards[:12]:
            try:
                link_node = card.select_one("a.result__a") or card.select_one("a")
                raw_link = link_node.get("href", "") if link_node else ""
                resolved_link = self._resolve_duckduckgo_redirect(raw_link)
                if resolved_link.lower().endswith(".pdf"):
                    continue
                link = self._normalize_website(resolved_link)
                if not link:
                    continue

                domain = self._extract_domain(link)
                if not domain or self._is_blocked_discovery_domain(domain):
                    continue

                title = self._clean_text(link_node.get_text(" ", strip=True) if link_node else "")
                snippet_node = card.select_one("a.result__snippet") or card.select_one("div.result__snippet")
                snippet = self._clean_text(snippet_node.get_text(" ", strip=True) if snippet_node else "")
                if self._is_noise_discovery_result(title, snippet):
                    continue
                if not self._is_likely_buyer_intent_result(title, snippet, resolved_link):
                    continue
                company_name = self._extract_company_name_from_result(title, domain)
                if not company_name:
                    continue

                signal_type = self._infer_buyer_signal_type(title, snippet)
                results.append(
                    {
                        "company_name": company_name,
                        "company_website": link,
                        "job_url": resolved_link,
                        "job_title": title or f"{service} opportunity",
                        "buyer_signal": snippet or title,
                        "location": location,
                        "source": "web",
                        "posted_date": "",
                        "signal_type": signal_type,
                        "service": service,
                        "details": snippet,
                        "discovered_at": datetime.utcnow().isoformat(),
                    }
                )
            except Exception:
                continue

        return results

    async def discover_buyer_intent(self, service: str, location: str) -> List[Dict[str, Any]]:
        """Run live buyer-intent discovery from web search providers."""
        serper_results = await self._discover_buyer_intent_with_serper(service, location)
        if serper_results:
            return serper_results
        return await self._discover_buyer_intent_with_duckduckgo(service, location)

    def _parse_indeed_html(self, html: str, keyword: str, location: str) -> List[Dict[str, Any]]:
        if not html:
            return []

        soup = BeautifulSoup(html, "html.parser")
        jobs: List[Dict[str, Any]] = []
        cards = soup.select("div.job_seen_beacon, div.slider_container, td.resultContent")

        for card in cards:
            try:
                job_title = self._clean_text(
                    (
                        card.select_one("h2 a span")
                        or card.select_one("h2.jobTitle span")
                        or card.select_one("a.jcs-JobTitle")
                        or card.select_one("[data-testid='job-title']")
                    ).get_text(" ", strip=True)
                )
            except Exception:
                job_title = ""

            try:
                company_name = self._clean_text(
                    (
                        card.select_one("[data-testid='company-name']")
                        or card.select_one("span.companyName")
                        or card.select_one(".companyName")
                    ).get_text(" ", strip=True)
                )
            except Exception:
                company_name = ""

            try:
                job_location = self._clean_text(
                    (
                        card.select_one("[data-testid='text-location']")
                        or card.select_one("div.companyLocation")
                        or card.select_one(".companyLocation")
                    ).get_text(" ", strip=True)
                )
            except Exception:
                job_location = ""

            try:
                posted_date = self._clean_text(
                    (
                        card.select_one("span.date")
                        or card.select_one("[data-testid='myJobsStateDate']")
                    ).get_text(" ", strip=True)
                )
            except Exception:
                posted_date = ""

            try:
                company_link_node = card.select_one("a[data-testid='company-name']") or card.select_one("span.companyName a")
                company_website = self._normalize_website(company_link_node.get("href", "")) if company_link_node else ""
            except Exception:
                company_website = ""

            if not company_name or not job_title:
                continue

            jobs.append(
                {
                    "company_name": company_name,
                    "company_website": company_website,
                    "job_title": job_title,
                    "location": job_location or location,
                    "source": "indeed",
                    "posted_date": posted_date,
                    "intent_signal": "hiring",
                    "service": keyword,
                    "discovered_at": datetime.utcnow().isoformat(),
                }
            )

        # Fallback parser for pages where cards are hydrated from JSON-LD.
        if jobs:
            return jobs

        scripts = soup.select("script[type='application/ld+json']")
        for script in scripts:
            try:
                payload = json.loads(script.get_text(strip=True) or "{}")
            except Exception:
                continue

            entries = payload if isinstance(payload, list) else [payload]
            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                if str(entry.get("@type", "")).lower() not in {"jobposting", "jobposting"}:
                    continue

                try:
                    job_title = self._clean_text(entry.get("title", ""))
                except Exception:
                    job_title = ""

                try:
                    org = entry.get("hiringOrganization", {}) if isinstance(entry.get("hiringOrganization"), dict) else {}
                    company_name = self._clean_text(org.get("name", ""))
                except Exception:
                    company_name = ""

                try:
                    org = entry.get("hiringOrganization", {}) if isinstance(entry.get("hiringOrganization"), dict) else {}
                    company_website = self._normalize_website(org.get("sameAs", ""))
                except Exception:
                    company_website = ""

                try:
                    location_obj = entry.get("jobLocation", {})
                    if isinstance(location_obj, list):
                        location_obj = location_obj[0] if location_obj else {}
                    address = location_obj.get("address", {}) if isinstance(location_obj, dict) else {}
                    job_location = self._clean_text(
                        " ".join(
                            [
                                str(address.get("addressLocality") or ""),
                                str(address.get("addressRegion") or ""),
                            ]
                        )
                    )
                except Exception:
                    job_location = ""

                try:
                    posted_date = self._clean_text(entry.get("datePosted", ""))
                except Exception:
                    posted_date = ""

                if not company_name or not job_title:
                    continue

                jobs.append(
                    {
                        "company_name": company_name,
                        "company_website": company_website,
                        "job_title": job_title,
                        "location": job_location or location,
                        "source": "indeed",
                        "posted_date": posted_date,
                        "intent_signal": "hiring",
                        "service": keyword,
                        "discovered_at": datetime.utcnow().isoformat(),
                    }
                )

        return jobs

    def _parse_naukri_html(self, html: str, keyword: str, location: str) -> List[Dict[str, Any]]:
        if not html:
            return []

        soup = BeautifulSoup(html, "html.parser")
        jobs: List[Dict[str, Any]] = []
        
        # Try multiple selectors for job cards (layout may vary)
        cards = soup.select("article.jobTuple, div.srp-jobtuple-wrapper, div.cust-job-tuple, article.jobCard, div.jobCard, div.job-listing")
        print(f"[JOBBOARD] Naukri HTML parsing: found {len(cards)} job cards")
        
        if not cards:
            print(f"[JOBBOARD] Naukri: No job cards found. Trying alternative selectors...")
            cards = soup.select("div[class*='job'], li[class*='job'], .jobContainer, .jobItem")
            print(f"[JOBBOARD] Naukri: Found {len(cards)} with alternative selectors")
        
        if not cards:
            print(f"[JOBBOARD] Naukri: Still no cards. Checking page structure...")
            print(f"[JOBBOARD] Naukri: Looking for any divs with job-related class names...")
            all_divs = soup.find_all('div', class_=lambda x: x and ('job' in x.lower() or 'posting' in x.lower()))
            print(f"[JOBBOARD] Naukri: Found {len(all_divs)} divs with job-related classes")
            if all_divs:
                print(f"[JOBBOARD] Naukri: First div class: {all_divs[0].get('class', [])}")

        for card in cards:
            try:
                job_title = self._clean_text(
                    (
                        card.select_one("a.title")
                        or card.select_one("a[title]")
                        or card.select_one("h2")
                        or card.select_one("a")
                    ).get_text(" ", strip=True)
                )
            except Exception:
                job_title = ""

            try:
                company_name = self._clean_text(
                    (
                        card.select_one("a.comp-name")
                        or card.select_one("span.comp-name")
                        or card.select_one(".comp-name")
                        or card.select_one(".company")
                    ).get_text(" ", strip=True)
                )
            except Exception:
                company_name = ""

            try:
                job_location = self._clean_text(
                    (
                        card.select_one("span.locWdth")
                        or card.select_one("span.location")
                        or card.select_one(".loc-wrap")
                        or card.select_one(".location")
                    ).get_text(" ", strip=True)
                )
            except Exception:
                job_location = ""

            try:
                posted_date = self._clean_text(
                    (
                        card.select_one("span.job-post-day")
                        or card.select_one("span.job-post-day-time")
                        or card.select_one("span.job-post-time")
                        or card.select_one("span[class*='post']")
                    ).get_text(" ", strip=True)
                )
            except Exception:
                posted_date = ""

            try:
                company_link_node = card.select_one("a.comp-name") or card.select_one("a[href*='company']")
                company_website = self._normalize_website(company_link_node.get("href", "")) if company_link_node else ""
            except Exception:
                company_website = ""

            if not company_name or not job_title:
                continue

            jobs.append(
                {
                    "company_name": company_name,
                    "company_website": company_website,
                    "job_title": job_title,
                    "location": job_location or location,
                    "source": "naukri",
                    "posted_date": posted_date,
                    "intent_signal": "hiring",
                    "service": keyword,
                    "discovered_at": datetime.utcnow().isoformat(),
                }
            )
        
        print(f"[JOBBOARD] Naukri: Extracted {len(jobs)} jobs from {len(cards)} cards")
        return jobs

    async def _scrape_indeed(self, session: aiohttp.ClientSession, keyword: str, location: str) -> List[Dict[str, Any]]:
        url = f"https://in.indeed.com/jobs?q={quote_plus(keyword)}&l={quote_plus(location)}&fromage=14"
        print(f"[JOBBOARD] Fetching Indeed URL: {url}")
        html = await self._fetch_html(session, url)
        print(f"[JOBBOARD] Indeed HTML length: {len(html)} chars")
        jobs = self._parse_indeed_html(html, keyword, location)
        print(f"[JOBBOARD] Indeed parsed: {len(jobs)} jobs")
        return jobs

    async def _scrape_naukri(self, session: aiohttp.ClientSession, keyword: str, location: str) -> List[Dict[str, Any]]:
        kw_slug = self._slugify(keyword)
        loc_slug = self._slugify(location)
        url = f"https://www.naukri.com/{kw_slug}-jobs-in-{loc_slug}"
        print(f"[JOBBOARD] Fetching Naukri URL: {url}")
        html = await self._fetch_html(session, url)
        print(f"[JOBBOARD] Naukri HTML length: {len(html)} chars")
        
        # Save HTML for debugging (first 3000 chars)
        if html and len(html) > 100:
            try:
                import os
                debug_file = os.path.join(os.getcwd(), 'naukri_sample.html')
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(html[:3000])
                print(f"[JOBBOARD] Naukri HTML sample saved to {debug_file}")
            except Exception as e:
                print(f"[JOBBOARD] Could not save HTML: {e}")
        
        jobs = self._parse_naukri_html(html, keyword, location)
        print(f"[JOBBOARD] Naukri parsed: {len(jobs)} jobs")
        return jobs

    async def scrape_job_postings(self, service: str, location: str) -> List[Dict[str, Any]]:
        """
        Scrape job boards for active hiring intent signals.

        Returns:
            List[dict] with fields:
            company_name, company_website, job_title, location,
            source, posted_date, intent_signal
        """
        if not self._clean_text(service) or not self._clean_text(location):
            print(f"[JOBBOARD] Skipping scrape: empty service or location")
            return []

        keywords = self._buyer_intent_keywords(service)
        print(f"[JOBBOARD] Generated keywords for '{service}': {keywords}")
        if not keywords:
            print(f"[JOBBOARD] No keywords generated for service '{service}'")
            return []

        jobs: List[Dict[str, Any]] = []
        seen = set()

        async with aiohttp.ClientSession() as session:
            for keyword in keywords:
                print(f"[JOBBOARD] Scraping Indeed for keyword '{keyword}' in '{location}'")
                try:
                    indeed_jobs = await self._scrape_indeed(session, keyword, location)
                    print(f"[JOBBOARD] Indeed found {len(indeed_jobs)} jobs for '{keyword}'")
                except Exception as exc:
                    print(f"[JOBBOARD] Indeed scrape FAILED for '{keyword}' in '{location}': {exc}")
                    indeed_jobs = []

                for item in indeed_jobs:
                    key = (
                        self._normalize_company_key(item.get("company_name", "")),
                        self._clean_text(item.get("job_title", "")).lower(),
                        str(item.get("source", "")).lower(),
                    )
                    if key in seen:
                        continue
                    seen.add(key)
                    jobs.append(item)

                print(f"[JOBBOARD] Scraping Naukri for keyword '{keyword}' in '{location}'")
                try:
                    naukri_jobs = await self._scrape_naukri(session, keyword, location)
                    print(f"[JOBBOARD] Naukri found {len(naukri_jobs)} jobs for '{keyword}'")
                except Exception as exc:
                    print(f"[JOBBOARD] Naukri scrape FAILED for '{keyword}' in '{location}': {exc}")
                    naukri_jobs = []

                for item in naukri_jobs:
                    key = (
                        self._normalize_company_key(item.get("company_name", "")),
                        self._clean_text(item.get("job_title", "")).lower(),
                        str(item.get("source", "")).lower(),
                    )
                    if key in seen:
                        continue
                    seen.add(key)
                    jobs.append(item)

        print(f"[JOBBOARD] Total unique jobs found: {len(jobs)}")
        
        # Fill missing company websites via Serper or deterministic fallback.
        resolved_jobs: List[Dict[str, Any]] = []
        for job in jobs:
            try:
                resolved_jobs.append(await self.get_company_from_job(job))
            except Exception as exc:
                print(f"[JOBBOARD] Company resolution failed for {job.get('company_name', 'unknown')}: {exc}")
                resolved_jobs.append(job)

        print(f"[JOBBOARD] Returning {len(resolved_jobs)} resolved jobs")
        return resolved_jobs

    async def get_company_from_job(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve company website for job posting when it is missing."""
        record = dict(job or {})
        existing = self._normalize_website(record.get("company_website", ""))
        if existing:
            record["company_website"] = existing
            return record

        company_name = self._clean_text(record.get("company_name", ""))
        if not company_name:
            record["company_website"] = ""
            return record

        serper_key = str(settings.SERPER_API_KEY or "").strip()
        if serper_key:
            try:
                await asyncio.sleep(random.uniform(1.0, 3.0))
                payload = {"q": f"{company_name} official website"}
                headers = {
                    "X-API-KEY": serper_key,
                    "Content-Type": "application/json",
                    "User-Agent": random.choice(USER_AGENTS),
                }
                async with aiohttp.ClientSession(timeout=self.request_timeout) as session:
                    async with session.post(
                        "https://google.serper.dev/search",
                        json=payload,
                        headers=headers,
                    ) as response:
                        if 200 <= response.status < 300:
                            data = await response.json(content_type=None)
                            for item in data.get("organic", [])[:8]:
                                candidate = self._normalize_website(item.get("link", ""))
                                if not candidate:
                                    continue
                                domain = self._extract_domain(candidate)
                                if any(token in domain for token in ["indeed.", "naukri.", "linkedin.", "glassdoor."]):
                                    continue
                                record["company_website"] = candidate
                                return record
            except Exception as exc:
                print(f"[JOBBOARD] Serper company resolution failed for {company_name}: {exc}")

        # Deterministic fallback for no-key / failed lookup scenarios.
        record["company_website"] = ""
        return record

    async def run_intent_discovery(self, services: List[str], locations: List[str]) -> List[Dict[str, Any]]:
        """Run job-board discovery across service-location combinations and dedupe by company."""
        service_values = [self._clean_text(s) for s in (services or []) if self._clean_text(s)]
        location_values = [self._clean_text(l) for l in (locations or []) if self._clean_text(l)]

        if not service_values:
            service_values = ["software development"]
        if not location_values:
            location_values = ["India"]

        print(f"[JOBBOARD] run_intent_discovery starting")
        print(f"[JOBBOARD]   services: {service_values}")
        print(f"[JOBBOARD]   locations: {location_values}")

        all_jobs: List[Dict[str, Any]] = []

        for service in service_values:
            for location in location_values:
                try:
                    board_jobs = await self.scrape_job_postings(service=service, location=location)
                    print(f"[JOBBOARD] Live job-board results for '{service}' in '{location}': {len(board_jobs)}")
                    all_jobs.extend(board_jobs)
                except Exception as exc:
                    print(f"[JOBBOARD] Job-board discovery failed for '{service}' in '{location}': {exc}")

                try:
                    web_jobs = await self.discover_buyer_intent(service=service, location=location)
                    print(f"[JOBBOARD] Live web buyer-intent results for '{service}' in '{location}': {len(web_jobs)}")
                    all_jobs.extend(web_jobs)
                except Exception as exc:
                    print(f"[JOBBOARD] Web intent discovery failed for '{service}' in '{location}': {exc}")

        print(f"[JOBBOARD] Total jobs from all sources: {len(all_jobs)}")

        deduped: Dict[str, Dict[str, Any]] = {}
        for job in all_jobs:
            company_name = self._clean_text(job.get("company_name", ""))
            if not company_name:
                continue

            website = self._clean_text(job.get("company_website", ""))
            source_url = self._clean_text(job.get("job_url", ""))
            domain = self._extract_domain(website) or self._extract_domain(source_url)

            key = domain or self._normalize_company_key(company_name)
            if not key:
                continue

            current = deduped.get(key)
            if not current:
                deduped[key] = job
                continue

            current_has_site = bool(self._clean_text(current.get("company_website", "")))
            new_has_site = bool(self._clean_text(job.get("company_website", "")))
            if new_has_site and not current_has_site:
                deduped[key] = job
                continue

            current_has_better_signal = str(current.get("signal_type", "")).lower() in {
                "rfp_posted",
                "seeking_partner",
                "digital_transformation",
            }
            new_has_better_signal = str(job.get("signal_type", "")).lower() in {
                "rfp_posted",
                "seeking_partner",
                "digital_transformation",
            }
            if new_has_better_signal and not current_has_better_signal:
                deduped[key] = job
                continue

            current_has_date = bool(self._clean_text(current.get("posted_date", "")))
            new_has_date = bool(self._clean_text(job.get("posted_date", "")))
            if new_has_date and not current_has_date:
                deduped[key] = job

        print(f"[JOBBOARD] Returning {len(deduped)} deduplicated companies")
        return list(deduped.values())


jobboard_service = JobBoardService()
