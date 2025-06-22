import logging
import os

import betterlogging as bl

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from starlette.templating import Jinja2Templates

from config import config


bot = Bot(token=config.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()


templates = Jinja2Templates(directory=f"{os.getcwd()}/templates")

database_url = (
    f"postgresql+asyncpg://"
    f"{config.db_user}:"
    f"{config.db_pass}@"
    f"{config.db_host}:"
    f"{config.db_port}/"
    f"{config.db_name}"
)
scheduler = AsyncIOScheduler(timezone="UTC")


TLG_PATH = f"/{config.bot_token}"
TLG_URL = config.webhook_url + "/bot" + TLG_PATH

logger = logging.getLogger(__name__)
log_level = logging.INFO
bl.basic_colorized_config(level=log_level)
