"""
Unit tests for Chunker, Hybrid Search, and Website Intelligence Classification.
"""

import pytest
from app.retrieval.chunker import chunk_page_content
from app.retrieval.hybrid import HybridSearchEngine, cosine_similarity
from app.providers.mock import MockLLMProvider
from packages.schemas.website import StructuredWebsiteProfile, WebsiteType


def test_chunk_page_content():
    sample_text = """# Acme SaaS Platform
Acme provides cloud analytics for data engineers.

## Pricing Plans
Our Starter plan is $49/mo and Enterprise is custom.

## Features
- Real-time stream processing
- Anomaly detection
- Automated ETL pipelines
"""
    chunks = chunk_page_content("Acme SaaS", sample_text)
    assert len(chunks) >= 2
    headings = [c.heading for c in chunks]
    assert any("Pricing Plans" in h for h in headings if h)
    assert any("Features" in h for h in headings if h)


@pytest.mark.asyncio
async def test_hybrid_search():
    provider = MockLLMProvider()
    engine = HybridSearchEngine(provider=provider)

    sample_chunks = [
        {
            "id": "c1",
            "page_id": "p1",
            "url": "https://acme.com/pricing",
            "title": "Pricing Plans",
            "heading": "Pricing Plans",
            "section": "Pricing",
            "content": "[Acme SaaS > Pricing Plans] Starter tier is $49 per month with annual discount.",
            "embedding": (await provider.embed(["Starter tier is $49 per month"]))[0],
        },
        {
            "id": "c2",
            "page_id": "p2",
            "url": "https://acme.com/about",
            "title": "About Acme",
            "heading": "Company Story",
            "section": "About",
            "content": "[Acme SaaS > About Company] Founded in 2021 by veterans of big tech.",
            "embedding": (await provider.embed(["Founded in 2021 by veterans of big tech"]))[0],
        },
    ]

    results = await engine.search("What is the cost or pricing of the starter plan?", sample_chunks, top_k=2)
    assert len(results) > 0
    assert results[0].url == "https://acme.com/pricing"
    assert "Starter tier" in results[0].snippet


@pytest.mark.asyncio
async def test_mock_classification_ecommerce():
    provider = MockLLMProvider()
    profile = await provider.generate_structured(
        prompt="Online shoe store with shopping cart and sneakers checkout for retail customers.",
        response_model=StructuredWebsiteProfile,
    )
    assert profile.website_type == WebsiteType.ECOMMERCE
    assert profile.confidence >= 0.90


@pytest.mark.asyncio
async def test_mock_classification_healthcare():
    provider = MockLLMProvider()
    profile = await provider.generate_structured(
        prompt="Clinical medical healthcare center for patient treatment and doctor consultations.",
        response_model=StructuredWebsiteProfile,
    )
    assert profile.website_type == WebsiteType.HEALTHCARE
    assert profile.limitations is not None
