"""
Enforces "only ONE rename task runs globally at a time" with a FIFO waiting
line (max 20). Fully in-memory — a restart naturally clears everything,
matching the "do not resume tasks after restart" requirement.
"""
import asyncio
import time
import uuid
from dataclasses import dataclass, field
from typing import Callable, Optional

from bot.config import config


class TaskCancelled(Exception):
    """Raised internally to unwind a rename task cleanly once cancel_event is set."""
    pass


@dataclass
class RenameTask:
    task_id: str
    user_id: int
    chat_id: int
    message: object            # the aiogram Message containing the file
    new_filename: str
    thumbnail_path: Optional[str] = None
    status: str = "queued"
    status_message_id: Optional[int] = None
    cancel_event: asyncio.Event = field(default_factory=asyncio.Event)
    created_at: float = field(default_factory=time.time)

    @staticmethod
    def new(user_id: int, chat_id: int, message, new_filename: str, thumbnail_path=None):
        return RenameTask(
            task_id=str(uuid.uuid4())[:8],
            user_id=user_id,
            chat_id=chat_id,
            message=message,
            new_filename=new_filename,
            thumbnail_path=thumbnail_path,
        )


class QueueManager:
    def __init__(self, max_size: int = config.MAX_QUEUE_SIZE):
        self.max_size = max_size
        self.waiting: list[RenameTask] = []
        self.current: Optional[RenameTask] = None
        self._lock = asyncio.Lock()
        self._new_item = asyncio.Event()
        self.worker_fn: Optional[Callable] = None  # set by workers/rename_worker.py at startup

    async def enqueue(self, task: RenameTask) -> Optional[int]:
        """Returns the 1-based waiting position, or None if the queue is full."""
        async with self._lock:
            if len(self.waiting) >= self.max_size:
                return None
            self.waiting.append(task)
            position = len(self.waiting)
        self._new_item.set()
        return position

    async def cancel(self, task_id: str) -> bool:
        async with self._lock:
            if self.current and self.current.task_id == task_id:
                self.current.cancel_event.set()
                return True
            for t in self.waiting:
                if t.task_id == task_id:
                    self.waiting.remove(t)
                    t.cancel_event.set()
                    return True
        return False

    async def position_of(self, task_id: str) -> Optional[int]:
        async with self._lock:
            for i, t in enumerate(self.waiting):
                if t.task_id == task_id:
                    return i + 1
        return None

    async def cancel_all(self):
        """Used on maintenance/restart — cancels the running task and clears the queue."""
        async with self._lock:
            if self.current:
                self.current.cancel_event.set()
            for t in self.waiting:
                t.cancel_event.set()
            self.waiting.clear()

    def stats(self):
        return {
            "running": 1 if self.current else 0,
            "waiting": len(self.waiting),
        }

    async def run_forever(self):
        while True:
            async with self._lock:
                task = self.waiting.pop(0) if self.waiting else None
                self.current = task

            if task is None:
                self._new_item.clear()
                await self._new_item.wait()
                continue

            if self.worker_fn:
                try:
                    await self.worker_fn(task)
                except Exception:
                    from bot.utils.logger import logger
                    logger.exception(f"Unhandled error processing task {task.task_id}")

            async with self._lock:
                self.current = None


queue_manager = QueueManager()
