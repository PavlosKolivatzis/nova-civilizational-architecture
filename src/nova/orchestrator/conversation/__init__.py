"""
Conversation session management for Phase 17.3 / Phase 18.

Provides canonical turn stream assembly and conversation history tracking.
Enables Phase 17 consent gate integration.
"""

from nova.orchestrator.conversation.session_manager import (
    ConversationSession,
    SessionManager,
    Turn,
)

__all__ = ["ConversationSession", "SessionManager", "Turn"]
