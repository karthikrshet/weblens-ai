"""
Deterministic Tool Definitions and Execution Registry for WebLens AI Agent.
Enforces strict input validation, domain boundaries, SSRF guards, and structured outputs.
"""

import time
import hashlib
import logging
from typing import Dict, Any, List, Optional, Callable, Awaitable
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.models.entities import Website, WebsitePage, ContentChunk, Source
from app.crawling.fetcher import fetch_page_secure, FetchError
from app.crawling.discovery import discover_internal_links, is_same_domain
from app.extraction.extractor import extract_metadata_and_clean_content
from app.retrieval.chunker import chunk_page_content
from app.retrieval.hybrid import HybridSearchEngine
from app.security.ssrf import validate_url_security
from app.providers.factory import get_llm_provider
from packages.schemas.agent import ToolStatus

logger = logging.getLogger(__name__)


class ToolResult(BaseModel):
    tool_name: str
    safe_input_summary: str
    result_summary: str
    data: Any
    status: ToolStatus
    duration_ms: float


class ToolRegistry:
    def __init__(self, db: Session, website: Website):
        self.db = db
        self.website = website
        self.hybrid_engine = HybridSearchEngine()

    async def validate_url_tool(self, url: str) -> ToolResult:
        t0 = time.time()
        try:
            canonical, resolved_ip = validate_url_security(url, enforce_dns=False)
            dt = round((time.time() - t0) * 1000, 2)
            return ToolResult(
                tool_name="validate_url",
                safe_input_summary=f"url='{url}'",
                result_summary=f"URL validated safely (canonical='{canonical}')",
                data={"canonical_url": canonical, "resolved_ip": resolved_ip},
                status=ToolStatus.SUCCESS,
                duration_ms=dt,
            )
        except Exception as e:
            dt = round((time.time() - t0) * 1000, 2)
            return ToolResult(
                tool_name="validate_url",
                safe_input_summary=f"url='{url}'",
                result_summary=f"Validation failed: {str(e)}",
                data=None,
                status=ToolStatus.FAILED,
                duration_ms=dt,
            )

    async def get_website_profile_tool(self) -> ToolResult:
        t0 = time.time()
        profile_data = {
            "name": self.website.name,
            "url": self.website.url,
            "type": self.website.website_type,
            "industry": self.website.industry,
            "purpose": self.website.purpose,
            "audience": self.website.target_audience,
            "summary": self.website.summary,
            "confidence": self.website.confidence,
            "categories": self.website.categories or [],
            "products_or_services": self.website.products_or_services or [],
            "key_features": self.website.key_features or [],
            "key_pages": self.website.key_pages or [],
            "limitations": self.website.limitations,
        }
        dt = round((time.time() - t0) * 1000, 2)
        return ToolResult(
            tool_name="get_website_profile",
            safe_input_summary=f"website_id='{self.website.id}'",
            result_summary=f"Retrieved profile for '{self.website.name}' ({self.website.website_type})",
            data=profile_data,
            status=ToolStatus.SUCCESS,
            duration_ms=dt,
        )

    async def search_website_tool(self, query: str, top_k: int = 4) -> ToolResult:
        t0 = time.time()
        # Query indexed chunks from database
        db_chunks = self.db.query(ContentChunk).filter(ContentChunk.website_id == self.website.id).all()
        chunk_dicts = [
            {
                "id": c.id,
                "page_id": c.page_id,
                "url": c.url,
                "title": c.title,
                "heading": c.heading,
                "section": c.section,
                "content": c.content,
                "embedding": c.embedding,
            }
            for c in db_chunks
        ]

        results = await self.hybrid_engine.search(query, chunk_dicts, top_k=top_k)
        dt = round((time.time() - t0) * 1000, 2)
        
        sources_found = [
            {
                "chunk_id": r.chunk_id,
                "url": r.url,
                "title": r.title,
                "heading": r.heading,
                "relevance_score": r.hybrid_score,
                "snippet": r.snippet,
                "content": r.content,
            }
            for r in results
        ]

        return ToolResult(
            tool_name="search_website",
            safe_input_summary=f"query='{query}', top_k={top_k}",
            result_summary=f"Found {len(sources_found)} relevant content passages for '{query}'",
            data=sources_found,
            status=ToolStatus.SUCCESS,
            duration_ms=dt,
        )

    async def discover_links_tool(self) -> ToolResult:
        t0 = time.time()
        pages = self.db.query(WebsitePage).filter(WebsitePage.website_id == self.website.id).all()
        page_urls = [{"url": p.url, "title": p.title, "depth": p.depth} for p in pages]
        dt = round((time.time() - t0) * 1000, 2)
        return ToolResult(
            tool_name="discover_links",
            safe_input_summary=f"website_id='{self.website.id}'",
            result_summary=f"Discovered {len(page_urls)} indexed website pages",
            data=page_urls,
            status=ToolStatus.SUCCESS,
            duration_ms=dt,
        )

    async def crawl_page_tool(self, target_url: str) -> ToolResult:
        t0 = time.time()
        # Domain Boundary Authorization
        if not is_same_domain(self.website.url, target_url):
            dt = round((time.time() - t0) * 1000, 2)
            return ToolResult(
                tool_name="crawl_page",
                safe_input_summary=f"url='{target_url}'",
                result_summary="Cross-domain crawl blocked by security policy.",
                data=None,
                status=ToolStatus.BLOCKED,
                duration_ms=dt,
            )

        try:
            fetch_res = await fetch_page_secure(target_url)
            extracted = extract_metadata_and_clean_content(fetch_res.final_url, fetch_res.html)

            # Store page
            db_page = WebsitePage(
                website_id=self.website.id,
                url=extracted.url,
                title=extracted.title,
                description=extracted.description,
                content=extracted.markdown_content,
                content_hash=extracted.content_hash,
                depth=1,
                status="completed",
            )
            self.db.add(db_page)
            self.db.flush()

            # Chunk and embed
            chunks = chunk_page_content(extracted.title, extracted.markdown_content)
            if chunks:
                provider = get_llm_provider()
                texts = [c.content for c in chunks]
                embeddings = await provider.embed(texts)
                for i, c in enumerate(chunks):
                    db_chunk = ContentChunk(
                        website_id=self.website.id,
                        page_id=db_page.id,
                        url=extracted.url,
                        title=extracted.title,
                        heading=c.heading,
                        section=c.section,
                        content=c.content,
                        token_count=c.token_count,
                        embedding=embeddings[i],
                        content_hash=c.content_hash,
                    )
                    self.db.add(db_chunk)

            self.db.commit()
            dt = round((time.time() - t0) * 1000, 2)
            return ToolResult(
                tool_name="crawl_page",
                safe_input_summary=f"url='{target_url}'",
                result_summary=f"Successfully fetched and indexed '{extracted.title}' ({len(chunks)} chunks)",
                data={"url": extracted.url, "title": extracted.title, "chunk_count": len(chunks)},
                status=ToolStatus.SUCCESS,
                duration_ms=dt,
            )

        except Exception as e:
            dt = round((time.time() - t0) * 1000, 2)
            return ToolResult(
                tool_name="crawl_page",
                safe_input_summary=f"url='{target_url}'",
                result_summary=f"Crawl failed: {str(e)}",
                data=None,
                status=ToolStatus.FAILED,
                duration_ms=dt,
            )
