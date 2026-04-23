"""Web scraper service for fetching company website and portfolio content."""

import asyncio
import importlib
import os
import re
import time
from typing import Any, Dict, Optional, List
from urllib.parse import urljoin, urlparse, quote_plus, parse_qs, unquote

import aiohttp
import requests
from app.services.business_signal_analyzer import analyze_business_signals as _analyze_business_signals_impl
from app.services.service_scope import is_query_in_service_scope


def _load_beautifulsoup():
    """Load BeautifulSoup lazily so scraping can degrade gracefully when bs4 is absent."""
    try:
        module = importlib.import_module("bs4")
        return getattr(module, "BeautifulSoup", None)
    except Exception:
        return None


BeautifulSoup = _load_beautifulsoup()


MAX_CONTENT_CHARS = 200000  # 200KB total - capture comprehensive company info
MAX_PAGE_CHARS = 15000      # 15KB per page - get full page content
MAX_INTERNAL_PAGES = 25     # Crawl up to 25 pages for complete coverage


USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
]

REFERERS = [
    "https://www.google.com/",
    "https://www.bing.com/",
    "https://duckduckgo.com/",
]


LOCATION_ALIASES = {
    "gurgoan": "gurgaon",
    "gurugram": "gurgaon",
    "banglore": "bangalore",
    "bengalure": "bangalore",
    "new delhi": "delhi",
}

BUYER_QUERY_TEMPLATES = [
    "{industry} companies {location}",
    "{location} {industry} digital transformation",
    "{location} {industry} company website",
    "top {industry} businesses in {location}",
    "{location} SMB looking for {service_category}",
    "site:linkedin.com/company {location} {industry}",
    "{location} {industry} ERP implementation",
]

SERVICE_CATEGORY_MAP = {
    "dynamics 365": "ERP",
    "web development": "website redesign",
    "mobile app": "app development",
    "software development": "custom software",
}


def _normalize_url(url: str) -> str:
    """Ensure URLs are absolute and normalized."""
    normalized = (url or "").strip()
    if not normalized:
        return ""
    if not normalized.startswith(("http://", "https://")):
        normalized = f"https://{normalized}"
    return normalized


def _normalize_location_text(value: Optional[str]) -> str:
    """Normalize frequent city spelling variants for better search hit-rate."""
    text = (value or "").strip().lower()
    if not text:
        return ""
    normalized = text
    for src, dst in LOCATION_ALIASES.items():
        normalized = normalized.replace(src, dst)
    return normalized


