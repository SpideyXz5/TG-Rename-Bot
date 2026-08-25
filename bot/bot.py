import asyncio
import functools

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import config
from bot.database.mongo import ensure_indexes
from bot.middlewares import PMOnlyMiddleware, MaintenanceMiddleware
from bot.handlers import all_routers
from bot.services.queue_manager import queue_manager
from bot.workers.rename_worker import process_task
from bot.utils.logger import logger


async def main():
    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    # PM-only must run before maintenance/admin checks.
    dp.message.middleware(PMOnlyMiddleware())
    dp.callback_query.middleware(PMOnlyMiddleware())
    dp.message.middleware(MaintenanceMiddleware())
    dp.callback_query.middleware(MaintenanceMiddleware())

    for router in all_routers:
        dp.include_router(router)

    await ensure_indexes()

    # Bind the bot instance into the single global worker function.
    queue_manager.worker_fn = functools.partial(process_task, bot=bot)
    asyncio.create_task(queue_manager.run_forever())

    logger.info(f"Bot starting... Developer: {config.DEVELOPER_CREDIT}")

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")
