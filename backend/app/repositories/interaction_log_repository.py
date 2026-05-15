"""
Interaction log repository.

Handles database operations related to
system interaction logs.
"""

from sqlalchemy.orm import Session

from app.models.interaction_log import (
    InteractionLog
)


class InteractionLogRepository:
    """
    Repository for interaction log database operations.
    """

    @staticmethod
    def create_log(
        db: Session,
        conversation_id,
        event_type: str,
        log_message: str
    ) -> InteractionLog:
        """
        Store interaction/system log.
        """

        interaction_log = InteractionLog(
            conversation_id=conversation_id,
            event_type=event_type,
            log_message=log_message
        )

        db.add(interaction_log)

        db.commit()

        db.refresh(interaction_log)

        return interaction_log