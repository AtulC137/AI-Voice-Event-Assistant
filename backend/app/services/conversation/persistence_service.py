"""
Conversation persistence service.

Responsible for:
- conversation persistence
- message storage
- transcript storage
- interaction logging
"""

from sqlalchemy.orm import Session

from app.repositories.message_repository import (
    MessageRepository
)

from app.repositories.transcript_repository import (
    TranscriptRepository
)

from app.repositories.interaction_log_repository import (
    InteractionLogRepository
)

from app.repositories.conversation_repository import (
    ConversationRepository
)


class PersistenceService:
    """
    Central persistence service for conversation data.
    """

    def __init__(
        self,
        db: Session
    ):
        """
        Initialize persistence service.
        """

        self.db = db

    def store_message(
        self,
        conversation_id,
        sender: str,
        message_text: str
    ):
        """
        Store conversation message.
        """

        return MessageRepository.create_message(
            db=self.db,
            conversation_id=conversation_id,
            sender=sender,
            message_text=message_text
        )

    def store_transcript(
        self,
        conversation_id,
        transcript_text: str
    ):
        """
        Store conversation transcript.
        """

        return TranscriptRepository.create_transcript(
            db=self.db,
            conversation_id=conversation_id,
            transcript_text=transcript_text
        )

    def store_log(
        self,
        conversation_id,
        event_type: str,
        log_message: str
    ):
        """
        Store interaction/system log.
        """

        return InteractionLogRepository.create_log(
            db=self.db,
            conversation_id=conversation_id,
            event_type=event_type,
            log_message=log_message
        )

    def update_intent(
        self,
        conversation_id,
        intent: str
    ):
        """
        Update conversation intent.
        """

        return ConversationRepository.update_intent(
            db=self.db,
            conversation_id=conversation_id,
            intent=intent
        )