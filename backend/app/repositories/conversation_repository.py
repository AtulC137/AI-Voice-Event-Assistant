"""
Conversation repository.

Handles database operations related to
conversation sessions.
"""

from sqlalchemy.orm import Session

from app.models.conversation import Conversation


class ConversationRepository:
    """
    Repository for conversation database operations.
    """

    @staticmethod
    def create_conversation(
        db: Session,
        user_id
    ) -> Conversation:
        """
        Create new conversation session.
        """

        conversation = Conversation(
            user_id=user_id,
            status="active"
        )

        db.add(conversation)

        db.commit()

        db.refresh(conversation)

        return conversation

    @staticmethod
    def update_intent(
        db: Session,
        conversation_id,
        intent: str
    ):
        """
        Update conversation final intent.
        """

        conversation = (
            db.query(Conversation)
            .filter(
                Conversation.id == conversation_id
            )
            .first()
        )

        if conversation:

            conversation.final_intent = intent

            db.commit()

    @staticmethod
    def end_conversation(
        db: Session,
        conversation_id
    ):
        """
        Mark conversation as completed.
        """

        conversation = (
            db.query(Conversation)
            .filter(
                Conversation.id == conversation_id
            )
            .first()
        )

        if conversation:

            conversation.status = "completed"

            db.commit()