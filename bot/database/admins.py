from bot.config import config
from bot.database.mongo import admins_col


def is_owner(user_id: int) -> bool:
    return user_id == config.OWNER_ID


async def is_admin(user_id: int) -> bool:
    if is_owner(user_id):
        return True
    return await admins_col.find_one({"user_id": user_id}) is not None


async def add_admin(user_id: int, added_by: int) -> bool:
    if await admins_col.find_one({"user_id": user_id}):
        return False
    await admins_col.insert_one({"user_id": user_id, "added_by": added_by})
    return True


async def remove_admin(user_id: int) -> bool:
    result = await admins_col.delete_one({"user_id": user_id})
    return result.deleted_count > 0


async def list_admins():
    admins = []
    async for doc in admins_col.find({}):
        admins.append(doc["user_id"])
    return admins
