import asyncio

import uvicorn

from create_app import dp, bot, app, logger
from tgbot.handlers.main_handlers import router as tg_router

from web_app.router import router as fastapi_router

app.include_router(fastapi_router)
dp.include_router(tg_router)


async def start_fastapi():
    config = uvicorn.Config(app=app, host="0.0.0.0", port=8001, log_level="warning")
    server = uvicorn.Server(config)
    await server.serve()


async def start_aiogram():
    logger.info("Starting bot")
    try:
        await bot.delete_webhook()
        await dp.start_polling(bot)
    finally:
        await dp.storage.close()
        await bot.session.close()


async def main():
    await asyncio.gather(start_aiogram(), start_fastapi())


if __name__ == "__main__":
    asyncio.run(main())
