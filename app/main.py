from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from app.config import get_settings
from app.database.connection import create_session_factory, init_db
from app.handlers import admin, cases, claim, consultation, contract, errors, flows, frequent, history, menu, profile, start
from app.middlewares.database import DatabaseSessionMiddleware, UserMiddleware
from app.ocr.extractors import DocumentTextExtractor
from app.ocr.tesseract import TesseractOCR
from app.services.claim import ClaimService
from app.services.bot_profile import setup_bot_profile
from app.services.consultation import ConsultationService
from app.services.contract import ContractService
from app.services.llm import LLMService
from app.utils.logging import configure_logging
from app.utils.paths import ensure_runtime_dirs


async def build_dispatcher() -> tuple[Bot, Dispatcher]:
    settings = get_settings()
    ensure_runtime_dirs(settings)
    configure_logging(settings)

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    if settings.enable_bot_profile_setup:
        await setup_bot_profile(bot)
    session_factory, engine = create_session_factory(settings.database_url)
    await init_db(engine)

    llm_service = LLMService(settings)
    ocr_service = TesseractOCR(settings)
    extractor = DocumentTextExtractor(settings, ocr_service)

    dp = Dispatcher(storage=MemoryStorage())
    dp.workflow_data.update(
        settings=settings,
        session_factory=session_factory,
        consultation_service=ConsultationService(llm_service),
        contract_service=ContractService(settings, extractor, llm_service),
        claim_service=ClaimService(settings, llm_service),
    )

    db_middleware = DatabaseSessionMiddleware(session_factory)
    user_middleware = UserMiddleware(settings)
    dp.update.outer_middleware(db_middleware)
    dp.update.outer_middleware(user_middleware)

    dp.include_routers(
        start.router,
        profile.router,
        consultation.router,
        contract.router,
        claim.router,
        flows.router,
        menu.router,
        cases.router,
        frequent.router,
        history.router,
        admin.router,
        errors.router,
    )

    async def on_shutdown() -> None:
        await bot.session.close()
        await engine.dispose()

    dp.shutdown.register(on_shutdown)

    return bot, dp


async def main() -> None:
    bot, dp = await build_dispatcher()
    logging.getLogger(__name__).info("Bot polling started")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


def run() -> None:
    asyncio.run(main())
