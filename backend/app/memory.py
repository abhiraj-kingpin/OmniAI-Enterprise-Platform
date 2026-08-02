"""Short-term conversation memory, keyed by session id.

Process-local and in-memory by design — this is the foundation slice for the
Multi-LLM Chat module. Swap this store for a Redis- or Postgres-backed one
(see the Enterprise RAG / MLOps modules) once conversations need to survive a
restart or be shared across workers.
"""

from app.schemas import ChatMessage

# Sliding-window context management: once a session's history exceeds this
# many messages, the oldest ones are dropped so the prompt sent to the model
# doesn't grow unbounded. A production system would summarize/compact instead
# of truncating — see shared/prompt-caching.md and the compaction API.
MAX_HISTORY_MESSAGES = 40


class ConversationStore:
    def __init__(self) -> None:
        self._sessions: dict[str, list[ChatMessage]] = {}

    def get(self, session_id: str) -> list[ChatMessage]:
        return self._sessions.setdefault(session_id, [])

    def append(self, session_id: str, message: ChatMessage) -> None:
        history = self.get(session_id)
        history.append(message)
        overflow = len(history) - MAX_HISTORY_MESSAGES
        if overflow > 0:
            del history[:overflow]

    def clear(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)


store = ConversationStore()
