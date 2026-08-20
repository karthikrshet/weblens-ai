"""
Heading-Aware Semantic Text Chunker.
Splits web pages along structural boundaries (headings, sections) to preserve context and citation relevance.
"""

import re
import hashlib
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class TextChunk:
    content: str
    heading: Optional[str]
    section: Optional[str]
    token_count: int
    content_hash: str


def approximate_token_count(text: str) -> int:
    """Approximate token count (1 token ~= 4 characters / 0.75 words)."""
    words = len(text.split())
    return max(1, int(words * 1.3))


def chunk_page_content(
    title: str,
    text: str,
    max_chunk_words: int = 250,
    overlap_words: int = 40,
) -> List[TextChunk]:
    """
    Split markdown/structural text into heading-aware semantic chunks.
    """
    if not text or not text.strip():
        return []

    lines = text.split("\n")
    sections: List[Dict[str, Any]] = []
    current_heading = title
    current_lines: List[str] = []

    # 1. Parse by markdown headings (# Header)
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#"):
            if current_lines:
                section_text = "\n".join(current_lines).strip()
                if section_text:
                    sections.append({
                        "heading": current_heading,
                        "text": section_text,
                    })
                current_lines = []
            current_heading = stripped.lstrip("#").strip()
        else:
            if stripped:
                current_lines.append(stripped)

    # Append trailing section
    if current_lines:
        section_text = "\n".join(current_lines).strip()
        if section_text:
            sections.append({
                "heading": current_heading,
                "text": section_text,
            })

    # If no heading structure was found, treat entire text as single section
    if not sections:
        sections = [{"heading": title, "text": text.strip()}]

    chunks: List[TextChunk] = []

    # 2. Split large sections into sub-chunks with overlap
    for sec in sections:
        words = sec["text"].split()
        if len(words) <= max_chunk_words:
            content = f"[{title} > {sec['heading']}]\n{sec['text']}"
            h = hashlib.sha256(content.encode("utf-8")).hexdigest()
            chunks.append(
                TextChunk(
                    content=content,
                    heading=sec["heading"],
                    section=sec["heading"],
                    token_count=approximate_token_count(content),
                    content_hash=h,
                )
            )
        else:
            # Sliding window over words
            start = 0
            while start < len(words):
                end = min(start + max_chunk_words, len(words))
                chunk_words = words[start:end]
                sub_text = " ".join(chunk_words)
                content = f"[{title} > {sec['heading']}]\n{sub_text}"
                h = hashlib.sha256(content.encode("utf-8")).hexdigest()
                chunks.append(
                    TextChunk(
                        content=content,
                        heading=sec["heading"],
                        section=sec["heading"],
                        token_count=approximate_token_count(content),
                        content_hash=h,
                    )
                )
                if end >= len(words):
                    break
                start += (max_chunk_words - overlap_words)

    return chunks
