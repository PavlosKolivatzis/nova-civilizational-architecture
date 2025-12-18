"""
Conversation session manager for Phase 17.3 / Phase 18.

Provides:
- Canonical turn stream: List[{"role": "user"|"assistant", "content": str}]
- Session-scoped conversation history
- Phase 17 consent gate integration (feature-flagged)

Design constraints:
- Minimal (no persistence, in-memory only for now)
- Feature-flagged (NOVA_ENABLE_CONVERSATION_HISTORY)
- No governance hooks yet
- No semantic inference
"""

import os
import time
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from threading import Lock

logger = logging.getLogger(__name__)


@dataclass
class Turn:
    """
    Single conversation turn.

    Attributes:
        role: "user" or "assistant"
        content: Turn text content
        timestamp: Unix timestamp
        metadata: Optional turn metadata (phase16_primitives, consent_results, etc.)
    """

    role: str
    content: str
    timestamp: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, str]:
        """Convert to Phase 17 contract format."""
        return {"role": self.role, "content": self.content}


@dataclass
class ConversationSession:
    """
    Conversation session with turn history.

    Attributes:
        session_id: Unique session identifier
        turns: List of Turn objects
        created_at: Session creation timestamp
        last_activity: Last turn timestamp
    """

    session_id: str
    turns: List[Turn] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)

    def add_turn(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> Turn:
        """
        Add a turn to the conversation.

        Args:
            role: "user" or "assistant"
            content: Turn text content
            metadata: Optional turn metadata

        Returns:
            Created Turn object
        """
        if role not in ("user", "assistant"):
            raise ValueError(f"Invalid role: {role}. Must be 'user' or 'assistant'.")

        turn = Turn(
            role=role,
            content=content,
            timestamp=time.time(),
            metadata=metadata or {},
        )
        self.turns.append(turn)
        self.last_activity = turn.timestamp
        return turn

    def get_history(self) -> List[Dict[str, str]]:
        """
        Get conversation history in Phase 17 contract format.

        Returns:
            List[{"role": "user"|"assistant", "content": str}]
        """
        return [turn.to_dict() for turn in self.turns]

    def get_history_up_to(self, turn_index: int) -> List[Dict[str, str]]:
        """
        Get conversation history up to (and including) specified turn index.

        Args:
            turn_index: Index of last turn to include

        Returns:
            List[{"role": "user"|"assistant", "content": str}]
        """
        return [turn.to_dict() for turn in self.turns[: turn_index + 1]]

    def add_assistant_turn_with_provenance(self, content: str) -> Turn:
        """
        Add an assistant turn with C3 provenance metadata.

        Analyzes the turn using Phase 17 consent gate and attaches
        provenance metadata (session_id, primitives, gate reasons, etc.).

        Args:
            content: Assistant turn text content

        Returns:
            Created Turn object with provenance metadata

        Note:
            C3 metadata-only extension. Does not change behavior or policy.
        """
        from nova.orchestrator.conversation.phase17_integration import (
            analyze_turn_with_consent_gate,
        )

        # Get current conversation history before adding this turn
        history_before = self.get_history()
        turn_index = len(self.turns)

        # Analyze turn with consent gate
        analysis = analyze_turn_with_consent_gate(
            turn_content=content,
            conversation_history=history_before
            + [{"role": "assistant", "content": content}],
            session_id=self.session_id,
            turn_index=turn_index,
        )

        # Extract provenance metadata (if present)
        metadata = {}
        if "provenance" in analysis:
            metadata["provenance"] = analysis["provenance"]

        # Add turn with metadata
        return self.add_turn("assistant", content, metadata=metadata)


class SessionManager:
    """
    Manages conversation sessions and turn history.

    Thread-safe, in-memory session storage.
    """

    def __init__(self):
        """Initialize session manager."""
        self._sessions: Dict[str, ConversationSession] = {}
        self._lock = Lock()

    def create_session(self, session_id: str) -> ConversationSession:
        """
        Create a new conversation session.

        Args:
            session_id: Unique session identifier

        Returns:
            ConversationSession object
        """
        with self._lock:
            if session_id in self._sessions:
                logger.warning(f"Session {session_id} already exists, returning existing")
                return self._sessions[session_id]

            session = ConversationSession(session_id=session_id)
            self._sessions[session_id] = session
            logger.info(f"Created conversation session: {session_id}")
            return session

    def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """
        Get existing conversation session.

        Args:
            session_id: Session identifier

        Returns:
            ConversationSession or None if not found
        """
        with self._lock:
            return self._sessions.get(session_id)

    def get_or_create_session(self, session_id: str) -> ConversationSession:
        """
        Get existing session or create new one.

        Args:
            session_id: Session identifier

        Returns:
            ConversationSession object
        """
        session = self.get_session(session_id)
        if session is None:
            session = self.create_session(session_id)
        return session

    def delete_session(self, session_id: str) -> bool:
        """
        Delete conversation session.

        Args:
            session_id: Session identifier

        Returns:
            True if session was deleted, False if not found
        """
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                logger.info(f"Deleted conversation session: {session_id}")
                return True
            return False

    def list_sessions(self) -> List[str]:
        """
        List all active session IDs.

        Returns:
            List of session IDs
        """
        with self._lock:
            return list(self._sessions.keys())

    def get_session_count(self) -> int:
        """
        Get count of active sessions.

        Returns:
            Number of active sessions
        """
        with self._lock:
            return len(self._sessions)


# Global session manager instance
_session_manager: Optional[SessionManager] = None
_manager_lock = Lock()


def get_session_manager() -> SessionManager:
    """
    Get global session manager instance (singleton).

    Returns:
        SessionManager instance
    """
    global _session_manager
    if _session_manager is None:
        with _manager_lock:
            if _session_manager is None:
                _session_manager = SessionManager()
    return _session_manager


def is_conversation_history_enabled() -> bool:
    """
    Check if conversation history tracking is enabled.

    Returns:
        True if NOVA_ENABLE_CONVERSATION_HISTORY=1
    """
    return os.getenv("NOVA_ENABLE_CONVERSATION_HISTORY", "0") == "1"
