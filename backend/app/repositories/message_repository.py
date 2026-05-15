"""
Message repository.

Handles database operations related to
conversation messages.
"""

from sqlalchemy.orm import Session

from app.models.message import Message


class MessageRepository:
    """
    Repository for message database operations.
    """

    @staticmethod
    def create_message(
        db: Session,
        conversation_id,
        sender: str,
        message_text: str
    ) -> Message:
        """
        Store conversation message.
        """

        message = Message(
            conversation_id=conversation_id,
            sender=sender,
            message_text=message_text
        )

        db.add(message)

        db.commit()

        db.refresh(message)

        return message