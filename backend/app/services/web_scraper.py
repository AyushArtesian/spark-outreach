"""Web scraper service for fetching company website and portfolio content."""

import asyncio
import re
from typing import Dict, Optional
from urllib.parse import urljoin, urlparse, quote_plus, parse_qs, unquote

import aiohttp
from bs4 import BeautifulSoup


MAX_CONTENT_CHARS = 200000  # 200KB total - capture comprehensive company info
MAX_PAGE_CHARS = 15000      # 15KB per page - get full page content
MAX_INTERNAL_PAGES = 25     # Crawl up to 25 pages for complete coverage


LOCATION_ALIASES = {
    "gurgoan": "gurgaon",
    "gurugram": "gurgaon",
    "banglore": "bangalore",
    "bengalure": "bangalore",
    "new delhi": "delhi",
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
) -> Optional[str]:
    """Fetch raw HTML with browser-like headers."""
    normalized = _normalize_url(url)
    if not normalized:
        return None

    try:
        async with session.get(
            normalized,
            timeout=aiohttp.ClientTimeout(total=timeout),
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
                "Referer": "https://www.google.com/",
            },
            allow_redirects=True,
        ) as response:
            if response.status < 200 or response.status >= 300:
                print(f"Failed to fetch {normalized}: Status {response.status}")
                return None
            try:
                return await response.text(errors="ignore")
            except Exception:
                raw = await response.read()
                return raw.decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"Error fetching {normalized}: {e}")
        return None


def _extract_priority_links(base_url: str, homepage_html: str) -> list:
    """Extract all useful internal links from homepage for comprehensive crawling."""
    soup = BeautifulSoup(homepage_html, "html.parser")
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

    for anchor in soup.find_all("a", href=True):
        href = anchor["href"].strip()
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


def _extract_company_name_from_html(soup: BeautifulSoup, title_text: str) -> str:
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
    """Validate and append candidate result while deduping by domain."""
    if not href.startswith(("http://", "https://")):
        return False

    parsed = urlparse(href)
    domain = (parsed.netloc or "").lower().replace("www.", "")
    path = (parsed.path or "").lower()
    title_lower = (title or "").lower()
    snippet_lower = (snippet or "").lower()

    low_value_domain_tokens = {
        "crunchbase",
        "tracxn",
        "g2",
        "clutch",
        "goodfirms",
        "sortlist",
        "designrush",
        "upcity",
        "wikipedia",
        "yelp",
        "justdial",
        "glassdoor",
        "indeed",
        "naukri",
        "monster",
        "forbes",
        "techcrunch",
        "businessinsider",
        "yourstory",
        "inc42",
        "wikipedia",
        "infinityjobs",
        "timesjobs",
        "naukri",
        "indeed",
        "monster",
        "apna",
        "shine",
        "freshersworld",
        "glassdoor",
    }
    low_value_text_tokens = {
        "top 100",
        "top 50",
        "top 10",
        "list of",
        "best companies",
        "best company",
        "to work for",
        "jobs in",
        "job openings",
        "salary",
        "compare",
        "rankings",
        "directory",
        "opening",
        "vacancy",
        "career",
    }

    if not domain:
        return False
    if any(token in domain for token in low_value_domain_tokens):
        return False
    if any(domain == d or domain.endswith(f".{d}") for d in blocked_domains):
        return False
    if any(token in title_lower for token in low_value_text_tokens):
        return False
    if any(token in snippet_lower for token in low_value_text_tokens):
        return False
    if any(token in path for token in ["/list", "/top", "/best", "/jobs", "/rank", "/compare"]):
        return False
    if any(token in path for token in ["/career", "/careers", "/vacancies", "/job", "/hiring"]):
        return False
    if " job" in title_lower or "jobs" in title_lower:
        return False
    if re.search(r"\b(20\d{2}|top\s*\d+)\b", title_lower):
        return False
    if re.match(r"^\d+\s+", title_lower):
        return False
    if domain in seen_domains:
        return False

    company_name = (title or "").split("|")[0].split("-")[0].strip() or domain.split(".")[0].title()
    canonical_url = f"https://{domain}"
    seen_domains.add(domain)
    results.append(
        {
            "name": company_name[:120],
            "url": canonical_url,
            "domain": domain,
            "snippet": (snippet or "")[:300],
        }
    )
    return True


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

            soup = BeautifulSoup(html, "html.parser")

            title = (soup.title.get_text(" ", strip=True) if soup.title else "").strip()
            name = _extract_company_name_from_html(soup, title)
            if name:
                result["company_name"] = name[:120]
            elif title:
                result["company_name"] = title.split("|")[0].split("-")[0].strip()[:120]

            text = soup.get_text(" ", strip=True)
            text = re.sub(r"\s+", " ", text)
            result["summary"] = text[:400]

            # Prefer explicit mailto links first
            emails = []
            for anchor in soup.find_all("a", href=True):
                href = anchor.get("href", "")
                if href.startswith("mailto:"):
                    candidate = href.replace("mailto:", "").split("?")[0].strip()
                    if candidate:
                        emails.append(candidate)

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


