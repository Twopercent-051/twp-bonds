import logging
import os

import betterlogging as bl

from aiogram import Bot, Dispatcher
from fastapi import FastAPI
from starlette.templating import Jinja2Templates

from config import config

bot = Bot(token=config.bot_token)
dp = Dispatcher()

app = FastAPI()
templates = Jinja2Templates(directory=f"{os.getcwd()}/templates")

database_url = (
    f"postgresql+asyncpg://"
    f"{config.db_user}:"
    f"{config.db_pass}@"
    f"{config.db_host}:"
    f"{config.db_port}/"
    f"{config.db_name}"
)

logger = logging.getLogger(__name__)
log_level = logging.INFO
bl.basic_colorized_config(level=log_level)
