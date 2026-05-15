"""
User database model.
Stores user/caller information.
"""

import uuid

from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class User(Base):
    """
    User model representing a caller/user interacting
    with the AI voice assistant.
    """

    __tablename__ = "users"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    name = Column(
        String,
        nullable=True
    )

    phone_number = Column(
        String,
        unique=True,
        nullable=True
    )

    preferred_language = Column(
        String,
        nullable=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    conversations = relationship(
        "Conversation",
        back_populates="user"
    )