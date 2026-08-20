"""
Website intelligence schemas and domain types.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class WebsiteType(str, Enum):
    ECOMMERCE = "ecommerce"
    SAAS = "saas"
    HEALTHCARE = "healthcare"
    EDUCATION = "education"
    FINANCE = "finance"
    GOVERNMENT = "government"
    NONPROFIT = "nonprofit"
    MEDIA = "media"
    NEWS = "news"
    TRAVEL = "travel"
    FOOD = "food"
    MARKETPLACE = "marketplace"
    DEVELOPER_DOCUMENTATION = "developer_documentation"
    PORTFOLIO = "portfolio"
    COMMUNITY = "community"
    BLOG = "blog"
    OTHER = "other"


class KeyPage(BaseModel):
    url: str
    title: Optional[str] = None
    category: str = "general"
    relevance_score: float = 1.0


class StructuredWebsiteProfile(BaseModel):
    name: str = Field(description="Name of the company or website")
    url: str = Field(description="Canonical URL of the website")
    website_type: WebsiteType = Field(default=WebsiteType.OTHER, description="Primary domain classification")
    secondary_types: List[WebsiteType] = Field(default_factory=list, description="Secondary domain classifications")
    industry: str = Field(description="Primary industry or vertical")
    purpose: str = Field(description="Core purpose and mission of the website")
    target_audience: str = Field(description="Primary target users/consumers/businesses")
    categories: List[str] = Field(default_factory=list, description="Main categories or taxonomies")
    products_or_services: List[str] = Field(default_factory=list, description="List of key offerings or services")
    key_features: List[str] = Field(default_factory=list, description="Key features or capabilities identified")
    key_pages: List[KeyPage] = Field(default_factory=list, description="Important discovered pages")
    summary: str = Field(description="Concise grounded overview of the website")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Classification confidence score")
    limitations: Optional[str] = Field(default=None, description="Any data limitations or caveats (e.g. medical disclaimer)")


class WebsiteAnalyzeRequest(BaseModel):
    url: str = Field(..., description="Target website URL to analyze")
    force_refresh: bool = Field(default=False, description="Bypass cache and recrawl")
    max_pages: Optional[int] = Field(default=None, ge=1, le=50, description="Override maximum crawl limit")


class WebsiteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    url: str
    canonical_url: str
    domain: str
    name: Optional[str] = None
    website_type: Optional[str] = None
    industry: Optional[str] = None
    purpose: Optional[str] = None
    target_audience: Optional[str] = None
    summary: Optional[str] = None
    confidence: Optional[float] = None
    language: Optional[str] = "en"
    categories: List[str] = []
    products_or_services: List[str] = []
    key_features: List[str] = []
    key_pages: List[Dict[str, Any]] = []
    limitations: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    last_crawled_at: Optional[datetime] = None
    page_count: int = 0
    chunk_count: int = 0


class PageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    website_id: str
    url: str
    title: Optional[str] = None
    description: Optional[str] = None
    depth: int = 0
    http_status: Optional[int] = None
    crawled_at: datetime
