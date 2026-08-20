"""
Conversation and Messaging Schemas for WebLens AI.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class MessageRole(str):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class SourceCitation(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[str] = None
    url: str
    title: Optional[str] = None
    section: Optional[str] = None
    chunk_id: Optional[str] = None
    relevance_score: float = 1.0
    snippet: Optional[str] = None


class MessageCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=4000, description="User question or follow-up request")


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    conversation_id: str
    role: str
    content: str
    sources: List[SourceCitation] = []
    created_at: datetime


class ConversationCreate(BaseModel):
    website_id: str
    title: Optional[str] = None


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    website_id: str
    title: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse] = []
