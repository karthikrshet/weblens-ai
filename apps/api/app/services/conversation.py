"""
Multi-turn Conversation Management Service.
Maintains chat context, executes agent investigations, persists messages,
and links source citations to specific answers.
"""

from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.entities import Website, Conversation, Message, Source, ToolExecution
from app.agents.orchestrator import AgentOrchestrator
from packages.schemas.conversation import MessageResponse, ConversationResponse, SourceCitation


class ConversationService:
    def __init__(self, db: Session):
        self.db = db

    def get_or_create_conversation(self, website_id: str, title: Optional[str] = None) -> Conversation:
        website = self.db.query(Website).filter(Website.id == website_id).first()
        if not website:
            raise HTTPException(status_code=404, detail="Website not found")

        conv = Conversation(
            website_id=website_id,
            title=title or f"Chat with {website.name or website.domain}",
        )
        self.db.add(conv)
        self.db.commit()
        self.db.refresh(conv)
        return conv

    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        return self.db.query(Conversation).filter(Conversation.id == conversation_id).first()

    async def send_user_message(
        self,
        conversation_id: str,
        content: str,
    ) -> Tuple[Message, List[SourceCitation], List[ToolExecution]]:
        """
        Record user message, run agent investigation, store assistant response & sources.
        """
        conv = self.get_conversation(conversation_id)
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")

        website = self.db.query(Website).filter(Website.id == conv.website_id).first()
        if not website:
            raise HTTPException(status_code=404, detail="Associated website not found")

        # 1. Store User Message
        user_msg = Message(
            conversation_id=conversation_id,
            role="user",
            content=content,
        )
        self.db.add(user_msg)
        self.db.commit()

        # 2. Run Agent Orchestrator
        orchestrator = AgentOrchestrator(db=self.db, website=website)
        answer_text, citations, tools = await orchestrator.run_investigation(
            query=content,
            conversation_id=conversation_id,
        )

        # 3. Store Assistant Message
        assistant_msg = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=answer_text,
        )
        self.db.add(assistant_msg)
        self.db.flush()

        # 4. Attach Source Citations
        for c in citations:
            src = Source(
                message_id=assistant_msg.id,
                chunk_id=c.chunk_id,
                url=c.url,
                title=c.title,
                section=c.section,
                relevance_score=c.relevance_score,
                snippet=c.snippet,
            )
            self.db.add(src)

        self.db.commit()
        self.db.refresh(assistant_msg)

        return assistant_msg, citations, tools
