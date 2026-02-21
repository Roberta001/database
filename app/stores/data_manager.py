# app/stores/data_manager.py
from typing import Callable, Awaitable
import asyncio

class AsyncDataManager[T]:
    def __init__(self, loader: Callable[[], Awaitable[T]]):
        self._loader = loader
        self._data: T | None = None
        self._lock = asyncio.Lock()

    async def load(self):
        async with self._lock:
            self._data = await self._loader()

    async def get(self) -> T:
        if self._data is None:
            await self.load()
        return self._data  # type: ignore


class AsyncAutoRefreshDataManager[T](AsyncDataManager[T]):
    def __init__(self, db_loader: Callable[[], Awaitable[T]], interval_seconds: int = 300):
        super().__init__(db_loader)
        self._interval = interval_seconds
        self._refresh_task: asyncio.Task | None = None
        self._stop_event = asyncio.Event()

    async def _auto_refresh_loop(self):
        while not self._stop_event.is_set():
            try:
                await self.load()
            except Exception as e:
                print("[AsyncAutoRefresh] Error during reload:", e)

            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=self._interval)
            except asyncio.TimeoutError:
                continue

    async def start_auto_refresh(self):
        if self._refresh_task is None:
            self._stop_event.clear()
            self._refresh_task = asyncio.create_task(self._auto_refresh_loop())

    async def stop_auto_refresh(self):
        self._stop_event.set()
        if self._refresh_task:
            try:
                await self._refresh_task
            except Exception:
                pass
        self._refresh_task = None
