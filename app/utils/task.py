# app/utils/task.py
import uuid
from typing import Dict, Any, Coroutine
import time
import asyncio


class TaskManager:
    def __init__(self, ttl: int = 600):
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.ttl = ttl  # seconds

    def add_task(self, task):
        task_id = str(uuid.uuid4())
        self.tasks[task_id] = {"task": task, "timestamp": time.time()}
        return task_id

    def get_task(self, task_id):
        data = self.tasks.get(task_id)
        if not data:
            return None

        # 如果过期，立即删除
        if time.time() - data["timestamp"] > self.ttl:
            del self.tasks[task_id]
            return None

        return data["task"]

    def remove_task(self, task_id):
        return self.tasks.pop(task_id, None) is not None

    def cleanup(self):
        """主动清理过期任务"""
        now = time.time()
        expired = [
            task_id
            for task_id, data in self.tasks.items()
            if now - data["timestamp"] > self.ttl
        ]
        for task_id in expired:
            del self.tasks[task_id]


task_manager = TaskManager()


async def cleanup_worker(task_manager: TaskManager):
    while True:
        task_manager.cleanup()
        await asyncio.sleep(60)  # 每分钟清理一次
