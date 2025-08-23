from __future__ import annotations
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.db.mixins import TimestampedMixin, _uuid4
from app.models.identity import Identity

class User(Base, TimestampedMixin):
    __tablename__ = "user"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid4)
    uid: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    nickname: Mapped[str | None] = mapped_column(String(100))
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    identities: Mapped[list[Identity]] = relationship(
        back_populates="user", cascade="all, delete-orphan", lazy="selectin", 
    )
