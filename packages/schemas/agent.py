"""
Agent execution telemetry, tool call definitions, and streaming event schemas.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class ToolStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    BLOCKED = "blocked"


class ToolExecutionRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    run_id: Optional[str] = None
    conversation_id: Optional[str] = None
    tool_name: str
    safe_input_summary: str
    result_summary: str
    status: ToolStatus
    duration_ms: float
    created_at: datetime


class StreamEventType(str, Enum):
    ANALYSIS_STARTED = "analysis_started"
    URL_VALIDATED = "url_validated"
    FETCH_STARTED = "fetch_started"
    FETCH_COMPLETED = "fetch_completed"
    EXTRACTION_COMPLETED = "extraction_completed"
    DISCOVERY_STARTED = "discovery_started"
    DISCOVERY_COMPLETED = "discovery_completed"
    CLASSIFICATION_COMPLETED = "classification_completed"
    INDEXING_COMPLETED = "indexing_completed"
    ANALYSIS_COMPLETED = "analysis_completed"
    
    TOOL_STARTED = "tool_started"
    TOOL_COMPLETED = "tool_completed"
    
    ANSWER_DELTA = "answer_delta"
    ANSWER_COMPLETED = "answer_completed"
    SOURCES_ATTACHED = "sources_attached"
    
    ERROR = "error"


class StreamEvent(BaseModel):
    event: StreamEventType
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AnalysisRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    website_id: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    metrics: Dict[str, Any] = {}
    tool_executions: List[ToolExecutionRecord] = []
