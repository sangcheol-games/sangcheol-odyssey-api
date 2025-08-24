from __future__ import annotations
import uuid
from enum import StrEnum
from sqlalchemy import String, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.db.mixins import TimestampedMixin, _uuid4

class Provider(StrEnum):
    google = "google"
    steam = "steam"

class Identity(Base, TimestampedMixin):
    __tablename__ = "identity"
    __table_args__ = (
        UniqueConstraint("provider", "provider_sub", name="uq_identity_provider_sub"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), index=True, nullable=False)

    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    provider_sub: Mapped[str] = mapped_column(String(128), nullable=False)

    email: Mapped[str | None] = mapped_column(String(320))
    email_verified: Mapped[bool | None] = mapped_column(Boolean)

    profile_json: Mapped[dict | None] = mapped_column(JSONB)

    user = relationship("User", back_populates="identities", lazy="selectin", )
