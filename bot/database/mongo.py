"""
Single Motor (async MongoDB) client shared across the bot.
"""
from motor.motor_asyncio import AsyncIOMotorClient
from bot.config import config

_client = AsyncIOMotorClient(config.MONGO_URI)
db = _client[config.DB_NAME]

users_col = db["users"]
admins_col = db["admins"]
settings_col = db["settings"]
force_subs_col = db["force_subs"]
shortener_col = db["shortener"]
tasks_col = db["tasks"]
stats_col = db["stats"]
verification_col = db["verification"]


async def ensure_indexes():
    await users_col.create_index("user_id", unique=True)
    await admins_col.create_index("user_id", unique=True)
    await force_subs_col.create_index("slot", unique=True)
    await tasks_col.create_index("task_id", unique=True)
    await verification_col.create_index("user_id", unique=True)
    await verification_col.create_index("expires_at", expireAfterSeconds=0)
