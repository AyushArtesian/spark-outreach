"""Async lead enrichment service with graceful fallbacks."""

import asyncio
import random
import re
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode, urlparse

import aiohttp
from bs4 import BeautifulSoup  # type: ignore[import-not-found]

from app.config import settings


USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
]


TITLE_PATTERN = r"(CEO|CTO|IT Head|Director|Founder|Co-Founder|Manager|Head of Engineering|VP Engineering)"


class EnrichmentService:
    """Enrich discovered leads with tech stack, contacts, and company signals."""

    def __init__(self) -> None:
        self.timeout = aiohttp.ClientTimeout(total=16)

    @staticmethod
    def _clean_text(value: Any) -> str:
        return re.sub(r"\s+", " ", str(value or "").strip())

    @staticmethod
    def _normalize_url(value: str) -> str:
        text = EnrichmentService._clean_text(value)
        if not text:
            return ""
        if not text.startswith(("http://", "https://")):
            text = f"https://{text}"
        parsed = urlparse(text)
        if not parsed.netloc:
            return ""
        return f"{parsed.scheme}://{parsed.netloc}".rstrip("/")

    @staticmethod
    def _extract_domain(value: str) -> str:
        normalized = EnrichmentService._normalize_url(value)
        if not normalized:
            return ""
        return (urlparse(normalized).netloc or "").replace("www.", "").lower()

    def _headers(self) -> Dict[str, str]:
        return {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        }

    async def _fetch_text(self, session: aiohttp.ClientSession, url: str) -> str:
        await asyncio.sleep(random.uniform(1.0, 3.0))
        for attempt in range(3):
            try:
                async with session.get(url, headers=self._headers(), timeout=self.timeout) as response:
                    if response.status == 429:
                        await asyncio.sleep(1.2 * (attempt + 1))
                        continue
                    if response.status >= 400:
                        return ""
                    return await response.text(errors="ignore")
            except Exception:
                await asyncio.sleep(0.7 * (attempt + 1))
        return ""

    async def _post_json(self, url: str, payload: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
        await asyncio.sleep(random.uniform(1.0, 3.0))
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            async with session.post(url, json=payload, headers=headers) as response:
                if 200 <= response.status < 300:
                    return await response.json(content_type=None)
        return {}

    async def _get_json(self, url: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        await asyncio.sleep(random.uniform(1.0, 3.0))
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            async with session.get(url, headers=headers or self._headers()) as response:
                if 200 <= response.status < 300:
                    return await response.json(content_type=None)
        return {}

    async def _detect_with_wappalyzer(self, website_url: str) -> Dict[str, Any]:
        result = {
            "technologies": [],
            "cms": "",
            "ecommerce_platform": "",
            "uses_microsoft_stack": False,
        }
        api_key = str(settings.WAPPALYZER_API_KEY or "").strip()
        if not api_key:
            return result

        try:
            query = urlencode({"urls": website_url})
            endpoint = f"https://api.wappalyzer.com/v2/lookup/?{query}"
            headers = {
                "x-api-key": api_key,
                "User-Agent": random.choice(USER_AGENTS),
                "Accept": "application/json",
            }
            data = await self._get_json(endpoint, headers=headers)
            items = data if isinstance(data, list) else []
            first = items[0] if items else {}
            detected = first.get("technologies", []) if isinstance(first, dict) else []

            technologies: List[str] = []
            for tech in detected:
                try:
                    name = self._clean_text(tech.get("name", ""))
                except Exception:
                    name = ""
                if name:
                    technologies.append(name)

            result["technologies"] = sorted(set(technologies))
            joined = " ".join(t.lower() for t in result["technologies"])

            if "wordpress" in joined:
                result["cms"] = "WordPress"
            if "shopify" in joined:
                result["ecommerce_platform"] = "Shopify"
            elif "woocommerce" in joined:
                result["ecommerce_platform"] = "WooCommerce"
            elif "magento" in joined:
                result["ecommerce_platform"] = "Magento"

            microsoft_tokens = ["microsoft", "azure", "power apps", "dynamics"]
            result["uses_microsoft_stack"] = any(token in joined for token in microsoft_tokens)
        except Exception as exc:
            print(f"[ENRICHMENT] Wappalyzer lookup failed for {website_url}: {exc}")

        return result

    async def detect_tech_stack(self, website_url: str) -> Dict[str, Any]:
        """Detect technologies from API (if configured) then HTML fallback."""
        result = {
            "technologies": [],
            "cms": "",
            "ecommerce_platform": "",
            "uses_microsoft_stack": False,
            "has_contact_form": False,
        }

        normalized_url = self._normalize_url(website_url)
        if not normalized_url:
            return result

        try:
            api_result = await self._detect_with_wappalyzer(normalized_url)
            result["technologies"] = list(api_result.get("technologies", []))
            result["cms"] = self._clean_text(api_result.get("cms", ""))
            result["ecommerce_platform"] = self._clean_text(api_result.get("ecommerce_platform", ""))
            result["uses_microsoft_stack"] = bool(api_result.get("uses_microsoft_stack", False))
        except Exception as exc:
            print(f"[ENRICHMENT] Wappalyzer stage failed for {normalized_url}: {exc}")

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                html = await self._fetch_text(session, normalized_url)
        except Exception as exc:
            print(f"[ENRICHMENT] HTML fetch failed for {normalized_url}: {exc}")
            html = ""

        if not html:
            return result

        lowered = html.lower()

        # Pattern-by-pattern extraction with independent guards.
        try:
            if "cdn.shopify.com" in lowered:
                if "Shopify" not in result["technologies"]:
                    result["technologies"].append("Shopify")
                if not result["ecommerce_platform"]:
                    result["ecommerce_platform"] = "Shopify"
        except Exception:
            pass

        try:
            if "wp-content" in lowered:
                if "WordPress" not in result["technologies"]:
                    result["technologies"].append("WordPress")
                if not result["cms"]:
                    result["cms"] = "WordPress"
        except Exception:
            pass

        try:
            if "microsoftonline.com" in lowered:
                if "Microsoft Online" not in result["technologies"]:
                    result["technologies"].append("Microsoft Online")
                result["uses_microsoft_stack"] = True
        except Exception:
            pass

        try:
            if "powerapps.com" in lowered:
                if "Power Apps" not in result["technologies"]:
                    result["technologies"].append("Power Apps")
                result["uses_microsoft_stack"] = True
        except Exception:
            pass

        try:
            if "dynamics.com" in lowered:
                if "Dynamics 365" not in result["technologies"]:
                    result["technologies"].append("Dynamics 365")
                result["uses_microsoft_stack"] = True
        except Exception:
            pass

        try:
            if any(token in lowered for token in ["azure", "azureedge.net", "windows.net"]):
                if "Microsoft Azure" not in result["technologies"]:
                    result["technologies"].append("Microsoft Azure")
                result["uses_microsoft_stack"] = True
        except Exception:
            pass

        try:
            if "<form" in lowered and any(token in lowered for token in ["contact", "get in touch", "request a demo", "get a quote"]):
                result["has_contact_form"] = True
        except Exception:
            pass

        result["technologies"] = sorted(set(result["technologies"]))
        return result

    async def _find_with_hunter(self, domain: str) -> Dict[str, Any]:
        response = {
            "name": "",
            "title": "",
            "email": "",
            "linkedin_url": "",
            "confidence": 0.0,
        }

        api_key = str(settings.HUNTER_API_KEY or "").strip()
        if not api_key or not domain:
            return response

        try:
            endpoint = f"https://api.hunter.io/v2/domain-search?domain={domain}&api_key={api_key}"
            data = await self._get_json(endpoint, headers={"User-Agent": random.choice(USER_AGENTS)})
            emails = data.get("data", {}).get("emails", []) if isinstance(data, dict) else []

            best: Dict[str, Any] = {}
            best_score = -1.0
            for item in emails:
                if not isinstance(item, dict):
                    continue

                try:
                    title = self._clean_text(item.get("position", ""))
                except Exception:
                    title = ""

                try:
                    first_name = self._clean_text(item.get("first_name", ""))
                except Exception:
                    first_name = ""

                try:
                    last_name = self._clean_text(item.get("last_name", ""))
                except Exception:
                    last_name = ""

                try:
                    email = self._clean_text(item.get("value", ""))
                except Exception:
                    email = ""

                try:
                    confidence_raw = float(item.get("confidence", 0.0) or 0.0)
                except Exception:
                    confidence_raw = 0.0

                title_boost = 0.25 if re.search(TITLE_PATTERN, title, flags=re.I) else 0.0
                score = min(1.0, (confidence_raw / 100.0) + title_boost)
                if score > best_score and email:
                    best_score = score
                    best = {
                        "name": self._clean_text(f"{first_name} {last_name}"),
                        "title": title,
                        "email": email,
                        "linkedin_url": "",
                        "confidence": round(score, 2),
                    }

            if best:
                return best
        except Exception as exc:
            print(f"[ENRICHMENT] Hunter lookup failed for domain={domain}: {exc}")

        return response

    @staticmethod
    def _extract_visible_text(soup: BeautifulSoup) -> str:
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        return re.sub(r"\s+", " ", soup.get_text(" ", strip=True)).strip()

    async def find_decision_maker(self, company_name: str, company_website: str) -> Dict[str, Any]:
        """Find decision maker via Hunter API (optional) or website page scraping."""
        result = {
            "name": "",
            "title": "",
            "email": "",
            "linkedin_url": "",
            "confidence": 0.0,
            "has_contact_form": False,
        }

        domain = self._extract_domain(company_website)
        try:
            hunter_result = await self._find_with_hunter(domain)
            if any(hunter_result.get(key) for key in ["name", "email", "title"]):
                merged = dict(result)
                merged.update(hunter_result)
                return merged
        except Exception as exc:
            print(f"[ENRICHMENT] Hunter stage failed for {company_name}: {exc}")

        base_url = self._normalize_url(company_website)
        if not base_url:
            return result

        candidate_pages = [
            base_url,
            f"{base_url}/about",
            f"{base_url}/team",
            f"{base_url}/contact",
            f"{base_url}/about-us",
            f"{base_url}/leadership",
        ]

        emails_found: List[str] = []
        found_name = ""
        found_title = ""
        found_linkedin = ""
        has_contact_form = False

        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            for page_url in candidate_pages:
                try:
                    html = await self._fetch_text(session, page_url)
                except Exception:
                    html = ""

                if not html:
                    continue

                try:
                    soup = BeautifulSoup(html, "html.parser")
                except Exception:
                    continue

                try:
                    page_text = self._extract_visible_text(soup)
                except Exception:
                    page_text = ""

                try:
                    page_emails = re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", page_text)
                except Exception:
                    page_emails = []
                for email in page_emails:
                    cleaned = self._clean_text(email).lower()
                    if cleaned and cleaned not in emails_found:
                        emails_found.append(cleaned)

                try:
                    if "<form" in html.lower() and any(token in html.lower() for token in ["contact", "request", "demo", "quote"]):
                        has_contact_form = True
                except Exception:
                    pass

                try:
                    if not found_linkedin:
                        for anchor in soup.select("a[href]"):
                            href = self._clean_text(anchor.get("href", ""))
                            if "linkedin.com/" in href:
                                found_linkedin = href
                                break
                except Exception:
                    pass

                # Extract "Name - Title" patterns first.
                if not found_name or not found_title:
                    try:
                        pattern = re.compile(
                            rf"([A-Z][a-z]+\s+[A-Z][a-z]+)\s*(?:[-|,]|\s+at\s+)\s*{TITLE_PATTERN}",
                            flags=re.I,
                        )
                        match = pattern.search(page_text)
                        if match:
                            found_name = self._clean_text(match.group(1))
                            found_title = self._clean_text(match.group(2))
                    except Exception:
                        pass

                # Fallback: infer from heading plus nearby title text.
                if not found_name or not found_title:
                    try:
                        for heading in soup.select("h1, h2, h3, h4")[:20]:
                            heading_text = self._clean_text(heading.get_text(" ", strip=True))
                            if not re.match(r"^[A-Z][a-z]+\s+[A-Z][a-z]+$", heading_text):
                                continue
                            nearby = self._clean_text(heading.find_parent().get_text(" ", strip=True))
                            title_match = re.search(TITLE_PATTERN, nearby, flags=re.I)
                            if title_match:
                                found_name = heading_text
                                found_title = self._clean_text(title_match.group(1))
                                break
                    except Exception:
                        pass

        if found_name and found_title and emails_found:
            confidence = 0.88
        elif emails_found and (found_name or found_title):
            confidence = 0.72
        elif emails_found:
            confidence = 0.55
        elif has_contact_form:
            confidence = 0.30
        else:
            confidence = 0.0

        result.update(
            {
                "name": found_name,
                "title": found_title,
                "email": emails_found[0] if emails_found else "",
                "linkedin_url": found_linkedin,
                "confidence": round(confidence, 2),
                "has_contact_form": has_contact_form,
            }
        )
        return result

    async def get_company_signals(self, company_name: str, website: str) -> Dict[str, Any]:
        """Fetch recency-weighted growth signals via Serper search."""
        result = {
            "recent_funding": False,
            "expansion_news": False,
            "new_product": False,
            "digital_transformation": False,
            "news_snippets": [],
            "signal_strength": 0,
        }

        company = self._clean_text(company_name)
        if not company:
            return result

        serper_key = str(settings.SERPER_API_KEY or "").strip()
        if not serper_key:
            return result

        query = (
            f'"{company}" funding OR "new product" OR expansion '
            f'OR "digital transformation" after:2025-01-01'
        )

        try:
            data = await self._post_json(
                "https://google.serper.dev/search",
                payload={"q": query},
                headers={
                    "X-API-KEY": serper_key,
                    "Content-Type": "application/json",
                    "User-Agent": random.choice(USER_AGENTS),
                },
            )
            organic = data.get("organic", []) if isinstance(data, dict) else []

            snippets: List[str] = []
            funding = False
            expansion = False
            product = False
            transformation = False

            for item in organic[:10]:
                try:
                    title = self._clean_text(item.get("title", ""))
                except Exception:
                    title = ""
                try:
                    snippet = self._clean_text(item.get("snippet", ""))
                except Exception:
                    snippet = ""
                merged = f"{title} {snippet}".lower()
                if not merged:
                    continue

                if snippet:
                    snippets.append(snippet)

                if any(token in merged for token in ["funding", "raised", "series a", "series b", "investment"]):
                    funding = True
                if any(token in merged for token in ["expansion", "expands", "new office", "hiring surge", "scaling"]):
                    expansion = True
                if any(token in merged for token in ["new product", "launch", "launched", "release"]):
                    product = True
                if "digital transformation" in merged:
                    transformation = True

            signal_strength = int(funding) + int(expansion) + int(product)
            result.update(
                {
                    "recent_funding": funding,
                    "expansion_news": expansion,
                    "new_product": product,
                    "digital_transformation": transformation,
                    "news_snippets": snippets[:6],
                    "signal_strength": max(0, min(3, signal_strength)),
                }
            )
        except Exception as exc:
            print(f"[ENRICHMENT] Signal query failed for {company}: {exc}")

        return result

    async def enrich_lead(self, lead: Dict[str, Any]) -> Dict[str, Any]:
        """Orchestrate enrichment and always return a partial merged lead dict."""
        lead_data = dict(lead or {})

        company_name = self._clean_text(
            lead_data.get("company_name")
            or lead_data.get("company")
            or lead_data.get("name")
        )
        website = self._normalize_url(
            lead_data.get("company_website")
            or lead_data.get("website")
            or lead_data.get("url")
            or lead_data.get("source_url")
        )

        default_tech = {
            "technologies": [],
            "cms": "",
            "ecommerce_platform": "",
            "uses_microsoft_stack": False,
            "has_contact_form": False,
        }
        default_decision = {
            "name": "",
            "title": "",
            "email": "",
            "linkedin_url": "",
            "confidence": 0.0,
            "has_contact_form": False,
        }
        default_signals = {
            "recent_funding": False,
            "expansion_news": False,
            "new_product": False,
            "digital_transformation": False,
            "news_snippets": [],
            "signal_strength": 0,
        }

        tasks = [
            self.detect_tech_stack(website),
            self.find_decision_maker(company_name, website),
            self.get_company_signals(company_name, website),
        ]

        try:
            tech_out, decision_out, signals_out = await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as exc:
            print(f"[ENRICHMENT] Orchestration error for {company_name}: {exc}")
            tech_out, decision_out, signals_out = default_tech, default_decision, default_signals

        tech = tech_out if isinstance(tech_out, dict) else default_tech
        decision = decision_out if isinstance(decision_out, dict) else default_decision
        signals = signals_out if isinstance(signals_out, dict) else default_signals

        lead_data["tech_stack"] = {**default_tech, **tech}
        lead_data["decision_maker"] = {**default_decision, **decision}
        lead_data["company_signals"] = {**default_signals, **signals}
        lead_data["enriched_at"] = datetime.utcnow().isoformat()

        return lead_data


enrichment_service = EnrichmentService()
