from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import Select, delete, func, literal, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import CaseMaterial, Claim, Consultation, Contract, LegalCase, Setting, User


@dataclass(slots=True)
class HistoryItem:
    kind: str
    title: str
    created_at: datetime


class UserRepository:
    async def upsert_from_telegram(
        self,
        session: AsyncSession,
        telegram_user: Any,
        admin_ids: set[int],
    ) -> User:
        user = await session.get(User, telegram_user.id)
        if user is None:
            user = User(id=telegram_user.id, telegram_id=telegram_user.id)
            session.add(user)

        user.telegram_id = telegram_user.id
        user.username = telegram_user.username
        user.first_name = telegram_user.first_name
        user.last_name = telegram_user.last_name
        user.full_name = telegram_user.full_name
        user.is_admin = telegram_user.id in admin_ids
        await session.flush()
        return user

    async def set_country(self, session: AsyncSession, user_id: int, country_code: str) -> User | None:
        user = await session.get(User, user_id)
        if user is None:
            return None
        user.country_code = country_code
        await session.flush()
        return user

    async def increment_requests(self, session: AsyncSession, user_id: int) -> None:
        user = await session.get(User, user_id)
        if user:
            user.requests_count += 1
            await session.flush()

    async def increment_documents(self, session: AsyncSession, user_id: int) -> None:
        user = await session.get(User, user_id)
        if user:
            user.documents_count += 1
            await session.flush()

    async def delete_user_data(self, session: AsyncSession, user_id: int) -> None:
        user = await session.get(User, user_id)
        if user:
            await session.delete(user)
        await session.execute(delete(Setting).where(Setting.key.like(f"user:{user_id}:%")))
        await session.flush()

    async def all_user_ids(self, session: AsyncSession) -> list[int]:
        result = await session.execute(select(User.id))
        return list(result.scalars().all())


class SettingRepository:
    async def get(self, session: AsyncSession, key: str, default: str | None = None) -> str | None:
        item = await session.get(Setting, key)
        return item.value if item else default

    async def set(self, session: AsyncSession, key: str, value: str) -> Setting:
        item = await session.get(Setting, key)
        if item is None:
            item = Setting(key=key, value=value)
            session.add(item)
        else:
            item.value = value
        await session.flush()
        return item

    async def get_user_mode(self, session: AsyncSession, user_id: int) -> str:
        return await self.get(session, f"user:{user_id}:mode", "simple") or "simple"

    async def set_user_mode(self, session: AsyncSession, user_id: int, mode: str) -> Setting:
        return await self.set(session, f"user:{user_id}:mode", mode)


class ConsultationRepository:
    async def create(
        self,
        session: AsyncSession,
        user_id: int,
        question: str,
        answer: str,
    ) -> Consultation:
        item = Consultation(user_id=user_id, question=question, answer=answer)
        session.add(item)
        await session.flush()
        return item


class ContractRepository:
    async def create(
        self,
        session: AsyncSession,
        user_id: int,
        file_name: str,
        extracted_text: str,
        small_print: str | None,
        analysis: str,
        risk_level: str,
    ) -> Contract:
        item = Contract(
            user_id=user_id,
            file_name=file_name,
            extracted_text=extracted_text,
            small_print=small_print,
            analysis=analysis,
            risk_level=risk_level,
        )
        session.add(item)
        await session.flush()
        return item


class ClaimRepository:
    async def create(
        self,
        session: AsyncSession,
        user_id: int,
        full_name: str,
        address: str,
        recipient: str,
        incident_date: str,
        damage_amount: str,
        situation: str,
        document_text: str,
        docx_path: str,
        pdf_path: str,
    ) -> Claim:
        item = Claim(
            user_id=user_id,
            full_name=full_name,
            address=address,
            recipient=recipient,
            incident_date=incident_date,
            damage_amount=damage_amount,
            situation=situation,
            document_text=document_text,
            docx_path=docx_path,
            pdf_path=pdf_path,
        )
        session.add(item)
        await session.flush()
        return item


class CaseRepository:
    async def create_case(
        self,
        session: AsyncSession,
        user_id: int,
        title: str,
        context: str,
        last_action: str,
        mode: str,
        status: str = "🟢 Анализ",
    ) -> LegalCase:
        item = LegalCase(
            user_id=user_id,
            title=title[:256],
            context=context,
            last_action=last_action[:256],
            mode=mode,
            status=status,
        )
        session.add(item)
        await session.flush()
        return item

    async def add_material(
        self,
        session: AsyncSession,
        case_id: int,
        kind: str,
        title: str,
        file_path: str | None = None,
    ) -> CaseMaterial:
        item = CaseMaterial(
            case_id=case_id,
            kind=kind,
            title=title[:256],
            file_path=file_path,
        )
        session.add(item)
        await session.flush()
        return item

    async def get_for_user(self, session: AsyncSession, case_id: int, user_id: int) -> LegalCase | None:
        result = await session.execute(
            select(LegalCase)
            .options(selectinload(LegalCase.materials))
            .where(LegalCase.id == case_id, LegalCase.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def latest_for_user(self, session: AsyncSession, user_id: int, limit: int = 5) -> list[LegalCase]:
        result = await session.execute(
            select(LegalCase)
            .options(selectinload(LegalCase.materials))
            .where(LegalCase.user_id == user_id)
            .order_by(LegalCase.updated_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update_progress(
        self,
        session: AsyncSession,
        item: LegalCase,
        context: str,
        last_action: str,
        status: str = "🟢 Анализ",
    ) -> LegalCase:
        item.context = context
        item.last_action = last_action[:256]
        item.status = status
        await session.flush()
        return item


class HistoryRepository:
    async def latest_for_user(self, session: AsyncSession, user_id: int, limit: int = 10) -> list[HistoryItem]:
        consultation_query = self._history_select(
            Consultation,
            "Консультация",
            Consultation.question,
            user_id,
        )
        contract_query = self._history_select(
            Contract,
            "Проверка договора",
            Contract.file_name,
            user_id,
        )
        claim_query = self._history_select(
            Claim,
            "Претензия",
            Claim.recipient,
            user_id,
        )
        case_query = self._history_select(
            LegalCase,
            "Дело",
            LegalCase.title,
            user_id,
        )

        items: list[HistoryItem] = []
        for query in (consultation_query, contract_query, claim_query, case_query):
            result = await session.execute(query.limit(limit))
            for kind, title, created_at in result.all():
                items.append(HistoryItem(kind=kind, title=title, created_at=created_at))

        return sorted(items, key=lambda item: item.created_at, reverse=True)[:limit]

    @staticmethod
    def _history_select(model: type, kind: str, title_column, user_id: int) -> Select:
        return (
            select(
                literal(kind).label("kind"),
                title_column.label("title"),
                model.created_at.label("created_at"),
            )
            .where(model.user_id == user_id)
            .order_by(model.created_at.desc())
        )


class StatsRepository:
    async def counts(self, session: AsyncSession) -> dict[str, int]:
        return {
            "users": await self._count(session, User),
            "consultations": await self._count(session, Consultation),
            "contracts": await self._count(session, Contract),
            "claims": await self._count(session, Claim),
            "cases": await self._count(session, LegalCase),
        }

    @staticmethod
    async def _count(session: AsyncSession, model: type) -> int:
        result = await session.execute(select(func.count()).select_from(model))
        return int(result.scalar_one())
