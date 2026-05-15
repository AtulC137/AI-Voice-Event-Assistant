"""
Conversation database model.
Represents one complete AI voice conversation session.
"""

import uuid

from sqlalchemy import (
    Column,
    String,
    DateTime,
    ForeignKey,
    Interval
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Conversation(Base):
    """
    Stores conversation session details.
    """

    __tablename__ = "conversations"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False
    )

    status = Column(
        String,
        nullable=False,
        default="active"
    )

    final_intent = Column(
        String,
        nullable=True
    )

    conversation_duration = Column(
        Interval,
        nullable=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    user = relationship(
        "User",
        back_populates="conversations"
    )

    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan"
    )

    transcripts = relationship(
        "Transcript",
        back_populates="conversation",
        cascade="all, delete-orphan"
    )

    interaction_logs = relationship(
        "InteractionLog",
        back_populates="conversation",
        cascade="all, delete-orphan"
    )