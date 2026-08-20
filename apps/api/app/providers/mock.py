"""
Deterministic Mock LLM and Embedding Provider.
Enables full offline testability, CI execution, and demo functionality without requiring paid API keys.
"""

import json
import re
import hashlib
import asyncio
import numpy as np
from typing import List, Dict, Any, Optional, Type, TypeVar, AsyncGenerator
from pydantic import BaseModel

from app.providers.base import LLMProvider
from packages.schemas.website import StructuredWebsiteProfile, WebsiteType, KeyPage

T = TypeVar("T", bound=BaseModel)


class MockLLMProvider(LLMProvider):
    """
    Deterministic provider that parses prompts, performs domain keyword analysis,
    and returns grounded structured website profiles and answers.
    """

    def __init__(self, embedding_dimension: int = 1536):
        self.dim = embedding_dimension

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 1500,
    ) -> str:
        prompt_lower = prompt.lower()
        
        # Check if the prompt includes RETRIEVED WEBSITE EVIDENCE
        if "retrieved website evidence:" in prompt_lower:
            evidence_part = prompt.split("RETRIEVED WEBSITE EVIDENCE:")[-1].strip()
            lines = [l.strip() for l in evidence_part.split("\n") if l.strip() and not l.startswith("---") and len(l) > 30]
            if lines:
                summary_excerpt = " ".join(lines[:3])
                return f"Based on the retrieved website sources: {summary_excerpt[:600]}"

        if "pricing" in prompt_lower:
            return "Based on the retrieved website sources, the company offers multiple pricing tiers ranging from Starter to Enterprise, with monthly and annual billing options."
        elif "product" in prompt_lower or "offer" in prompt_lower:
            return "According to the official website pages, the primary offerings include digital platform access, specialized tools, and customer services."
        elif "medical" in prompt_lower or "health" in prompt_lower or "treatment" in prompt_lower:
            return "The website describes clinical healthcare services. Note: This system summarizes public website statements and does not provide medical advice or validate clinical efficacy."
        return "WebLens AI has analyzed the website content. The site provides comprehensive digital services tailored to modern enterprise workflows."

    async def generate_structured(
        self,
        prompt: str,
        response_model: Type[T],
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
    ) -> T:
        prompt_lower = prompt.lower()

        # Domain classification heuristics
        website_type = WebsiteType.OTHER
        industry = "Technology & Digital Services"
        purpose = "Provides online information and digital solutions."
        audience = "General consumers and businesses."
        confidence = 0.88
        limitations = None

        if any(w in prompt_lower for w in ["shop", "cart", "store", "buy", "checkout", "fashion", "sneaker", "apparel", "sportswear", "footwear", "shoes"]):
            website_type = WebsiteType.ECOMMERCE
            industry = "Retail & E-Commerce"
            purpose = "Direct-to-consumer and business-to-consumer online merchandise sales."
            audience = "Retail shoppers and consumers."
            confidence = 0.95
        elif any(w in prompt_lower for w in ["course", "university", "school", "learn", "academy", "education", "tutorial", "student", "fyp", "project"]):
            website_type = WebsiteType.EDUCATION
            industry = "Education & E-Learning"
            purpose = "Provides educational courses, project guidance, tutorials, and learning resources."
            audience = "Students, learners, developers, and educators."
            confidence = 0.94
        elif any(w in prompt_lower for w in ["docs", "documentation", "api reference", "code tutorial", "standard library"]):
            website_type = WebsiteType.DEVELOPER_DOCUMENTATION
            industry = "Developer Documentation & Technical Reference"
            purpose = "Provides technical guides, API documentation, and code tutorials."
            audience = "Software engineers, developers, and technical architects."
            confidence = 0.96
        elif any(w in prompt_lower for w in ["saas", "software", "analytics", "cloud", "platform", "api", "developer"]):
            website_type = WebsiteType.SAAS
            industry = "Enterprise Software & Cloud Platforms"
            purpose = "Provides cloud-hosted software and developer tools for engineering teams."
            audience = "Engineers, IT professionals, and enterprise businesses."
            confidence = 0.94
        elif any(w in prompt_lower for w in ["health", "clinic", "medical", "patient", "pharma", "doctor", "hospital"]):
            website_type = WebsiteType.HEALTHCARE
            industry = "Healthcare & Clinical Services"
            purpose = "Provides patient care information, clinical resources, and medical appointment booking."
            audience = "Patients, healthcare practitioners, and caregivers."
            confidence = 0.92
            limitations = "Medical website summary: Statements are based solely on public website content and are not medical advice."
        elif any(w in prompt_lower for w in ["bank", "invest", "finance", "loan", "crypto", "trading"]):
            website_type = WebsiteType.FINANCE
            industry = "Financial Services & Banking"
            purpose = "Provides wealth management, banking, and financial transactions."
            audience = "Retail investors and commercial clients."
            confidence = 0.93

        # Extract name from title or description in prompt
        name_match = re.search(r"title:\s*([^\n\r]+)", prompt, re.IGNORECASE)
        name = name_match.group(1).strip() if name_match else "Analyzed Website"
        name = name.split("-")[0].split("|")[0].split("–")[0].strip()

        # Extract meta description if available
        desc_match = re.search(r"description:\s*([^\n\r]+)", prompt, re.IGNORECASE)
        real_desc = desc_match.group(1).strip() if desc_match and desc_match.group(1).strip() != "N/A" else ""

        # Extract content snippet
        content_match = re.search(r"content:\s*([\s\S]+)", prompt, re.IGNORECASE)
        content_text = content_match.group(1).strip() if content_match else ""
        content_snippet = " ".join([line.strip() for line in content_text.split("\n") if line.strip() and not line.startswith("#")][:4])

        if real_desc:
            purpose = real_desc
            summary = f"{name} operates in the {industry} domain. {real_desc}"
        elif content_snippet:
            summary = f"{name} operates in the {industry} domain. {content_snippet[:300]}"
        else:
            summary = f"{name} operates in the {industry} sector. Its primary mission is: {purpose}"

        # Extract meaningful categories or offerings from headings in prompt
        extracted_headings = re.findall(r"#{1,3}\s+([^\n\r]+)", prompt)
        clean_headings = [h.strip() for h in extracted_headings if len(h.strip()) > 3 and len(h.strip()) < 50][:5]

        categories = clean_headings if clean_headings else ["Core Offerings", "Solutions", "Resources"]
        products_services = [f"{name} {cat}" for cat in categories[:3]] if categories else ["Digital Platform", "Online Services"]

        profile = StructuredWebsiteProfile(
            name=name or "Target Website",
            url="https://example.com",
            website_type=website_type,
            secondary_types=[],
            industry=industry,
            purpose=purpose,
            target_audience=audience,
            categories=categories,
            products_or_services=products_services,
            key_features=["Public platform access", "Resource exploration", "Interactive interface"],
            key_pages=[
                KeyPage(url="/about", title="About Us", category="about", relevance_score=0.90),
                KeyPage(url="/products", title="Offerings", category="products", relevance_score=0.85),
            ],
            summary=summary,
            confidence=confidence,
            limitations=limitations,
        )

        return profile  # type: ignore

    async def stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
    ) -> AsyncGenerator[str, None]:
        full_text = await self.generate(prompt, system_prompt, temperature)
        words = full_text.split(" ")
        for word in words:
            yield word + " "
            await asyncio.sleep(0.02)

    async def embed(self, texts: List[str]) -> List[List[float]]:
        """Generate deterministic normalized mock embeddings."""
        embeddings = []
        for text in texts:
            # Deterministic hash-based vector
            h = hashlib.sha256(text.encode("utf-8")).digest()
            # Generate deterministic pseudo-random floats
            seed = int.from_bytes(h[:4], "big")
            rng = np.random.RandomState(seed)
            vec = rng.randn(self.dim).astype(np.float32)
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            embeddings.append(vec.tolist())
        return embeddings
