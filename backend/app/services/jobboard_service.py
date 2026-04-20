"""Async job board intent discovery service."""

import asyncio
import json
import random
import re
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus, urljoin, urlparse

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

        # Focus on finding buyers, not job seekers
        return [
            f"{normalized_service} implementation partner",
            f"looking for {normalized_service}",
            f"{normalized_service} vendor",
            f"{normalized_service} consulting",
            f"hire {normalized_service} firm",
        ]

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

        keywords = self._keywords_for_service(service)
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
        
        # Generate mock buyer company data for testing/development
        print(f"[JOBBOARD] ⚠️  NOTE: Using mock buyer company data for testing")
        print(f"[JOBBOARD] ⚠️  Real scraping will search for buyer intent signals (RFP, partnerships, etc)")
        
        mock_buyers = self._get_mock_buyer_companies(service_values, location_values)
        print(f"[JOBBOARD] Generated {len(mock_buyers)} mock buyer company signals")
        all_jobs.extend(mock_buyers)
        
        # TODO: Add real buyer intent discovery when Puppeteer/API endpoints available
        # For now, returning mock data immediately without trying job board scraping
        # (Indeed = 0 bytes blocked, Naukri = requires JavaScript rendering)
        
        print(f"[JOBBOARD] Total jobs from all sources: {len(all_jobs)}")

        deduped: Dict[str, Dict[str, Any]] = {}
        for job in all_jobs:
            company_name = self._clean_text(job.get("company_name", ""))
            if not company_name:
                continue
            key = self._normalize_company_key(company_name)
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

            current_has_date = bool(self._clean_text(current.get("posted_date", "")))
            new_has_date = bool(self._clean_text(job.get("posted_date", "")))
            if new_has_date and not current_has_date:
                deduped[key] = job

        print(f"[JOBBOARD] Returning {len(deduped)} deduplicated companies")
        return list(deduped.values())

    def _get_mock_buyer_companies(self, services: List[str], locations: List[str]) -> List[Dict[str, Any]]:
        """
        Generate mock buyer intent data for testing the discovery pipeline.
        Shows companies SEEKING our services (not hiring employees).
        Remove this when real scraper is implemented.
        """
        mock_data = [
            {
                "company_name": "Acme Financial Corp",
                "company_website": "https://acmefinance.example.com",
                "job_title": "Digital Transformation Project - RFP Open",
                "buyer_signal": "Posted RFP for legacy modernization",
                "location": "Bangalore, India",
                "source": "web",
                "posted_date": "2 days ago",
                "signal_type": "rfp_posted",
                "service": services[0] if services else "Development",
                "details": "Seeking development partner for legacy system modernization",
                "discovered_at": datetime.utcnow().isoformat(),
            },
            {
                "company_name": "EnterpriseFlow Systems",
                "company_website": "https://enterpriseflow.example.com",
                "job_title": "Partnership Opportunity - Implementation Support",
                "buyer_signal": "Looking for implementation partner",
                "location": "Pune, India",
                "source": "web",
                "posted_date": "1 day ago",
                "signal_type": "seeking_partner",
                "service": services[0] if services else "Development",
                "details": "Recently funded Series A, expanding engineering capabilities",
                "discovered_at": datetime.utcnow().isoformat(),
            },
            {
                "company_name": "CloudScale Ventures",
                "company_website": "https://cloudscale.example.com",
                "job_title": "Expansion Project - Development Services Request",
                "buyer_signal": "Posted expansion project needing development services",
                "location": "Hyderabad, India",
                "source": "web",
                "posted_date": "3 days ago",
                "signal_type": "expansion",
                "service": services[1] if len(services) > 1 else services[0],
                "details": "Growing tech startup seeking external development partner",
                "discovered_at": datetime.utcnow().isoformat(),
            },
            {
                "company_name": "RetailPro Analytics",
                "company_website": "https://retailpro.example.com",
                "job_title": "eCommerce Development - Consultant Needed",
                "buyer_signal": "Seeking eCommerce development consultant",
                "location": "Mumbai, India",
                "source": "web",
                "posted_date": "4 days ago",
                "signal_type": "seeking_partner",
                "service": services[1] if len(services) > 1 else services[0],
                "details": "MNC looking to build custom ecommerce platform",
                "discovered_at": datetime.utcnow().isoformat(),
            },
            {
                "company_name": "DataAI Corporation",
                "company_website": "https://dataai.example.com",
                "job_title": "AI/ML Development Initiative - External Team Wanted",
                "buyer_signal": "Series B funded, expanding AI capabilities",
                "location": "Bangalore, India",
                "source": "web",
                "posted_date": "1 day ago",
                "signal_type": "funding",
                "service": "AI/ML Development",
                "details": "Series B funded, building AI solutions - need specialized developers",
                "discovered_at": datetime.utcnow().isoformat(),
            },
        ]
        return mock_data


jobboard_service = JobBoardService()
