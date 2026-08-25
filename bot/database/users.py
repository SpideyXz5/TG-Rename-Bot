import time
from bot.database.mongo import users_col


async def add_user(user_id: int, first_name: str = "", username: str = ""):
    await users_col.update_one(
        {"user_id": user_id},
        {
            "$setOnInsert": {
                "user_id": user_id,
                "first_name": first_name,
                "username": username,
                "joined_at": time.time(),
            }
        },
        upsert=True,
    )


async def is_known_user(user_id: int) -> bool:
    return await users_col.find_one({"user_id": user_id}) is not None


async def total_users() -> int:
    return await users_col.count_documents({})


async def all_user_ids():
    async for doc in users_col.find({}, {"user_id": 1}):
        yield doc["user_id"]
