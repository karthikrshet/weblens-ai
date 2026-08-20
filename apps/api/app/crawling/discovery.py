"""
Link Discovery, Canonicalization, and Relevance Scoring.
Extracts internal links from HTML, restricts to same domain boundaries,
and scores paths based on informational relevance.
"""

import re
from urllib.parse import urlparse, urljoin, urldefrag
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass
from bs4 import BeautifulSoup

IGNORED_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico",
    ".pdf", ".zip", ".tar", ".gz", ".rar", ".7z",
    ".mp3", ".mp4", ".wav", ".avi", ".mov",
    ".css", ".js", ".json", ".xml", ".txt",
    ".exe", ".dmg", ".pkg", ".deb", ".rpm",
    ".woff", ".woff2", ".ttf", ".eot",
}

# Semantic category keywords for scoring relevance
CATEGORY_KEYWORDS = {
    "about": ["about", "company", "who-we-are", "team", "story", "mission", "leadership"],
    "products": ["product", "products", "item", "items", "catalog", "collection", "shop", "store"],
    "services": ["service", "services", "solutions", "offerings", "capabilities"],
    "pricing": ["pricing", "price", "plans", "tier", "subscription", "cost"],
    "documentation": ["doc", "docs", "documentation", "guide", "guides", "api", "developer", "reference"],
    "features": ["feature", "features", "how-it-works", "platform", "technology"],
    "contact": ["contact", "support", "help", "contact-us", "get-in-touch"],
    "careers": ["career", "careers", "jobs", "hiring", "work-with-us"],
    "blog": ["blog", "news", "articles", "press", "insights", "resources"],
    "faq": ["faq", "frequently-asked-questions", "q-and-a"],
    "legal": ["privacy", "terms", "legal", "security", "compliance", "policy"],
}


@dataclass
class DiscoveredLink:
    url: str
    text: str
    category: str
    relevance_score: float
    is_internal: bool


def get_base_domain(url: str) -> str:
    """Extract registered domain or hostname (e.g., example.com from www.example.com)."""
    netloc = urlparse(url).netloc.lower().split(":")[0]
    # Remove 'www.' prefix for same-domain comparisons
    if netloc.startswith("www."):
        netloc = netloc[4:]
    return netloc


def is_same_domain(url1: str, url2: str) -> bool:
    """Check if two URLs belong to the same parent domain."""
    d1 = get_base_domain(url1)
    d2 = get_base_domain(url2)
    return d1 == d2 or d1.endswith("." + d2) or d2.endswith("." + d1)


def categorize_and_score_url(path: str, link_text: str) -> Tuple[str, float]:
    """Assign semantic category and relevance score to a URL."""
    path_lower = path.lower()
    text_lower = link_text.lower()
    combined = f"{path_lower} {text_lower}"

    for category, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in path_lower:
                # Direct path match has highest relevance
                score = 0.95 if category in ["about", "products", "services", "pricing", "features"] else 0.75
                return category, score
            if kw in text_lower:
                score = 0.85 if category in ["about", "products", "services", "pricing", "features"] else 0.65
                return category, score

    # General page
    return "general", 0.50


def discover_internal_links(
    base_url: str,
    html: str,
    max_links: int = 50,
) -> List[DiscoveredLink]:
    """
    Extract, normalize, deduplicate, and score internal links from HTML.
    """
    soup = BeautifulSoup(html, "html.parser")
    seen_urls: Set[str] = set()
    discovered: List[DiscoveredLink] = []

    clean_base, _ = urldefrag(base_url)
    seen_urls.add(clean_base.rstrip("/"))

    for a_tag in soup.find_all("a", href=True):
        raw_href = a_tag["href"].strip()
        link_text = a_tag.get_text(strip=True)

        if not raw_href or raw_href.startswith("#") or raw_href.startswith("javascript:") or raw_href.startswith("mailto:") or raw_href.startswith("tel:"):
            continue

        # Resolve relative link
        full_url = urljoin(base_url, raw_href)
        clean_url, _ = urldefrag(full_url)
        clean_url = clean_url.rstrip("/")

        parsed = urlparse(clean_url)
        if parsed.scheme not in ["http", "https"]:
            continue

        # Check ignored file extension
        path = parsed.path.lower()
        if any(path.endswith(ext) for ext in IGNORED_EXTENSIONS):
            continue

        internal = is_same_domain(base_url, clean_url)
        if not internal:
            continue

        if clean_url in seen_urls:
            continue

        seen_urls.add(clean_url)
        category, score = categorize_and_score_url(parsed.path, link_text)

        discovered.append(
            DiscoveredLink(
                url=clean_url,
                text=link_text[:100] if link_text else "",
                category=category,
                relevance_score=score,
                is_internal=internal,
            )
        )

        if len(discovered) >= max_links:
            break

    # Sort discovered links by relevance score descending
    discovered.sort(key=lambda x: x.relevance_score, reverse=True)
    return discovered