async def discover_company_websites(
    query: str,
    location: Optional[str] = None,
    industry: Optional[str] = None,
    service_focus: Optional[list] = None,
    target_locations: Optional[list] = None,
    context_keywords: Optional[list] = None,
    max_results: int = 20,
) -> list:
    """Discover candidate company websites from public search results."""
    query_text = (query or "").strip()
    if not query_text:
        return []

    cleaned_query = _clean_search_query_text(query_text)
    normalized_location = _normalize_location_text(location)
    parts = []
    if industry and str(industry).lower() != "all":
        parts.append(str(industry))
    if normalized_location:
        parts.append(normalized_location)
    if service_focus:
        parts.append(" ".join([str(s) for s in service_focus if s]))
    if target_locations:
        parts.append(" ".join([str(t) for t in target_locations[:3] if t]))
    if cleaned_query:
        parts.append(cleaned_query)
    # Use a concise search phrase that emphasizes company software/service discovery.
    parts.append("software development company b2b")
    search_query = _compact_query(parts, max_len=260)
    fallback_query = _compact_query([
        normalized_location or "",
        industry or "",
        " ".join([str(s) for s in (service_focus or [])[:3]]),
        cleaned_query,
        "software development company b2b",
    ], max_len=180)

    no_location_query = _compact_query([
        industry or "",
        " ".join([str(s) for s in (service_focus or [])[:3]]),
        "software development company b2b",
        "india",
    ], max_len=160)

    ddg_search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(search_query)}"
    bing_search_url = f"https://www.bing.com/search?q={quote_plus(search_query)}"
    bing_fallback_url = f"https://www.bing.com/search?q={quote_plus(fallback_query)}"
    bing_no_location_url = f"https://www.bing.com/search?q={quote_plus(no_location_query)}"
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

    try:
        async with aiohttp.ClientSession() as session:
            # Primary source: DuckDuckGo HTML
            ddg_html = await _fetch_html(ddg_search_url, session, timeout=15)
            if ddg_html:
                soup = BeautifulSoup(ddg_html, "html.parser")
                for anchor in soup.select("a.result__a"):
                    href = _resolve_duckduckgo_url(anchor.get("href", ""))
                    title = anchor.get_text(" ", strip=True)

                    snippet = ""
                    block = anchor.find_parent("div", class_="result")
                    if block:
                        snippet_node = block.select_one("a.result__snippet, div.result__snippet")
                        if snippet_node:
                            snippet = snippet_node.get_text(" ", strip=True)

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

            # Fallback source: Bing HTML (used when DDG is sparse or blocked)
            if len(results) < max_results:
                bing_html = await _fetch_html(bing_search_url, session, timeout=15)
                if bing_html:
                    soup = BeautifulSoup(bing_html, "html.parser")
                    for item in soup.select("li.b_algo"):
                        anchor = item.select_one("h2 a")
                        if not anchor:
                            continue

                        href = (anchor.get("href") or "").strip()
                        title = anchor.get_text(" ", strip=True)
                        snippet_node = item.select_one(".b_caption p")
                        snippet = snippet_node.get_text(" ", strip=True) if snippet_node else ""

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

            # Secondary Bing pass with shorter query if still sparse
            if len(results) < max_results:
                bing_html = await _fetch_html(bing_fallback_url, session, timeout=15)
                if bing_html:
                    soup = BeautifulSoup(bing_html, "html.parser")

                    # First try standard Bing result cards
                    for item in soup.select("li.b_algo, .b_algo"):
                        anchor = item.select_one("h2 a") or item.select_one("a[href]")
                        if not anchor:
                            continue

                        href = (anchor.get("href") or "").strip()
                        title = anchor.get_text(" ", strip=True)
                        snippet_node = item.select_one(".b_caption p, p")
                        snippet = snippet_node.get_text(" ", strip=True) if snippet_node else ""

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

            # Third pass: remove location to recover from sparse city spelling/network indexing issues
            if len(results) < max_results:
                bing_html = await _fetch_html(bing_no_location_url, session, timeout=15)
                if bing_html:
                    soup = BeautifulSoup(bing_html, "html.parser")
                    for item in soup.select("li.b_algo, .b_algo"):
                        anchor = item.select_one("h2 a") or item.select_one("a[href]")
                        if not anchor:
                            continue

                        href = (anchor.get("href") or "").strip()
                        title = anchor.get_text(" ", strip=True)
                        snippet_node = item.select_one(".b_caption p, p")
                        snippet = snippet_node.get_text(" ", strip=True) if snippet_node else ""

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

            print(f"Discovery results: query='{search_query}' total={len(results)}")
    except Exception as e:
        print(f"Error discovering company websites: {e}")
        return []

    return results
