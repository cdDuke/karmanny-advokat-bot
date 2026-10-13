from __future__ import annotations

from sqlalchemy import BigInteger, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class LegalCase(Base, TimestampMixin):
    __tablename__ = "legal_cases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    status: Mapped[str] = mapped_column(String(64), default="🟢 Анализ", nullable=False)
    mode: Mapped[str] = mapped_column(String(64), default="💬 Простыми словами", nullable=False)
    context: Mapped[str] = mapped_column(Text, nullable=False)
    last_action: Mapped[str] = mapped_column(String(256), nullable=False)

    user = relationship("User", back_populates="legal_cases")
    materials = relationship("CaseMaterial", back_populates="case", cascade="all, delete-orphan")


class CaseMaterial(Base, TimestampMixin):
    __tablename__ = "case_materials"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[int] = mapped_column(Integer, ForeignKey("legal_cases.id"), index=True, nullable=False)
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    file_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    case = relationship("LegalCase", back_populates="materials")
