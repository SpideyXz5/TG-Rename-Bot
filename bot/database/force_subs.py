from bot.database.mongo import force_subs_col

MAX_FORCE_SUB_SLOTS = 6


async def get_all_force_subs():
    subs = []
    async for doc in force_subs_col.find({}).sort("slot", 1):
        subs.append(doc)
    return subs


async def get_enabled_force_subs():
    subs = []
    async for doc in force_subs_col.find({"enabled": True}).sort("slot", 1):
        subs.append(doc)
    return subs


async def set_force_sub(slot: int, sub_type: str, value: str, enabled: bool = True):
    """sub_type: 'channel' | 'group' | 'folder'; value: chat id or invite link."""
    await force_subs_col.update_one(
        {"slot": slot},
        {"$set": {"slot": slot, "type": sub_type, "value": value, "enabled": enabled}},
        upsert=True,
    )


async def toggle_force_sub(slot: int, enabled: bool):
    await force_subs_col.update_one({"slot": slot}, {"$set": {"enabled": enabled}})


async def delete_force_sub(slot: int):
    await force_subs_col.delete_one({"slot": slot})


async def next_free_slot():
    used = {doc["slot"] async for doc in force_subs_col.find({}, {"slot": 1})}
    for i in range(1, MAX_FORCE_SUB_SLOTS + 1):
        if i not in used:
            return i
    return None
