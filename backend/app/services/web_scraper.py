"""Web scraper service for fetching company website and portfolio content."""

import asyncio
import re
from typing import Dict, Optional
from urllib.parse import urljoin, urlparse

import aiohttp
from bs4 import BeautifulSoup


MAX_CONTENT_CHARS = 200000  # 200KB total - capture comprehensive company info
MAX_PAGE_CHARS = 15000      # 15KB per page - get full page content
MAX_INTERNAL_PAGES = 25     # Crawl up to 25 pages for complete coverage


def _normalize_url(url: str) -> str:
    """Ensure URLs are absolute and normalized."""
    normalized = (url or "").strip()
    if not normalized:
        return ""
    if not normalized.startswith(("http://", "https://")):
        normalized = f"https://{normalized}"
    return normalized


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
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
            },
            allow_redirects=True,
        ) as response:
            if response.status != 200:
                print(f"Failed to fetch {normalized}: Status {response.status}")
                return None
            return await response.text()
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
