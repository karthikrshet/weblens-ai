"""
Website Intelligence Service.
Coordinates fetching, link discovery, selective crawling, structured classification,
chunking, embedding indexing, and persistence into the database.
"""

import time
import logging
from typing import List, Dict, Any, Optional, Tuple, AsyncGenerator
from sqlalchemy.orm import Session

from app.models.entities import Website, WebsitePage, ContentChunk, AnalysisRun, ToolExecution
from app.models.db import SessionLocal
from packages.schemas.website import (
    StructuredWebsiteProfile,
    WebsiteType,
    KeyPage,
    WebsiteResponse,
)
from packages.schemas.agent import StreamEventType, StreamEvent, ToolStatus
from app.crawling.fetcher import fetch_page_secure, FetchError
from app.crawling.discovery import discover_internal_links, DiscoveredLink
from app.crawling.browser_fallback import fetch_page_with_browser
from app.extraction.extractor import extract_metadata_and_clean_content, ExtractedContent
from app.retrieval.chunker import chunk_page_content
from app.providers.base import LLMProvider
from app.providers.factory import get_llm_provider
from app.config.settings import settings

logger = logging.getLogger(__name__)


CLASSIFICATION_SYSTEM_PROMPT = """
You are a Principal AI Agent Architect and Website Intelligence Specialist.
Analyze the provided public website content (title, meta description, structured JSON-LD, headings, and clean page text).
Extract a structured, highly accurate profile of what this website is about.

Rules:
1. Ground your classification strictly in the provided text.
2. Identify the website type (ecommerce, saas, healthcare, education, finance, government, nonprofit, media, news, travel, food, marketplace, developer_documentation, portfolio, community, blog, other).
3. If it is a medical or healthcare website, highlight patient/care focus and summarize claims cautiously without providing medical endorsements.
4. Extract key categories, products/services, and capabilities.
5. Provide a concise, clear summary and confidence score between 0.0 and 1.0.
"""


class WebsiteIntelligenceService:
    def __init__(self, db: Session, provider: Optional[LLMProvider] = None):
        self.db = db
        self.provider = provider or get_llm_provider()

    async def analyze_website(
        self,
        target_url: str,
        force_refresh: bool = False,
        max_crawl_pages: Optional[int] = None,
    ) -> Tuple[Website, StructuredWebsiteProfile, List[ExtractedContent]]:
        """
        End-to-end website analysis: fetch homepage, discover links, crawl important pages,
        extract structured intelligence, chunk, embed, and store.
        """
        max_pages = min(max_crawl_pages or settings.MAX_PAGES_PER_WEBSITE, 20)

        # 1. Fetch homepage
        fetch_res = await fetch_page_secure(target_url)
        html = fetch_res.html

        # Check if browser fallback is needed (empty or sparse)
        extracted_home = extract_metadata_and_clean_content(fetch_res.final_url, html)
        if extracted_home.is_sparse:
            logger.info(f"Homepage for {target_url} was sparse ({extracted_home.word_count} words). Attempting browser fallback...")
            rendered_html = await fetch_page_with_browser(fetch_res.final_url)
            if rendered_html:
                html = rendered_html
                extracted_home = extract_metadata_and_clean_content(fetch_res.final_url, html)

        # 2. Discover links and selectively crawl top relevant pages (e.g. /about, /pricing, /products)
        discovered = discover_internal_links(fetch_res.final_url, html, max_links=max_pages * 2)
        top_links = [l for l in discovered if l.relevance_score >= 0.70][:max_pages - 1]

        all_extracted: List[ExtractedContent] = [extracted_home]

        for link in top_links:
            try:
                sub_res = await fetch_page_secure(link.url)
                if sub_res.is_success and sub_res.html:
                    sub_extracted = extract_metadata_and_clean_content(sub_res.final_url, sub_res.html)
                    all_extracted.append(sub_extracted)
            except Exception as e:
                logger.warning(f"Could not crawl secondary link '{link.url}': {str(e)}")
                continue

        # 3. Classify and extract structured intelligence using LLM
        combined_text_sample = f"URL: {fetch_res.final_url}\nTitle: {extracted_home.title}\nDescription: {extracted_home.description or 'N/A'}\n\nContent:\n{extracted_home.clean_text[:4000]}"
        for page in all_extracted[1:]:
            combined_text_sample += f"\n\n--- Subpage: {page.url} ({page.title}) ---\n{page.clean_text[:1500]}"

        profile = await self.provider.generate_structured(
            prompt=combined_text_sample,
            response_model=StructuredWebsiteProfile,
            system_prompt=CLASSIFICATION_SYSTEM_PROMPT,
        )

        # 4. Persist Website into Database
        canonical = extracted_home.canonical_url or fetch_res.final_url
        from urllib.parse import urlparse
        domain = urlparse(canonical).netloc

        website = self.db.query(Website).filter(Website.canonical_url == canonical).first()
        if not website:
            website = Website(
                url=target_url,
                canonical_url=canonical,
                domain=domain,
            )
            self.db.add(website)
            self.db.flush()

        from datetime import datetime
        website.name = profile.name
        website.website_type = profile.website_type.value
        website.secondary_types = [t.value for t in profile.secondary_types]
        website.industry = profile.industry
        website.purpose = profile.purpose
        website.target_audience = profile.target_audience
        website.summary = profile.summary
        website.confidence = profile.confidence
        website.language = extracted_home.language
        website.categories = profile.categories
        website.products_or_services = profile.products_or_services
        website.key_features = profile.key_features
        website.key_pages = [p.model_dump() if hasattr(p, "model_dump") else p.dict() for p in profile.key_pages]
        website.limitations = profile.limitations
        website.last_crawled_at = datetime.utcnow()

        # Clean existing pages if force_refresh
        if force_refresh:
            self.db.query(WebsitePage).filter(WebsitePage.website_id == website.id).delete()
            self.db.flush()

        # 5. Save pages, chunk content, generate embeddings and persist chunks
        all_chunks_to_embed = []
        chunk_objects = []

        for page in all_extracted:
            # Check if page already exists
            existing_page = self.db.query(WebsitePage).filter(
                WebsitePage.website_id == website.id,
                WebsitePage.url == page.url,
            ).first()

            if not existing_page:
                db_page = WebsitePage(
                    website_id=website.id,
                    url=page.url,
                    title=page.title,
                    description=page.description,
                    content=page.markdown_content,
                    content_hash=page.content_hash,
                    depth=0 if page.url == fetch_res.final_url else 1,
                    status="completed",
                )
                self.db.add(db_page)
                self.db.flush()
            else:
                db_page = existing_page

            # Chunk content
            raw_chunks = chunk_page_content(page.title, page.markdown_content)
            for rc in raw_chunks:
                all_chunks_to_embed.append(rc.content)
                db_chunk = ContentChunk(
                    website_id=website.id,
                    page_id=db_page.id,
                    url=page.url,
                    title=page.title,
                    heading=rc.heading,
                    section=rc.section,
                    content=rc.content,
                    token_count=rc.token_count,
                    content_hash=rc.content_hash,
                )
                chunk_objects.append(db_chunk)

        # 6. Generate embeddings in batch and attach
        if all_chunks_to_embed:
            embeddings = await self.provider.embed(all_chunks_to_embed)
            for i, chunk in enumerate(chunk_objects):
                chunk.embedding = embeddings[i]
                self.db.add(chunk)

        self.db.commit()
        self.db.refresh(website)

        return website, profile, all_extracted
