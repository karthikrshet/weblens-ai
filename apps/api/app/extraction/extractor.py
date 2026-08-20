"""
High-quality Web Content Extractor.
Extracts title, metadata, JSON-LD, structural headings, body text,
and strips trackers/boilerplate/scripts while computing cryptographic content hashes.
"""

import json
import hashlib
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from bs4 import BeautifulSoup
import trafilatura


@dataclass
class ExtractedContent:
    url: str
    title: str
    description: Optional[str]
    clean_text: str
    markdown_content: str
    content_hash: str
    word_count: int
    headings: List[Dict[str, str]] = field(default_factory=list)
    json_ld: List[Dict[str, Any]] = field(default_factory=list)
    open_graph: Dict[str, str] = field(default_factory=dict)
    canonical_url: Optional[str] = None
    language: Optional[str] = "en"
    is_sparse: bool = False


def compute_content_hash(text: str) -> str:
    """Compute SHA-256 hash of normalized text for deduplication."""
    normalized = re.sub(r"\s+", " ", text).strip().lower()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def extract_metadata_and_clean_content(url: str, html: str) -> ExtractedContent:
    """
    Extract structured information and clean text from raw HTML.
    """
    soup = BeautifulSoup(html, "html.parser")

    # 1. Extract Page Title
    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.strip()
    if not title:
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            title = og_title["content"].strip()
    if not title:
        h1 = soup.find("h1")
        if h1:
            title = h1.get_text().strip()
    if not title:
        title = "Untitled Page"

    # 2. Extract Meta Description
    description = None
    desc_meta = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", attrs={"name": "Description"})
    if desc_meta and desc_meta.get("content"):
        description = desc_meta["content"].strip()
    if not description:
        og_desc = soup.find("meta", property="og:description")
        if og_desc and og_desc.get("content"):
            description = og_desc["content"].strip()

    # 3. Extract Canonical URL & Language
    canonical_url = None
    canonical_tag = soup.find("link", rel="canonical")
    if canonical_tag and canonical_tag.get("href"):
        canonical_url = canonical_tag["href"].strip()

    html_tag = soup.find("html")
    language = html_tag.get("lang", "en").split("-")[0] if html_tag and html_tag.get("lang") else "en"

    # 4. Extract OpenGraph & Twitter metadata
    open_graph: Dict[str, str] = {}
    for meta in soup.find_all("meta"):
        prop = meta.get("property") or meta.get("name")
        content = meta.get("content")
        if prop and content and (prop.startswith("og:") or prop.startswith("twitter:")):
            open_graph[prop] = content.strip()

    # 5. Extract JSON-LD structured data
    json_ld_data: List[Dict[str, Any]] = []
    for script in soup.find_all("script", type="application/ld+json"):
        if script.string:
            try:
                data = json.loads(script.string.strip())
                if isinstance(data, list):
                    json_ld_data.extend(data)
                elif isinstance(data, dict):
                    json_ld_data.append(data)
            except Exception:
                continue

    # 6. Extract Headings hierarchy (h1 - h6)
    headings: List[Dict[str, str]] = []
    for h in soup.find_all(["h1", "h2", "h3", "h4"]):
        h_text = h.get_text(separator=" ", strip=True)
        if h_text and len(h_text) < 300:
            headings.append({"level": h.name, "text": h_text})

    # 7. Extract main clean body text via Trafilatura
    clean_text = trafilatura.extract(
        html,
        url=url,
        include_links=True,
        include_images=False,
        include_tables=True,
        no_fallback=False,
    )

    # Fallback to BeautifulSoup clean text if trafilatura extracts nothing
    if not clean_text or len(clean_text.strip()) < 50:
        # Remove noisy elements
        for element in soup(["script", "style", "nav", "footer", "aside", "noscript", "svg", "form"]):
            element.decompose()
        clean_text = soup.get_text(separator="\n", strip=True)

    clean_text = clean_text or ""
    words = len(clean_text.split())
    is_sparse = words < 40  # Less than 40 words suggests JS-rendered or blank page

    # Format Markdown representation
    md_lines = [f"# {title}"]
    if description:
        md_lines.append(f"> {description}\n")
    md_lines.append(clean_text)
    markdown_content = "\n\n".join(md_lines)

    content_hash = compute_content_hash(clean_text)

    return ExtractedContent(
        url=url,
        title=title,
        description=description,
        clean_text=clean_text,
        markdown_content=markdown_content,
        content_hash=content_hash,
        word_count=words,
        headings=headings,
        json_ld=json_ld_data,
        open_graph=open_graph,
        canonical_url=canonical_url,
        language=language,
        is_sparse=is_sparse,
    )
