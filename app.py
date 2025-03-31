import asyncio
from contextlib import asynccontextmanager
from locale import currency

from fastapi import FastAPI
from aiogram.types import Update
import uvicorn

from create_app import TLG_PATH, TLG_URL, dp, bot, logger, config, scheduler
from models.sql_dao import MoneyBalanceDAO
from tgbot.handlers.main_handlers import router as tg_router
from services.scheduler_service import create_task

from web_app.router import router as fastapi_router


async def on_startup():
    logger.info("Starting Bot")
    webhook_info = await bot.get_webhook_info()
    if webhook_info.url != TLG_URL:
        await bot.delete_webhook()
        await bot.set_webhook(url=TLG_URL, drop_pending_updates=True)
    logger.info("Bot started")
    logger.info(webhook_info)
    dp.include_router(tg_router)
    scheduler.remove_all_jobs()
    await create_task()
    scheduler.start()
    balance = await MoneyBalanceDAO.get_one_or_none(currency="RUB")
    if not balance:
        await MoneyBalanceDAO.create_with_return_id(currency="RUB", amount=0)
        logger.info("Balance created")


async def on_shutdown():
    await dp.storage.close()
    await bot.session.close()
    logger.info("Bot stopped")


@asynccontextmanager
async def lifespan(_: FastAPI):
    await on_startup()
    yield
    await on_shutdown()


app = FastAPI(lifespan=lifespan)
app.include_router(fastapi_router)


@app.post(f"/bot{TLG_PATH}", include_in_schema=False)
async def bot_webhook(update: dict):
    telegram_update = Update(**update)
    await dp.feed_update(bot=bot, update=telegram_update)


async def main():
    app_config = uvicorn.Config(app=app, host="0.0.0.0", port=config.inner_port, log_level="info")
    server = uvicorn.Server(config=app_config)
    await server.serve()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("Bot stopped")
