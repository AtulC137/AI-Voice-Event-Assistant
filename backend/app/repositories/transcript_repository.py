"""
Transcript repository.

Handles database operations related to
conversation transcripts.
"""

from sqlalchemy.orm import Session

from app.models.transcript import Transcript


class TranscriptRepository:
    """
    Repository for transcript database operations.
    """

    @staticmethod
    def create_transcript(
        db: Session,
        conversation_id,
        transcript_text: str
    ) -> Transcript:
        """
        Store conversation transcript.
        """

        transcript = Transcript(
            conversation_id=conversation_id,
            transcript_text=transcript_text
        )

        db.add(transcript)

        db.commit()

        db.refresh(transcript)

        return transcript