def _clean_search_query_text(raw_query: str) -> str:
    """Reduce verbose user query prompts into search-friendly keyword strings."""
    text = (raw_query or "").strip().lower()
    if not text:
        return ""

    # Remove common instruction phrases and filler terms that harm web search relevance.
    text = re.sub(r"\b(find|search for|looking for|discover|show|find me)\b", "", text)
    text = re.sub(r"\b(companies?|firms?|businesses?)\b", "", text)
    text = re.sub(r"\b(in|located in|based in|near|around)\b", "", text)
    text = re.sub(r"\b(that need|that require|needing|need|requires?)\b", "", text)
    text = re.sub(r"\b(size|sizes|small|medium|large|all sizes|all industries)\b", "", text)
    text = re.sub(r"\b(software services|company software|services b2b|b2b service)\b", "", text)
    text = re.sub(r"[^a-z0-9\s]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _resolve_service_category(service_focus: Optional[list]) -> str:
    """Map a service label to buyer-side language for intent discovery queries."""
    normalized_service = " ".join(
        [str(item).strip().lower() for item in (service_focus or []) if str(item).strip()]
    ).strip()
    if not normalized_service:
        return "digital transformation"

    for source, mapped in SERVICE_CATEGORY_MAP.items():
        if source in normalized_service:
            return mapped

    return str(service_focus[0]).strip() if service_focus else "digital transformation"


def _is_valid_planned_query(query: str, location: Optional[str] = None) -> bool:
    """Validate that planner output is an executable web search query, not meta/instructional text."""
    text = re.sub(r"\s+", " ", str(query or "").strip().lower())
    if not text or len(text.split()) < 4:  # Reduced from 5 to 4 words
        return False

    if text.count('"') % 2 != 0:
        return False

    if "series a\" b\"" in text or "series a b" in text:
        return False

    blocked_fragments = [
        "original queries mention",
        "queries mention things like",
        "things like",
        "return only json",
        "output only json",
        "json schema",
        "query_text",
        "rules:",
        "example good",
        "example bad",
        "rewrite these queries",
        "current queries:",
        "etc",
    ]
    if any(fragment in text for fragment in blocked_fragments):
        return False

    # Overly quoted query strings become too restrictive and often yield zero results.
    if text.count('"') > 6:
        return False

    # Reject obvious seller/vendor targeting patterns.
    seller_patterns = [
        "top web development companies",
        "best app development companies",
        "software development agency",
        "hire dedicated developers",
        "it services company",
        "training institute",
        "course",
        "freelancer platform",
    ]
    if any(fragment in text for fragment in seller_patterns):
        return False

    # Require at least one buyer-intent or company-discovery trigger.
    intent_triggers = [
        "looking for",
        "seeking",
        "vendor",
        "implementation",
        "rfp",
        "procurement",
        "digital transformation",
        "erp",
        "funded",
        "funding",
        "series",
        "startups",
        "companies",
        "cto",
        "it manager",
        "growth",
        "expansion",
        "2026",
    ]
    if not any(token in text for token in intent_triggers):
        return False

    # Strict location check: planned queries must include requested location tokens.
    if location:
        location_hint = _normalize_location_text(location) or str(location).strip().lower()
        location_keywords = [location_hint] + location_hint.split() if location_hint else []
        if location_keywords and not any(kw in text for kw in location_keywords if len(kw) >= 3):
            return False

    return True


def _is_service_scoped_planned_query(query: str, service_focus: Optional[list]) -> bool:
    """Validate that planned query stays aligned with requested service focus."""
    return is_query_in_service_scope(query, service_focus or [])


def _normalize_planned_query_for_search(query: str) -> str:
    """Repair malformed LLM query text so search providers receive executable syntax."""
    text = str(query or "").strip().lower()
    if not text:
        return ""

    text = text.replace("\u201c", '"').replace("\u201d", '"').replace("\u2018", "'").replace("\u2019", "'")
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\bor\b", "OR", text, flags=re.IGNORECASE)

    # Common malformed LLM pattern: '"series a" b"' -> '"series a" OR "series b"'
    text = re.sub(
        r'"series\s*a"\s*b"',
        '"series a" OR "series b"',
        text,
        flags=re.IGNORECASE,
    )

    if text.count('"') % 2 != 0:
        text = text.replace('"', "")

    text = re.sub(r"\bOR\s+OR\b", "OR", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text).strip(" -")
    return text


def generate_high_intent_queries(
    query: str,
    location: Optional[str] = None,
    industry: Optional[str] = None,
    service_focus: Optional[list] = None,
    min_queries: int = 10,
    max_queries: int = 15,
    log_prefix: str = "[QUERY GENERATION: HEURISTIC]",
) -> List[str]:
    """Generate high-intent BUYER-side queries for lead discovery."""
    normalized_location = _normalize_location_text(location) or ""
    if not normalized_location:
        normalized_location = "india"

    normalized_industry = (industry or "").strip().lower()
    priority_industries = [
        "manufacturing",
        "retail",
        "healthcare",
        "finance",
        "logistics",
        "real estate",
        "hospitality",
    ]
    if normalized_industry and normalized_industry != "all":
        industries = [normalized_industry]
    else:
        industries = priority_industries[:3]

    service_category = _resolve_service_category(service_focus)

    templates: List[str] = []
    for vertical in industries[:3]:
        templates.extend(
            [
                template.format(
                    industry=vertical,
                    location=normalized_location,
                    service_category=service_category,
                )
                for template in BUYER_QUERY_TEMPLATES
            ]
        )

    deduped = []
    seen = set()
    for candidate in templates:
        normalized = _compact_query([candidate], max_len=220).strip().lower()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        deduped.append(normalized)
        if len(deduped) >= max_queries:
            break

    # Ensure minimum query count even for sparse inputs.
    while len(deduped) < min_queries:
        fallback = _compact_query([
            industries[0],
            service_category,
            normalized_location,
            f"buyer intent company query {len(deduped) + 1}",
        ], max_len=220).strip().lower()
        if fallback and fallback not in seen:
            deduped.append(fallback)
            seen.add(fallback)
        else:
            break

    # Debug logging
    print(f"{log_prefix} Type: BUYER | Industry: {','.join(industries)} | Service: {service_category} | Location: {normalized_location}")
    for i, q in enumerate(deduped[:5], 1):
        print(f"{log_prefix} Query {i}: {q}")
    
    return deduped[:max_queries]


def _is_likely_noise_line(line: str) -> bool:
    """Filter nav/menu/footer heavy lines that pollute embeddings."""
    lower = line.lower()
    
    # Exact match noise patterns
    noise_tokens = (
        "skip to content",
        "home",
        "contact us",
        "privacy policy",
        "terms of service",
        "terms and conditions",
        "cookie",
        "all rights reserved",
        "copyright",
        "call us",
        "follow us",
        "subscribe",
        "newsletter",
    )
    if any(token == lower or lower.startswith(token) for token in noise_tokens):
        return True
    
    # Filter very short lines (typical nav menu items)
    words = line.split()
    if len(words) <= 1:
        return True
    
    # Filter pure navigation phrases
    if lower in ("services", "solutions", "about", "contact", "blog", "pricing", "careers", "company"):
        return True
    
    return False


def _clean_html(html: str) -> str:
    """Extract meaningful visible text from HTML, filtering nav/menu/footer pollution."""
    if BeautifulSoup is None:
        # Fallback parser when bs4 is not available in the current environment.
        text = re.sub(r"(?is)<(script|style|noscript|svg).*?>.*?</\\1>", " ", html or "")
        text = re.sub(r"(?s)<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        chunks = re.split(r"(?<=[.!?])\s+", text)
        filtered = []
        for chunk in chunks:
            chunk = chunk.strip()
            if chunk and not _is_likely_noise_line(chunk) and len(chunk) > 10:
                filtered.append(chunk)
        return " ".join(filtered)

    soup = BeautifulSoup(html, "html.parser")

    # Remove non-content elements, footers, sidebars, navigation
    for tag in soup(["script", "style", "noscript", "svg", "footer", "nav", "aside", "header"]):
        tag.decompose()
    
    # Remove elements with common nav/menu classes/ids
    nav_selectors = ['[class*="nav"]', '[class*="menu"]', '[class*="sidebar"]', '[id*="nav"]', 
                     '[id*="menu"]', '[role="navigation"]', '[role="complementary"]']
    for selector in nav_selectors:
        for elem in soup.select(selector):
            elem.decompose()

    # Prefer semantic/main content blocks
    candidates = soup.select("main, article, section.content, div[class*='main'], div[class*='content'], section")
    if candidates:
        # Get text from main content areas
        text = "\n".join(node.get_text(" ", strip=True) for node in candidates)
    else:
        # Fallback to full page text
        text = soup.get_text(" ", strip=True)

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()
    
    # Split by sentence boundaries and filter noise
    chunks = re.split(r"(?<=[.!?])\s+", text)
    filtered = []
    for chunk in chunks:
        chunk = chunk.strip()
        if chunk and not _is_likely_noise_line(chunk) and len(chunk) > 10:
            filtered.append(chunk)
    
    return " ".join(filtered)


async def _fetch_html(
    url: str,
    session: aiohttp.ClientSession,
    timeout: int = 12,
    max_retries: int = 3,
) -> Optional[str]:
    """Fetch raw HTML with exponential backoff retry, UA rotation, and SSL fallback.
    
    Args:
        url: URL to fetch
        session: aiohttp session
        timeout: Request timeout in seconds
        max_retries: Maximum retry attempts (exponential backoff: base_delay * 2^attempt)
    
    Returns:
        HTML content or None if all retries exhausted
    """
    normalized = _normalize_url(url)
    if not normalized:
        return None

    timeout_cfg = aiohttp.ClientTimeout(total=timeout)
    base_delay = 0.5  # 0.5s base delay for exponential backoff
    
    for attempt in range(max_retries):
        headers = {
            "User-Agent": USER_AGENTS[attempt % len(USER_AGENTS)],
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Referer": REFERERS[attempt % len(REFERERS)],
        }
        request_kwargs = {
            "timeout": timeout_cfg,
            "headers": headers,
            "allow_redirects": True,
        }
        
        # Use SSL verification on first attempt, disable on retry for problematic sites
        if attempt >= 1:
            request_kwargs["ssl"] = False

        try:
            async with session.get(normalized, **request_kwargs) as response:
                # Handle rate limiting and server errors with exponential backoff
                if response.status == 429:  # Too Many Requests
                    wait_time = base_delay * (2 ** attempt)
                    print(f"Rate limited (429) for {normalized}. Waiting {wait_time:.2f}s before retry {attempt + 1}/{max_retries}")
                    await asyncio.sleep(wait_time)
                    continue
                
                if response.status == 403:  # Forbidden - might be anti-bot
                    if attempt == 0:
                        wait_time = base_delay * (2 ** attempt)
                        print(f"Forbidden (403) for {normalized}. Waiting {wait_time:.2f}s before retry...")
                        await asyncio.sleep(wait_time)
                        continue
                    print(f"Forbidden (403) for {normalized}. Skipping further retries.")
                    return None
                
                if response.status == 503:  # Service Unavailable
                    wait_time = base_delay * (2 ** attempt)
                    print(f"Service unavailable (503). Waiting {wait_time:.2f}s...")
                    await asyncio.sleep(wait_time)
                    continue
                
                if response.status < 200 or response.status >= 400:
                    print(f"Failed to fetch {normalized}: HTTP {response.status} (not retrying)")
                    return None
                
                # Success - read content
                try:
                    return await response.text(errors="ignore")
                except Exception as decode_err:
                    print(f"Decode error for {normalized}: {decode_err}. Trying raw decode...")
                    raw = await response.read()
                    return raw.decode("utf-8", errors="ignore")
        
        except (aiohttp.ClientSSLError, aiohttp.ClientConnectorCertificateError) as ssl_err:
            print(f"SSL error for {normalized}: {ssl_err}")
            if attempt < max_retries - 1:
                wait_time = base_delay * (2 ** attempt)
                await asyncio.sleep(wait_time)
                continue
            else:
                if normalized.startswith("https://"):
                    fallback_http = "http://" + normalized[len("https://"):]
                    try:
                        async with session.get(
                            fallback_http,
                            timeout=timeout_cfg,
                            headers=headers,
                            allow_redirects=True,
                        ) as fallback_response:
                            if 200 <= fallback_response.status < 400:
                                print(f"Recovered via HTTP fallback for {normalized}")
                                return await fallback_response.text(errors="ignore")
                    except Exception:
                        pass
                print(f"SSL error on final attempt for {normalized}")
                return None
        
        except asyncio.TimeoutError:
            print(f"Timeout for {normalized} (attempt {attempt + 1}/{max_retries})")
            if attempt < max_retries - 1:
                wait_time = base_delay * (2 ** attempt)
                await asyncio.sleep(wait_time)
                continue
        
        except (aiohttp.ClientConnectorError, aiohttp.ClientOSError) as conn_err:
            print(f"Connection error for {normalized}: {conn_err}")
            if attempt < max_retries - 1:
                wait_time = base_delay * (2 ** attempt)
                await asyncio.sleep(wait_time)
                continue
        
        except Exception as e:
            print(f"Unexpected error fetching {normalized}: {e}")
            if attempt < max_retries - 1:
                wait_time = base_delay * (2 ** attempt)
                await asyncio.sleep(wait_time)
                continue

    print(f"Failed to fetch {normalized} after {max_retries} attempts")
    return None


def _extract_priority_links(base_url: str, homepage_html: str) -> list:
    """Extract all useful internal links from homepage for comprehensive crawling."""
    if BeautifulSoup is None:
        hrefs = re.findall(r'href=["\']([^"\']+)["\']', homepage_html or "", flags=re.IGNORECASE)
    else:
        soup = BeautifulSoup(homepage_html, "html.parser")
        hrefs = [a.get("href", "") for a in soup.find_all("a", href=True)]

    base_host = urlparse(base_url).netloc
    
    # Expanded keyword list to find comprehensive company info
    wanted = [
        "about", "service", "solution", "industry", "product", "portfolio", 
        "project", "work", "case", "team", "company", "client", "technology",
        "capability", "expertise", "feature", "why", "how", "integration",
        "partner", "blog", "resource", "testimonial", "success", "process",
        "our-team", "team-members", "careers", "hiring", "culture", "values",
        "pricing", "package", "plan", "enterprise", "development", "saas",
        "power-platform", "dynamics", "azure", "microsoft", "staffing",
        "augmentation", "consulting", "migration", "custom", "implementation"
    ]
    
    links = []

    for raw_href in hrefs:
        href = str(raw_href or "").strip()
        if not href or href.startswith("#") or href.startswith("mailto:") or href.startswith("tel:"):
            continue
        
        full = urljoin(base_url, href)
        parsed = urlparse(full)
        if parsed.netloc != base_host:
            continue
        
        path = (parsed.path or "").lower()
        # Check if any keyword matches the path
        if any(token in path for token in wanted):
            links.append(full)

    # Remove duplicates while preserving order
    unique = []
    seen = set()
    for link in links:
        if link not in seen:
            seen.add(link)
            unique.append(link)
        if len(unique) >= MAX_INTERNAL_PAGES:
            break
    
    return unique


async def fetch_url_content(url: str, timeout: int = 10) -> Optional[str]:
    """Fetch clean text content from a URL."""
    normalized = _normalize_url(url)
    if not normalized:
        return None

    async with aiohttp.ClientSession() as session:
        html = await _fetch_html(normalized, session, timeout=timeout)
        if not html:
            return None
        cleaned = _clean_html(html)
        return cleaned[:MAX_PAGE_CHARS] if cleaned else None


async def fetch_company_website_context(company_website: str) -> Optional[str]:
    """Fetch homepage + key internal pages to build richer website context."""
    base_url = _normalize_url(company_website)
    if not base_url:
        return None

    async with aiohttp.ClientSession() as session:
        homepage_html = await _fetch_html(base_url, session)
        if not homepage_html:
            return None

        parts = []
        home_text = _clean_html(homepage_html)
        if home_text:
            parts.append(f"[HOME] {home_text[:MAX_PAGE_CHARS]}")

        internal_links = _extract_priority_links(base_url, homepage_html)
        if internal_links:
            html_list = await asyncio.gather(
                *[_fetch_html(link, session) for link in internal_links],
                return_exceptions=True,
            )
            for link, page_html in zip(internal_links, html_list):
                if isinstance(page_html, Exception) or not page_html:
                    continue
                page_text = _clean_html(page_html)
                if page_text:
                    parts.append(f"[{urlparse(link).path or '/'}] {page_text[:MAX_PAGE_CHARS]}")

    if not parts:
        return None
    combined = "\n".join(parts)
    return combined[:MAX_CONTENT_CHARS]


async def fetch_upwork_profile(upwork_id: str) -> Optional[str]:
    """Fetch Upwork agency content from public URL and preserve fallback signal."""
    identifier = (upwork_id or "").strip()
    if not identifier:
        return None

    if "upwork.com/" in identifier:
        url = _normalize_url(identifier)
    else:
        url = f"https://www.upwork.com/agencies/{identifier.strip('/')}/"

    content = await fetch_url_content(url)
    if content:
        return content

    return (
        f"Upwork profile configured: {url}. "
        "Direct scraping blocked by Upwork anti-bot, but this source should still be treated as portfolio signal."
    )


def _extract_github_identity(github_value: str) -> tuple:
    """Parse GitHub input into owner and optional repo."""
    raw = (github_value or "").strip().rstrip("/")
    if not raw:
        return "", ""

    if "github.com/" in raw:
        path = raw.split("github.com/", 1)[1].strip("/")
    else:
        path = raw

    parts = [p for p in path.split("/") if p]
    if not parts:
        return "", ""
    owner = parts[0]
    repo = parts[1] if len(parts) > 1 else ""
    return owner, repo


async def fetch_github_profile(github_value: str) -> Optional[str]:
    """Fetch GitHub user/org details and optional repository metadata."""
    owner, repo = _extract_github_identity(github_value)
    if not owner:
        return None

    headers = {
        "User-Agent": "spark-outreach-bot",
        "Accept": "application/vnd.github+json",
    }
    lines = []

    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            # Try user first, then org.
            for endpoint in [f"https://api.github.com/users/{owner}", f"https://api.github.com/orgs/{owner}"]:
                async with session.get(endpoint, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        lines.append(f"GitHub Name: {data.get('name') or owner}")
                        lines.append(f"GitHub Bio: {data.get('bio') or 'N/A'}")
                        lines.append(f"Public Repos: {data.get('public_repos', 'N/A')}")
                        lines.append(f"Followers: {data.get('followers', 'N/A')}")
                        break

            if repo:
                repo_endpoint = f"https://api.github.com/repos/{owner}/{repo}"
                async with session.get(repo_endpoint, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        r = await response.json()
                        lines.append(f"Repository: {r.get('full_name')}")
                        lines.append(f"Repo Description: {r.get('description') or 'N/A'}")
                        lines.append(f"Primary Language: {r.get('language') or 'N/A'}")
                        lines.append(f"Stars: {r.get('stargazers_count', 0)}")
    except Exception as e:
        print(f"Error fetching GitHub profile {github_value}: {e}")

    if lines:
        return "\n".join(lines)

    # Last fallback: scrape public HTML profile page.
    return await fetch_url_content(f"https://github.com/{owner}")


async def fetch_linkedin_company(linkedin_url: str) -> Optional[str]:
    """Fetch LinkedIn page with graceful fallback when blocked."""
    normalized = _normalize_url(linkedin_url)
    if not normalized:
        return None

    content = await fetch_url_content(normalized)
    if content:
        return content

    parsed = urlparse(normalized)
    slug = parsed.path.strip("/") or "company"
    return (
        f"LinkedIn profile configured: {normalized}. "
        f"Profile slug: {slug}. Direct scraping may be blocked by LinkedIn anti-bot controls."
    )


async def fetch_all_portfolio_content(
    company_website: Optional[str] = None,
    upwork_id: Optional[str] = None,
    github_url: Optional[str] = None,
    linkedin_url: Optional[str] = None,
    portfolio_urls: Optional[list] = None,
) -> Dict[str, str]:
    """Fetch content from all provided portfolio sources in parallel."""
    tasks = []

    if company_website:
        tasks.append(("company_website", fetch_company_website_context(company_website)))

    if upwork_id:
        tasks.append(("upwork", fetch_upwork_profile(upwork_id)))

    if github_url:
        tasks.append(("github", fetch_github_profile(github_url)))

    if linkedin_url:
        tasks.append(("linkedin", fetch_linkedin_company(linkedin_url)))

    if portfolio_urls:
        for idx, url in enumerate(portfolio_urls):
            tasks.append((f"portfolio_{idx}", fetch_url_content(url)))

    results: Dict[str, str] = {}
    if not tasks:
        return results

    names = [name for name, _ in tasks]
    coroutines = [task for _, task in tasks]
    outputs = await asyncio.gather(*coroutines, return_exceptions=True)

    for name, output in zip(names, outputs):
        if isinstance(output, Exception):
            print(f"Error fetching {name}: {output}")
            continue
        if output:
            results[name] = output

    return results


def combine_portfolio_content(portfolio_content: Dict[str, str]) -> str:
    """Combine all portfolio content into a single string for embeddings."""
    combined = []
    for source, content in portfolio_content.items():
        if content:
            combined.append(f"[{source.upper()}]\n{content}\n")
    return "\n".join(combined)


def _resolve_duckduckgo_url(raw_href: str) -> str:
    """Resolve DuckDuckGo redirect links to their target URL."""
    href = (raw_href or "").strip()
    if not href:
        return ""
    parsed = urlparse(href)
    if "duckduckgo.com" in parsed.netloc and parsed.path.startswith("/l/"):
        params = parse_qs(parsed.query)
        uddg = params.get("uddg", [])
        if uddg:
            return unquote(uddg[0])
    return href


def _extract_company_name_from_html(soup: Any, title_text: str) -> str:
    """Extract a better company name from metadata or prominent headers."""
    title = (title_text or "").strip()
    company_name = ""

    def _clean(value: str) -> str:
        return value.strip().split("|")[0].split("-")[0].strip()

    if title:
        company_name = _clean(title)

    # Prefer explicit site name metadata when available.
    for selector in (
        "meta[property='og:site_name']",
        "meta[property='og:title']",
        "meta[name='twitter:title']",
        "meta[name='twitter:site']",
    ):
        elem = soup.select_one(selector)
        if elem and elem.get("content"):
            candidate = _clean(elem.get("content", ""))
            if candidate and candidate.lower() not in ("home", "home page"):
                company_name = candidate
                break

    # Fallback to main heading if the title is too generic.
    if company_name and re.search(r"\b(web|software|development|company|services|design|agency|it)\b", company_name.lower()):
        heading = soup.find(["h1", "h2"])
        if heading:
            heading_text = _clean(heading.get_text(" ", strip=True))
            if heading_text and heading_text.lower() not in ("home", "welcome", "services", "solutions", "about us"):
                company_name = heading_text

    # Final fallback: if extracted name is still generic, return empty so calling code can use domain.
    if not company_name or len(company_name) < 3 or re.search(r"\b(web|software|development|company|services|agency)\b", company_name.lower()):
        return ""

    return company_name


def _append_candidate_result(
    results: list,
    seen_domains: set,
    href: str,
    title: str,
    snippet: str,
    blocked_domains: set,
) -> bool:
    """Validate and append candidate result while deduping by domain.
    
    STRICT FILTERING:
    - Reject service providers, agencies, outsourcers
    - Only accept: SaaS, Product companies, Startups, Tech companies
    - Multiple signals required for acceptance
    """
    if not href.startswith(("http://", "https://")):
        return False

    parsed = urlparse(href)
    domain = (parsed.netloc or "").lower().replace("www.", "")
    path = (parsed.path or "").lower()
    title_lower = (title or "").lower()
    snippet_lower = (snippet or "").lower()

    # === HARD BLOCKS (Directory/Index sites) ===
    low_value_domain_tokens = {
        "crunchbase", "tracxn", "g2", "clutch", "goodfirms", "sortlist",
        "designrush", "upcity", "wikipedia", "yelp", "justdial",
        "glassdoor", "indeed", "naukri", "monster", "forbes",
        "techcrunch", "businessinsider", "yourstory", "inc42",
        "infinityjobs", "timesjobs", "apna", "shine", "freshersworld",
    }
    
    low_value_text_tokens = {
        "top 100", "top 50", "top 10", "list of", "best companies",
        "best company", "to work for", "salary", "compare",
        "rankings", "directory", "job board", "job listings",
    }
    
    competitor_domain_tokens = {
        "toptal", "infosys", "accenture", "wipro", "tcs",
        "cognizant", "capgemini", "fiverr", "upwork", "freelancer",
        "thoughtworks",
    }

    # === PRODUCT/BUYER INTENT (Accept these) ===
    product_company_tokens = {
        "saas", "platform", "product company", "startup", "venture backed",
        "series a", "series b", "b2b software", "cloud platform",
        "software company", "tech company", "fintech", "edtech",
        "proptech", "deep-tech", "ai platform", "api first",
    }

    # === SERVICE PROVIDER / AGENCY (Strictly reject these) ===
    service_provider_tokens = {
        "it services", "outsourcing", "staff augmentation",
        "hire dedicated developers", "freelance service", "web agency",
        "digital agency", "marketing agency", "design agency",
        "development shop", "consulting firm", "management consulting",
        "business consulting", "it consulting", "software consulting",
        "system integration", "system integrator", "integrator",
        "consulting services", "managed services", "professional services",
        "business process outsourcing", "bpo", "shared services",
        "temporary staffing", "contract staffing", "staffing agency",
        "recruitment agency", "placement agency", "recruitment firm",
    }

    # === BLACKLIST PATH PATTERNS ===
    if not domain:
        return False
    if any(token in domain for token in low_value_domain_tokens):
        return False
    if any(token in domain for token in competitor_domain_tokens):
        return False
    if any(domain == d or domain.endswith(f".{d}") for d in blocked_domains):
        return False
    
    # Reject directory/listing/job-related results
    if any(token in title_lower for token in low_value_text_tokens):
        return False
    if any(token in snippet_lower for token in low_value_text_tokens):
        return False
    if any(token in path for token in ["/list", "/top", "/best", "/jobs", "/rank", "/compare"]):
        return False
    if any(token in path for token in ["/vacancies", "/jobs/"]):
        return False
    if " job" in title_lower or "jobs in" in title_lower:
        return False
    if re.search(r"\b(20\d{2}|top\s*\d+)\b", title_lower):
        return False
    if re.match(r"^\d+\s+", title_lower):
        return False

    merged_text = f"{title_lower} {snippet_lower}".strip()

    # === STRICT SERVICE PROVIDER REJECTION ===
    # Count service provider keywords - if ANY found, it's likely a service provider
    service_provider_count = 0
    for token in service_provider_tokens:
        if token in merged_text:
            service_provider_count += 1
    
    if service_provider_count >= 1:
        # Service provider keywords found - only override if strong product signals
        product_signals = 0
        for token in product_company_tokens:
            if token in merged_text:
                product_signals += 1
        
        # Need multiple product signals to override service provider keywords
        if product_signals == 0:
            return False  # Pure service provider, no product signals
        if product_signals == 1 and "platform" not in merged_text and "product" not in merged_text:
            return False  # Weak product signals, likely still a service provider
        # If multiple strong product signals, allow it (e.g., "consulting + saas platform")

    # === Deduplication ===
    if domain in seen_domains:
        return False

    # === Add to results ===
    buyer_intent_signal = any(token in merged_text for token in product_company_tokens)
    company_name = (title or "").split("|")[0].split("-")[0].strip() or domain.split(".")[0].title()
    canonical_url = f"https://{domain}"
    seen_domains.add(domain)
    results.append(
        {
            "name": company_name[:120],
            "title": (title or "")[:180],
            "url": canonical_url,
            "domain": domain,
            "snippet": (snippet or "")[:300],
            "buyer_intent_signal": buyer_intent_signal,
        }
    )
    return True


def analyze_business_signals(
    snippet: str,
    website_text: str,
    service_focus: Optional[list] = None,
    search_query: Optional[str] = None,
) -> Dict[str, object]:
    """Compatibility wrapper around the dedicated business signal analyzer."""
    return _analyze_business_signals_impl(
        snippet=snippet,
        website_text=website_text,
        service_focus=service_focus,
        search_query=search_query,
    )


async def fetch_company_profile_snapshot(url: str) -> Dict[str, str]:
    """Fetch lightweight company profile details from homepage (name/contact hints)."""
    normalized = _normalize_url(url)
    if not normalized:
        return {}

    parsed = urlparse(normalized)
    base_url = f"{parsed.scheme or 'https'}://{parsed.netloc}"

    result: Dict[str, str] = {
        "website": base_url,
        "company_name": "",
        "email": "",
        "phone": "",
        "summary": "",
    }

    try:
        async with aiohttp.ClientSession() as session:
            html = await _fetch_html(base_url, session, timeout=12)
            if not html:
                return result

            mailto_matches = re.findall(
                r'href=["\']mailto:([^"\'?]+)',
                html,
                flags=re.IGNORECASE,
            )

            if BeautifulSoup is None:
                title_match = re.search(r"(?is)<title[^>]*>(.*?)</title>", html)
                title = re.sub(r"\s+", " ", title_match.group(1)).strip() if title_match else ""
                result["company_name"] = title.split("|")[0].split("-")[0].strip()[:120] if title else ""
                text = re.sub(r"(?is)<(script|style|noscript|svg).*?>.*?</\\1>", " ", html)
                text = re.sub(r"(?s)<[^>]+>", " ", text)
            else:
                soup = BeautifulSoup(html, "html.parser")
                title = (soup.title.get_text(" ", strip=True) if soup.title else "").strip()
                name = _extract_company_name_from_html(soup, title)
                if name:
                    result["company_name"] = name[:120]
                elif title:
                    result["company_name"] = title.split("|")[0].split("-")[0].strip()[:120]

                text = soup.get_text(" ", strip=True)

                if not mailto_matches:
                    mailto_matches = []
                    for anchor in soup.find_all("a", href=True):
                        href = anchor.get("href", "")
                        if href.startswith("mailto:"):
                            candidate = href.replace("mailto:", "").split("?")[0].strip()
                            if candidate:
                                mailto_matches.append(candidate)

            text = re.sub(r"\s+", " ", text)
            result["summary"] = text[:400]

            # Prefer explicit mailto links first
            emails = [str(e).strip() for e in mailto_matches if str(e).strip()]

            if not emails:
                emails = re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)

            valid_emails = []
            for email in emails:
                e = email.lower().strip()
                if any(bad in e for bad in ["noreply", "no-reply", "example.com", "sentry", "wixpress"]):
                    continue
                valid_emails.append(e)

            if valid_emails:
                result["email"] = valid_emails[0]

            phones = re.findall(r"(?:\+?\d[\d\-\s()]{8,}\d)", text)
            if phones:
                result["phone"] = phones[0][:32]
    except Exception as e:
        print(f"Error fetching company profile snapshot from {base_url}: {e}")

    return result


def _compact_query(parts: list, max_len: int = 260) -> str:
    """Compact query text to avoid anti-bot/rate-limit triggers on very long URLs."""
    tokens = []
    seen = set()
    for part in parts:
        for token in str(part).split():
            normalized = token.strip().lower()
            if not normalized:
                continue
            if normalized in seen:
                continue
            seen.add(normalized)
            tokens.append(token.strip())

    query = " ".join(tokens)
    if len(query) <= max_len:
        return query
    return query[:max_len].rsplit(" ", 1)[0]


def _relax_query_for_retry(query: str, location: Optional[str] = None, max_len: int = 180) -> str:
    """Loosen over-constrained SERP query when first attempt returns zero results."""
    raw = re.sub(r"\s+", " ", str(query or "").strip().lower())
    if not raw:
        return ""

    # Remove strict operators and negative filters first.
    relaxed = re.sub(r"\b(?:intitle|inurl|site):[^\s]+", " ", raw)
    relaxed = re.sub(r"(?:^|\s)-(?:jobs|careers|internship|salary)\b", " ", relaxed)
    relaxed = relaxed.replace('"', " ")
    relaxed = relaxed.replace("|", " or ")

    tokens = [t for t in re.split(r"\W+", relaxed) if len(t) >= 3]
    drop_tokens = {
        "best", "top", "list", "companies", "company", "looking", "developer",
        "consultant", "request", "demo", "quote", "services", "service",
        "implementation", "partner", "development", "digital", "transformation",
        "2025", "2026",
    }
    kept = [t for t in tokens if t not in drop_tokens]

    location_tokens = [t for t in re.split(r"\W+", str(location or "").lower()) if len(t) >= 3]
    base = [*kept[:8], *location_tokens[:2], "business", "technology"]
    dedup: List[str] = []
    seen = set()
    for token in base:
        if not token or token in seen:
            continue
        seen.add(token)
        dedup.append(token)

    compact = " ".join(dedup)
    if len(compact) > max_len:
        compact = compact[:max_len].rsplit(" ", 1)[0]
    return compact.strip()


def _search_with_fallback_providers(query: str) -> Optional[List[Dict]]:
    """Try SerpAPI first and fallback to Serper if unavailable/rate-limited."""
    serpapi_results = _search_with_serpapi(query, max_retries=2, retry_delay=1)
    if serpapi_results:
        return serpapi_results

    print(f"Fallback: Trying Serper for query '{query[:40]}...'")
    return _search_with_serper(query, max_retries=2, retry_delay=1)


def _is_valid_domain(domain: str) -> bool:
    """Validate domain format and check for blocked patterns."""
    if not domain:
        return False
    
    # Domain must have TLD
    if "." not in domain or len(domain.split(".")[-1]) < 2:
        return False
    
    # Block known problematic domains
    blocked_patterns = {
        "2captcha", "captcha", "recaptcha",
        "verify-human",
        "ip.address", "localhost", "127.0.0.1",
    }
    for pattern in blocked_patterns:
        if pattern in domain.lower():
            return False
    
    return True


async def _validate_domain_ssl(url: str, timeout: int = 8) -> bool:
    """Check if domain has valid SSL certificate. Return False only for hard SSL failures.
    
    Returns:
        True if domain is valid/accessible
        False if hard SSL error (certificate invalid, not a domain, etc.)
    """
    normalized = _normalize_url(url)
    if not normalized:
        return False
    
    parsed = urlparse(normalized)
    domain = parsed.netloc
    
    try:
        timeout_cfg = aiohttp.ClientTimeout(total=timeout)
        # First attempt: normal SSL
        async with aiohttp.ClientSession() as session:
            try:
                async with session.head(
                    normalized,
                    timeout=timeout_cfg,
                    allow_redirects=True,
                    ssl=True
                ) as response:
                    # Any successful response (even 404/403) means domain is valid
                    return True
            except (aiohttp.ClientSSLError, aiohttp.ClientConnectorCertificateError) as ssl_err:
                print(f"SSL warning for {domain}: {ssl_err}. Will retry with SSL verification disabled.")
                # Retry without SSL verification - if it works, domain exists (just has cert issues)
                try:
                    async with session.head(
                        normalized,
                        timeout=timeout_cfg,
                        allow_redirects=True,
                        ssl=False
                    ) as response:
                        return True
                except Exception as retry_err:
                    print(f"Hard SSL failure for {domain}: {retry_err}")
                    return False  # Domain doesn't exist or completely unreachable
    except Exception as e:
        print(f"Domain validation error for {domain}: {e}")
        return False
    
    return False


def _search_with_serpapi(query: str, max_retries: int = 2, retry_delay: int = 2) -> Optional[List[Dict]]:
    """Search using SerpAPI with exponential backoff retry logic.
    
    Args:
        query: Search query string
        max_retries: Maximum retry attempts for failed requests
        retry_delay: Starting delay in seconds (exponential backoff)
    
    Returns:
        List of search results with url, title, snippet, or None if failed
    """
    # Import here to avoid circular imports
    from app.config import settings
    
    if not settings.SERPAPI_KEY:
        return None
    
    headers = {
        "User-Agent": USER_AGENTS[0],
        "Accept": "application/json",
    }
    
    params = {
        "q": query,
        "api_key": settings.SERPAPI_KEY,
        "num": 20,  # Get 20 results per query for better filtering
        "engine": "google",
    }
    
    for attempt in range(max_retries):
        try:
            print(f"SerpAPI search: query='{query[:60]}...' attempt={attempt + 1}/{max_retries}")
            response = requests.get(
                "https://serpapi.com/search",
                params=params,
                headers=headers,
                timeout=12
            )
            
            if response.status_code == 429:  # Rate limit
                print(f"SerpAPI rate limited. Returning None to trigger Serper fallback...")
                return None
            
            if response.status_code == 403:  # Forbidden
                print(f"SerpAPI returned 403 Forbidden. Check API key and quota.")
                return None
            
            if response.status_code != 200:
                print(f"SerpAPI returned status {response.status_code}")
                return None
            
            data = response.json()
            results = []
            
            # Extract organic results
            organic_results = data.get("organic_results", [])
            for result in organic_results:
                results.append({
                    "url": result.get("link", "").strip(),
                    "title": result.get("title", "").strip(),
                    "snippet": result.get("snippet", "").strip(),
                    "source": "Google",
                })
            
            print(f"SerpAPI returned {len(results)} results for query '{query[:40]}...'")
            return results
        
        except requests.exceptions.Timeout:
            print(f"SerpAPI timeout on attempt {attempt + 1}/{max_retries}")
            if attempt < max_retries - 1:
                wait_time = retry_delay * (2 ** attempt)
                time.sleep(wait_time)
        except requests.exceptions.ConnectionError as e:
            print(f"SerpAPI connection error: {e}")
            if attempt < max_retries - 1:
                wait_time = retry_delay * (2 ** attempt)
                time.sleep(wait_time)
        except Exception as e:
            print(f"SerpAPI error: {e}")
            return None
    
    print(f"SerpAPI search failed after {max_retries} attempts")
    return None


def _search_with_serper(query: str, max_retries: int = 2, retry_delay: int = 2) -> Optional[List[Dict]]:
    """Search using Serper API with exponential backoff retry logic.
    
    Args:
        query: Search query string
        max_retries: Maximum retry attempts for failed requests
        retry_delay: Starting delay in seconds (exponential backoff)
    
    Returns:
        List of search results with url, title, snippet, or None if failed
    """
    # Import here to avoid circular imports
    from app.config import settings
    
    if not settings.SERPER_API_KEY:
        return None
    
    headers = {
        "X-API-KEY": settings.SERPER_API_KEY,
        "Content-Type": "application/json",
        "User-Agent": USER_AGENTS[0],
    }
    
    payload = {
        "q": query,
        "num": 20,  # Request 20 results (Serper API may return up to 10 organic results per request)
        # Note: For more results, pagination with 'page' parameter can be used
    }
    
    for attempt in range(max_retries):
        try:
            print(f"Serper search: query='{query[:60]}...' attempt={attempt + 1}/{max_retries}")
            response = requests.post(
                "https://google.serper.dev/search",
                headers=headers,
                json=payload,
                timeout=12
            )
            
            if response.status_code == 429:  # Rate limit
                wait_time = retry_delay * (2 ** attempt)
                print(f"Serper rate limited. Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
                continue
            
            if response.status_code == 403:  # Forbidden
                print(f"Serper returned 403 Forbidden. Check API key and quota.")
                return None
            
            if response.status_code != 200:
                print(f"Serper returned status {response.status_code}")
                return None
            
            data = response.json()
            results = []
            
            # Extract organic results from Serper (different format than SerpAPI)
            organic_results = data.get("organic", [])
            for result in organic_results:
                results.append({
                    "url": result.get("link", "").strip(),
                    "title": result.get("title", "").strip(),
                    "snippet": result.get("snippet", "").strip(),
                    "source": "Serper",
                })
            
            print(f"Serper returned {len(results)} results for query '{query[:40]}...'")
            return results
        
        except requests.exceptions.Timeout:
            print(f"Serper timeout on attempt {attempt + 1}/{max_retries}")
            if attempt < max_retries - 1:
                wait_time = retry_delay * (2 ** attempt)
                time.sleep(wait_time)
        except requests.exceptions.ConnectionError as e:
            print(f"Serper connection error: {e}")
            if attempt < max_retries - 1:
                wait_time = retry_delay * (2 ** attempt)
                time.sleep(wait_time)
        except Exception as e:
            print(f"Serper error: {e}")
            return None
    
    print(f"Serper search failed after {max_retries} attempts")
    return None


def _discover_companies_with_google_maps(
    location: Optional[str],
    industry: Optional[str],
    service_focus: Optional[list],
    max_results: int = 10,
) -> List[Dict[str, Any]]:
    """Discover local SMB companies via Google Maps Places API when configured."""
    from app.config import settings

    key = str(settings.GOOGLE_MAPS_API_KEY or "").strip()
    if not key:
        return []

    normalized_location = _normalize_location_text(location) or str(location or "").strip().lower()
    if not normalized_location:
        normalized_location = "india"

    requested_industry = str(industry or "").strip().lower()
    preferred_industries = [
        requested_industry if requested_industry and requested_industry != "all" else "manufacturing",
        "retail",
        "healthcare",
        "logistics",
    ]

    service_label = " ".join([str(s).strip() for s in (service_focus or []) if str(s).strip()][:1]).lower()
    if not service_label:
        service_label = "digital transformation"

    search_terms: List[str] = []
    for vertical in preferred_industries:
        search_terms.append(f"{vertical} company {normalized_location}")
    search_terms.append(f"SMB business {normalized_location} {service_label}")

    discovered: List[Dict[str, Any]] = []
    seen_domains: set[str] = set()

    for term in search_terms:
        try:
            response = requests.get(
                "https://maps.googleapis.com/maps/api/place/textsearch/json",
                params={"query": term, "key": key},
                timeout=10,
            )
            if response.status_code != 200:
                continue

            payload = response.json() or {}
            for place in payload.get("results", [])[:8]:
                company_name = str(place.get("name") or "").strip()
                if not company_name:
                    continue

                website = ""
                place_id = str(place.get("place_id") or "").strip()
                if place_id:
                    try:
                        details_response = requests.get(
                            "https://maps.googleapis.com/maps/api/place/details/json",
                            params={"place_id": place_id, "fields": "website", "key": key},
                            timeout=10,
                        )
                        if details_response.status_code == 200:
                            details_payload = details_response.json() or {}
                            website = str((details_payload.get("result") or {}).get("website") or "").strip()
                    except Exception:
                        website = ""

                if not website:
                    continue

                parsed = urlparse(website if website.startswith(("http://", "https://")) else f"https://{website}")
                domain = (parsed.netloc or "").lower().replace("www.", "")
                if not domain or domain in seen_domains:
                    continue

                snippet = str(place.get("formatted_address") or place.get("vicinity") or "").strip()
                if not snippet:
                    snippet = f"Google Maps listed company in {normalized_location}"

                seen_domains.add(domain)
                discovered.append(
                    {
                        "name": company_name[:120],
                        "title": company_name[:180],
                        "url": f"https://{domain}",
                        "domain": domain,
                        "snippet": snippet[:300],
                        "buyer_intent_signal": True,
                        "source": "google_maps",
                    }
                )

                if len(discovered) >= max_results:
                    return discovered
        except Exception as e:
            print(f"Google Maps discovery failed for term '{term}': {e}")

    return discovered


async def discover_company_websites(
    query: str,
    location: Optional[str] = None,
    industry: Optional[str] = None,
    service_focus: Optional[list] = None,
    target_locations: Optional[list] = None,
    context_keywords: Optional[list] = None,
    planned_queries: Optional[list] = None,
    max_results: int = 20,
) -> list:
    """Discover candidate company websites from high-intent public search results using SerpAPI."""
    query_text = (query or "").strip()
    if not query_text:
        return []

    # Merge optional LLM-planned queries with deterministic fallback.
    generated_queries = []
    seen_queries = set()
    rejected_planned_queries = 0
    accepted_planned_queries = 0

    for candidate in (planned_queries or []):
        candidate_text = _normalize_planned_query_for_search(str(candidate or "").strip())
        if not _is_valid_planned_query(candidate_text, location=location):
            rejected_planned_queries += 1
            print(
                "[QUERY GENERATION: LLM] "
                f"Rejected: {candidate_text[:100] if candidate_text else candidate}"
            )
            continue
        if not _is_service_scoped_planned_query(candidate_text, service_focus=service_focus):
            rejected_planned_queries += 1
            print(
                "[QUERY GENERATION: LLM] "
                f"Rejected(service_scope): {candidate_text[:100] if candidate_text else candidate}"
            )
            continue

        normalized = _compact_query([candidate_text], max_len=220).strip().lower()
        normalized = _normalize_location_text(normalized)
        if not normalized or normalized in seen_queries:
            continue
        seen_queries.add(normalized)
        generated_queries.append(normalized)
        accepted_planned_queries += 1
        if len(generated_queries) >= 10:
            break

    if planned_queries:
        print(
            "[QUERY GENERATION: LLM] "
            f"received_planned_queries={len(planned_queries)} "
            f"accepted={accepted_planned_queries} rejected={rejected_planned_queries}"
        )
        for idx, q in enumerate(generated_queries[:5], 1):
            print(f"[QUERY GENERATION: LLM] Query {idx}: {q}")

    # Build deterministic fallback only when LLM planning returned very few usable queries.
    heuristic_queries: List[str] = []
    if len(generated_queries) < 2:
        heuristic_queries = generate_high_intent_queries(
            query=query_text,
            location=location,
            industry=industry,
            service_focus=service_focus,
            min_queries=3,
            max_queries=4,
            log_prefix="[QUERY GENERATION: HEURISTIC]",
        )
        print(
            f"[QUERY GENERATION: MERGE] llm_count={len(generated_queries)} "
            f"heuristic_count={len(heuristic_queries)}"
        )

    for fallback_query in heuristic_queries:
        normalized = str(fallback_query).strip().lower()
        if not normalized or normalized in seen_queries:
            continue
        seen_queries.add(normalized)
        generated_queries.append(normalized)
        if len(generated_queries) >= 10:
            break

    query_source = "LLM" if planned_queries else "HEURISTIC"
    if planned_queries and heuristic_queries:
        query_source = "LLM+HEURISTIC"
    print(
        f"[QUERY GENERATION: FINAL] source={query_source} "
        f"final_queries={len(generated_queries)}"
    )
    for idx, q in enumerate(generated_queries[:10], 1):
        print(f"[QUERY GENERATION: FINAL] Query {idx}: {q}")

    blocked_domains = {
        "duckduckgo.com",
        "bing.com",
        "linkedin.com",
        "facebook.com",
        "instagram.com",
        "x.com",
        "twitter.com",
        "youtube.com",
        "wikipedia.org",
        "reddit.com",
        "github.com",
    }

    results = []
    seen_domains = set()
    request_delay = 1.5  # 1.5 second delay between queries
    zero_result_streak = 0

    maps_candidates = _discover_companies_with_google_maps(
        location=location,
        industry=industry,
        service_focus=service_focus,
        max_results=min(8, max_results),
    )
    if maps_candidates:
        for candidate in maps_candidates:
            domain = str(candidate.get("domain") or "").strip().lower()
            if not domain or domain in seen_domains:
                continue
            seen_domains.add(domain)
            results.append(candidate)
            if len(results) >= max_results:
                break
        print(f"[DISCOVERY SOURCES] google_maps={len(maps_candidates)} accepted={len(results)}")

    try:
        for idx, search_query in enumerate(generated_queries):
            if len(results) >= max_results:
                break

            # Add delay between requests (exponential backoff friendly)
            if idx > 0:
                print(f"Waiting {request_delay}s before next query...")
                time.sleep(request_delay)

            active_query = search_query
            if zero_result_streak >= 2:
                relaxed_for_streak = _relax_query_for_retry(search_query, location=location)
                if relaxed_for_streak and relaxed_for_streak != search_query:
                    print(
                        "[QUERY OPTIMIZER] "
                        f"zero_streak={zero_result_streak}; broadening query to '{relaxed_for_streak[:70]}...'"
                    )
                    active_query = relaxed_for_streak

            serpapi_results = _search_with_fallback_providers(active_query)

            # Real-time adaptation: if a query yields no results, relax and retry once.
            if not serpapi_results:
                relaxed_query = _relax_query_for_retry(active_query, location=location)
                if relaxed_query and relaxed_query != active_query:
                    print(
                        "[QUERY OPTIMIZER] "
                        f"no-results -> retrying relaxed query '{relaxed_query[:70]}...'"
                    )
                    serpapi_results = _search_with_fallback_providers(relaxed_query)
                else:
                    print(f"[QUERY OPTIMIZER] no-results and query could not be relaxed: '{active_query[:70]}...'")

            if serpapi_results:
                zero_result_streak = 0
            else:
                zero_result_streak += 1
            
            if serpapi_results:
                for result in serpapi_results:
                    href = result.get("url", "").strip()
                    title = result.get("title", "").strip()
                    snippet = result.get("snippet", "").strip()
                    
                    # Validate domain before processing
                    parsed = urlparse(href)
                    domain = (parsed.netloc or "").lower().replace("www.", "")
                    
                    if _is_valid_domain(domain):
                        _append_candidate_result(
                            results=results,
                            seen_domains=seen_domains,
                            href=href,
                            title=title,
                            snippet=snippet,
                            blocked_domains=blocked_domains,
                        )
                    
                    if len(results) >= max_results:
                        break

        print(f"Discovery results: queries={len(generated_queries)} total={len(results)}")
    except Exception as e:
        print(f"Error discovering company websites: {e}")
        import traceback
        traceback.print_exc()
        return []

    return results
