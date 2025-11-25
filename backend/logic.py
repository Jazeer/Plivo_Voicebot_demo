# backend/logic.py

"""
Rules-based conversation logic — NO AI.

You can expand the intent rules manually.
"""

from dataclasses import dataclass, field
from backend.utils import logger
import uuid


@dataclass
class Session:
    session_id: str
    context: dict = field(default_factory=dict)


class ConversationManager:

    def __init__(self):
        self.sessions = {}

    # ---------------------------------------------------------
    # Create conversation session
    # ---------------------------------------------------------
    def create_session(self, session_id: str, stream_id: str) -> Session:
        s = Session(session_id=session_id)
        s.context["stream_id"] = stream_id
        self.sessions[session_id] = s
        logger.info(f"Created session {session_id}")
        return s

    # ---------------------------------------------------------
    # End session
    # ---------------------------------------------------------
    def end_session(self, session_id: str):
        if session_id in self.sessions:
            logger.info(f"Ending session {session_id}")
            del self.sessions[session_id]

    # ---------------------------------------------------------
    # Rules-based NLP — no AI, purely pattern matching
    # ---------------------------------------------------------
    def handle_user_utterance(self, session: Session, text: str):
        """
        Return tuple: (reply_text, escalate_flag)
        """

        normalized = text.lower().strip()
        logger.info(f"Handling utterance (normalized): '{normalized}'")

        # -----------------------------------------------------
        # Escalation phrases
        # -----------------------------------------------------
        escalate_keywords = [
            "agent",
            "representative",
            "human",
            "someone else",
            "talk to someone",
            "talk to agent",
            "customer support",
            "speak to a person",
        ]

        for k in escalate_keywords:
            if k in normalized:
                return ("Okay, transferring you to a live agent now.", True)

        # -----------------------------------------------------
        # Simple bot rules
        # -----------------------------------------------------
        if "hello" in normalized or "hi" in normalized:
            return ("Hello! How can I assist you today?", False)

        if "holiday" in normalized:
            return ("We currently have offers available this holiday season!", False)

        if "price" in normalized:
            return ("Our pricing depends on the product. Can you specify which one?", False)

        if "help" in normalized:
            return ("Sure, please tell me what you need help with.", False)

        if "bye" in normalized:
            return ("Thank you for calling. Have a great day!", False)

        # -----------------------------------------------------
        # Default fallback
        # -----------------------------------------------------
        return ("I'm here to assist you. Please tell me more.", False)
