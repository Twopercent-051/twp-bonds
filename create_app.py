import logging
import os

import betterlogging as bl

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from starlette.templating import Jinja2Templates
from redis.asyncio import Redis

from config import config

redis = Redis(host=config.redis.host, port=config.redis.port, db=config.redis.db)
storage = RedisStorage(redis=redis)

bot = Bot(token=config.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=storage)


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
job_store = RedisJobStore(
    jobs_key="bonds_jobs",
    run_times_key="bonds_times",
    host=config.redis.host,
    port=config.redis.port,
    db=config.redis.db,
)
scheduler.add_jobstore(jobstore=job_store, alias="bonds_jobstore")


TLG_PATH = f"/{config.bot_token}"
TLG_URL = config.webhook_url + "/bot" + TLG_PATH

logger = logging.getLogger(__name__)
log_level = logging.INFO
bl.basic_colorized_config(level=log_level)
