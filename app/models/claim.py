from __future__ import annotations

from sqlalchemy import BigInteger, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Claim(Base, TimestampMixin):
    __tablename__ = "claims"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(256), nullable=False)
    address: Mapped[str] = mapped_column(String(512), nullable=False)
    recipient: Mapped[str] = mapped_column(String(512), nullable=False)
    incident_date: Mapped[str] = mapped_column(String(128), nullable=False)
    damage_amount: Mapped[str] = mapped_column(String(128), nullable=False)
    situation: Mapped[str] = mapped_column(Text, nullable=False)
    document_text: Mapped[str] = mapped_column(Text, nullable=False)
    docx_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    pdf_path: Mapped[str] = mapped_column(String(1024), nullable=False)

    user = relationship("User", back_populates="claims")
