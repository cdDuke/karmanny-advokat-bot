from __future__ import annotations

import logging

from aiogram import Bot
from aiogram.types import BotCommand

logger = logging.getLogger(__name__)


async def setup_bot_profile(bot: Bot) -> None:
    try:
        await bot.set_my_name(name="Карманный Адвокат")
        await bot.set_my_short_description(
            short_description="AI-юрист для России и Казахстана: консультации, документы, риски и понятные правовые ответы."
        )
        await bot.set_my_description(
            description=(
                "⚖️ Карманный Адвокат — юридический AI-помощник для России и Казахстана.\n\n"
                "Бот помогает разобраться в правовой ситуации, проверить договор или документ, найти риски, "
                "подготовить черновик претензии, заявления или жалобы.\n\n"
                "При первом запуске выберите страну: Россию или Казахстан. После этого бот будет отвечать "
                "с учетом законодательства выбранной юрисдикции.\n\n"
                "Ответы носят информационный характер и не заменяют консультацию адвоката или юриста."
            )
        )
        await bot.set_my_commands(
            commands=[
                BotCommand(command="start", description="запуск бота"),
                BotCommand(command="menu", description="главное меню"),
                BotCommand(command="profile", description="профиль"),
                BotCommand(command="country", description="сменить страну"),
                BotCommand(command="about", description="о боте"),
                BotCommand(command="privacy", description="конфиденциальность"),
                BotCommand(command="delete_data", description="удалить мои данные"),
                BotCommand(command="help", description="помощь"),
            ]
        )
    except Exception:
        logger.exception("Bot profile setup failed")
