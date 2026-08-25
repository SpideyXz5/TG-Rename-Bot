import time
from bot.database.mongo import tasks_col, stats_col


async def create_task_record(task_id: str, user_id: int, filename: str, filesize: int):
    await tasks_col.insert_one(
        {
            "task_id": task_id,
            "user_id": user_id,
            "filename": filename,
            "filesize": filesize,
            "status": "queued",
            "created_at": time.time(),
        }
    )


async def update_task_status(task_id: str, status: str):
    await tasks_col.update_one(
        {"task_id": task_id}, {"$set": {"status": status, "updated_at": time.time()}}
    )


async def bump_stat(field: str, amount: int = 1):
    await stats_col.update_one(
        {"_id": "global"}, {"$inc": {field: amount}}, upsert=True
    )


async def get_stats() -> dict:
    doc = await stats_col.find_one({"_id": "global"})
    if not doc:
        doc = {}
    return {
        "total_renames": doc.get("total_renames", 0),
        "successful_renames": doc.get("successful_renames", 0),
        "failed_renames": doc.get("failed_renames", 0),
        "cancelled_tasks": doc.get("cancelled_tasks", 0),
        "total_files_processed": doc.get("total_files_processed", 0),
        "total_processing_size": doc.get("total_processing_size", 0),
    }
