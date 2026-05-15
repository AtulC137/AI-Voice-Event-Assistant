"""
Interaction log database model.
Stores debugging, latency, and system interaction logs.
"""

import uuid

from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    ForeignKey
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class InteractionLog(Base):
    """
    Stores system logs and interaction events
    during conversations.
    """

    __tablename__ = "interaction_logs"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id"),
        nullable=False
    )

    event_type = Column(
        String,
        nullable=False
    )

    log_message = Column(
        Text,
        nullable=False
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    conversation = relationship(
        "Conversation",
        back_populates="interaction_logs"
    )