import time
from datetime import datetime, timedelta, timezone
from bot.database.mongo import verification_col


async def is_verified(user_id: int) -> bool:
    doc = await verification_col.find_one({"user_id": user_id})
    if not doc:
        return False
    return doc["expires_at"] > datetime.now(timezone.utc)


async def set_verified(user_id: int, duration_seconds: int):
    expires_dt = datetime.now(timezone.utc) + timedelta(seconds=duration_seconds)
    await verification_col.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "user_id": user_id,
                "verified_at": time.time(),
                "expires_at": expires_dt,  # Mongo TTL index needs a Date, not epoch float
            }
        },
        upsert=True,
    )


async def clear_verification(user_id: int):
    await verification_col.delete_one({"user_id": user_id})
