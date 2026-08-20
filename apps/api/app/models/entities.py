"""
SQLAlchemy Domain Entities for WebLens AI.
"""

import uuid
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

from sqlalchemy import (
    Column,
    String,
    Text,
    Float,
    Integer,
    DateTime,
    ForeignKey,
    JSON,
    Boolean,
    Index,
)
from sqlalchemy.orm import relationship

from app.models.db import Base


def generate_uuid() -> str:
    return uuid.uuid4().hex


class Website(Base):
    __tablename__ = "websites"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    url = Column(String(2048), nullable=False)
    canonical_url = Column(String(2048), nullable=False, unique=True, index=True)
    domain = Column(String(255), nullable=False, index=True)
    name = Column(String(255), nullable=True)
    website_type = Column(String(100), nullable=True)
    secondary_types = Column(JSON, default=list)
    industry = Column(String(255), nullable=True)
    purpose = Column(Text, nullable=True)
    target_audience = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    confidence = Column(Float, default=0.0)
    language = Column(String(10), default="en")
    
    categories = Column(JSON, default=list)
    products_or_services = Column(JSON, default=list)
    key_features = Column(JSON, default=list)
    key_pages = Column(JSON, default=list)
    limitations = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_crawled_at = Column(DateTime, nullable=True)

    # Relationships
    pages = relationship("WebsitePage", back_populates="website", cascade="all, delete-orphan")
    chunks = relationship("ContentChunk", back_populates="website", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="website", cascade="all, delete-orphan")
    runs = relationship("AnalysisRun", back_populates="website", cascade="all, delete-orphan")


class WebsitePage(Base):
    __tablename__ = "website_pages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    website_id = Column(String(36), ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True)
    url = Column(String(2048), nullable=False, index=True)
    title = Column(String(512), nullable=True)
    description = Column(Text, nullable=True)
    content = Column(Text, nullable=True)  # Clean extracted markdown/text
    raw_html = Column(Text, nullable=True) # Trimmed raw HTML for debugging/parsing
    depth = Column(Integer, default=0)
    status = Column(String(50), default="completed")
    content_hash = Column(String(64), nullable=True, index=True)
    http_status = Column(Integer, nullable=True)
    content_type = Column(String(100), default="text/html")
    crawled_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    website = relationship("Website", back_populates="pages")
    chunks = relationship("ContentChunk", back_populates="page", cascade="all, delete-orphan")


class ContentChunk(Base):
    __tablename__ = "content_chunks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    website_id = Column(String(36), ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True)
    page_id = Column(String(36), ForeignKey("website_pages.id", ondelete="CASCADE"), nullable=False, index=True)
    url = Column(String(2048), nullable=False)
    title = Column(String(512), nullable=True)
    heading = Column(String(512), nullable=True)
    section = Column(String(255), nullable=True)
    content = Column(Text, nullable=False)
    token_count = Column(Integer, default=0)
    embedding = Column(JSON, nullable=True) # Serialized float array for cross-DB compatibility
    chunk_metadata = Column(JSON, default=dict)
    content_hash = Column(String(64), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    website = relationship("Website", back_populates="chunks")
    page = relationship("WebsitePage", back_populates="chunks")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    website_id = Column(String(36), ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    website = relationship("Website", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")
    tool_executions = relationship("ToolExecution", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(50), nullable=False) # user | assistant | system
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    sources = relationship("Source", back_populates="message", cascade="all, delete-orphan")


class Source(Base):
    __tablename__ = "sources"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    message_id = Column(String(36), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False, index=True)
    page_id = Column(String(36), ForeignKey("website_pages.id", ondelete="SET NULL"), nullable=True)
    chunk_id = Column(String(36), ForeignKey("content_chunks.id", ondelete="SET NULL"), nullable=True)
    url = Column(String(2048), nullable=False)
    title = Column(String(512), nullable=True)
    section = Column(String(255), nullable=True)
    relevance_score = Column(Float, default=1.0)
    snippet = Column(Text, nullable=True)

    # Relationships
    message = relationship("Message", back_populates="sources")


class ToolExecution(Base):
    __tablename__ = "tool_executions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    run_id = Column(String(36), ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=True, index=True)
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=True, index=True)
    tool_name = Column(String(100), nullable=False)
    safe_input_summary = Column(Text, nullable=False)
    result_summary = Column(Text, nullable=False)
    status = Column(String(50), default="success") # pending, success, failed, blocked
    duration_ms = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    run = relationship("AnalysisRun", back_populates="tool_executions")
    conversation = relationship("Conversation", back_populates="tool_executions")


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    website_id = Column(String(36), ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(50), default="pending") # pending, running, completed, failed, cancelled
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    error = Column(Text, nullable=True)
    metrics = Column(JSON, default=dict)

    # Relationships
    website = relationship("Website", back_populates="runs")
    tool_executions = relationship("ToolExecution", back_populates="run", cascade="all, delete-orphan")


class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    benchmark_name = Column(String(255), nullable=False)
    total_cases = Column(Integer, default=0)
    passed_cases = Column(Integer, default=0)
    metrics = Column(JSON, default=dict) # precision, recall, groundedness, latency, cost
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    results = Column(JSON, default=list)
