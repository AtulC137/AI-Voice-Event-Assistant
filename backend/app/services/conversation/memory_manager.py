"""
Conversation memory manager.

Responsible for:
- maintaining conversation history
- limiting memory size
- preparing conversational context
"""

from typing import Dict, List


class MemoryManager:
    """
    In-memory conversation history manager.

    Later this can be upgraded to:
    - Redis
    - vector memory
    - persistent session memory
    """

    def __init__(self):
        """
        Initialize memory storage.
        """

        self.memory_store: Dict[str, List[dict]] = {}

    def get_conversation_history(
        self,
        conversation_id: str
    ) -> List[dict]:
        """
        Retrieve conversation history for a session.
        """

        return self.memory_store.get(
            conversation_id,
            []
        )

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str
    ):
        """
        Add message to conversation history.
        """

        if conversation_id not in self.memory_store:
            self.memory_store[conversation_id] = []

        self.memory_store[conversation_id].append(
            {
                "role": role,
                "content": content
            }
        )

    def clear_conversation(
        self,
        conversation_id: str
    ):
        """
        Remove conversation memory for a session.
        """

        if conversation_id in self.memory_store:
            del self.memory_store[conversation_id]