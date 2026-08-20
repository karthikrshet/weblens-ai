"""
FastAPI REST API and SSE Streaming Endpoints for WebLens AI.
"""

import json
import asyncio
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.models.db import get_db, SessionLocal
from app.models.entities import Website, WebsitePage, ContentChunk, Conversation, Message, Source, ToolExecution, AnalysisRun
from packages.schemas.website import (
    WebsiteAnalyzeRequest,
    WebsiteResponse,
    PageResponse,
)
from packages.schemas.conversation import (
    ConversationCreate,
    ConversationResponse,
    MessageCreate,
    MessageResponse,
    SourceCitation,
)
from packages.schemas.agent import (
    AnalysisRunResponse,
    ToolExecutionRecord,
    StreamEventType,
)
from app.services.intelligence import WebsiteIntelligenceService
from app.services.conversation import ConversationService
from app.agents.orchestrator import AgentOrchestrator
from app.security.ssrf import validate_url_security, SSRFValidationError, InvalidURLError

router = APIRouter()


# --- Health & Readiness ---

@router.get("/health")
def health_check():
    return {"status": "ok", "service": "WebLens AI API", "version": "0.1.0"}


@router.get("/ready")
def readiness_check(db: Session = Depends(get_db)):
    try:
        # Check DB connection
        db.execute("SELECT 1")
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        return {"status": "ready", "database": "sqlite_ready"}


# --- Website Analysis ---

@router.post("/websites/analyze", response_model=WebsiteResponse)
async def analyze_website(
    request: WebsiteAnalyzeRequest,
    db: Session = Depends(get_db),
):
    """
    Analyze a website URL: validates URL, crawls pages, classifies domain, extracts intelligence & builds RAG index.
    """
    try:
        validate_url_security(request.url, enforce_dns=False)
    except (SSRFValidationError, InvalidURLError) as e:
        raise HTTPException(status_code=400, detail=str(e))

    service = WebsiteIntelligenceService(db=db)
    try:
        website, profile, pages = await service.analyze_website(
            target_url=request.url,
            force_refresh=request.force_refresh,
            max_crawl_pages=request.max_pages,
        )

        page_count = db.query(WebsitePage).filter(WebsitePage.website_id == website.id).count()
        chunk_count = db.query(ContentChunk).filter(ContentChunk.website_id == website.id).count()

        resp = WebsiteResponse.from_orm(website)
        resp.page_count = page_count
        resp.chunk_count = chunk_count
        return resp
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Website analysis failed: {str(e)}")


@router.get("/websites/analyze/stream")
async def stream_website_analysis(
    url: str = Query(..., description="URL to analyze"),
    force_refresh: bool = Query(False),
):
    """
    Server-Sent Events (SSE) stream providing real-time website analysis telemetry.
    """
    async def event_generator():
        # Validate URL
        yield f"event: {StreamEventType.ANALYSIS_STARTED.value}\ndata: {json.dumps({'message': 'Starting analysis', 'url': url})}\n\n"
        await asyncio.sleep(0.1)

        try:
            canonical_url, _ = validate_url_security(url, enforce_dns=False)
            yield f"event: {StreamEventType.URL_VALIDATED.value}\ndata: {json.dumps({'canonical_url': canonical_url})}\n\n"
            await asyncio.sleep(0.1)

            yield f"event: {StreamEventType.FETCH_STARTED.value}\ndata: {json.dumps({'message': 'Fetching homepage'})}\n\n"
            
            db = SessionLocal()
            service = WebsiteIntelligenceService(db=db)

            website, profile, pages = await service.analyze_website(target_url=url, force_refresh=force_refresh)
            
            yield f"event: {StreamEventType.FETCH_COMPLETED.value}\ndata: {json.dumps({'pages_fetched': len(pages)})}\n\n"
            yield f"event: {StreamEventType.CLASSIFICATION_COMPLETED.value}\ndata: {json.dumps({'type': website.website_type, 'confidence': website.confidence})}\n\n"
            yield f"event: {StreamEventType.INDEXING_COMPLETED.value}\ndata: {json.dumps({'status': 'indexed'})}\n\n"
            
            payload = {
                "id": website.id,
                "url": website.url,
                "name": website.name,
                "website_type": website.website_type,
                "industry": website.industry,
                "purpose": website.purpose,
                "target_audience": website.target_audience,
                "summary": website.summary,
                "confidence": website.confidence,
                "categories": website.categories,
                "products_or_services": website.products_or_services,
                "key_features": website.key_features,
                "key_pages": website.key_pages,
            }
            yield f"event: {StreamEventType.ANALYSIS_COMPLETED.value}\ndata: {json.dumps(payload)}\n\n"
            db.close()

        except Exception as e:
            yield f"event: {StreamEventType.ERROR.value}\ndata: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/websites/{id}", response_model=WebsiteResponse)
def get_website(id: str, db: Session = Depends(get_db)):
    website = db.query(Website).filter(Website.id == id).first()
    if not website:
        raise HTTPException(status_code=404, detail="Website profile not found")
    
    page_count = db.query(WebsitePage).filter(WebsitePage.website_id == website.id).count()
    chunk_count = db.query(ContentChunk).filter(ContentChunk.website_id == website.id).count()
    
    resp = WebsiteResponse.from_orm(website)
    resp.page_count = page_count
    resp.chunk_count = chunk_count
    return resp


@router.get("/websites/{id}/pages", response_model=List[PageResponse])
def get_website_pages(id: str, db: Session = Depends(get_db)):
    pages = db.query(WebsitePage).filter(WebsitePage.website_id == id).all()
    return [PageResponse.from_orm(p) for p in pages]


# --- Conversations & Follow-up Q&A ---

@router.post("/conversations", response_model=ConversationResponse)
def create_conversation(request: ConversationCreate, db: Session = Depends(get_db)):
    service = ConversationService(db=db)
    conv = service.get_or_create_conversation(website_id=request.website_id, title=request.title)
    return ConversationResponse.from_orm(conv)


@router.get("/conversations/{id}", response_model=ConversationResponse)
def get_conversation(id: str, db: Session = Depends(get_db)):
    conv = db.query(Conversation).filter(Conversation.id == id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return ConversationResponse.from_orm(conv)


@router.post("/conversations/{id}/messages", response_model=MessageResponse)
async def post_message(
    id: str,
    request: MessageCreate,
    db: Session = Depends(get_db),
):
    service = ConversationService(db=db)
    assistant_msg, citations, tools = await service.send_user_message(
        conversation_id=id,
        content=request.content,
    )
    
    resp = MessageResponse.from_orm(assistant_msg)
    resp.sources = [SourceCitation.from_orm(s) for s in assistant_msg.sources]
    return resp


@router.get("/conversations/{id}/sources", response_model=List[SourceCitation])
def get_conversation_sources(id: str, db: Session = Depends(get_db)):
    messages = db.query(Message).filter(Message.conversation_id == id).all()
    msg_ids = [m.id for m in messages]
    sources = db.query(Source).filter(Source.message_id.in_(msg_ids)).all()
    return [SourceCitation.from_orm(s) for s in sources]


# --- Agent Observability & Telemetry ---

@router.get("/conversations/{id}/telemetry", response_model=List[ToolExecutionRecord])
def get_conversation_telemetry(id: str, db: Session = Depends(get_db)):
    executions = db.query(ToolExecution).filter(ToolExecution.conversation_id == id).order_by(ToolExecution.created_at.desc()).all()
    return [ToolExecutionRecord.from_orm(e) for e in executions]
