# data_manager.py
from typing import Any, Callable, Awaitable, Iterable
from asyncio import Lock, sleep, Task, create_task
from app.stores.name_store import AsyncNameStore

class AsyncDataManager:
    """
    - 从数据库异步加载
    - 内部维护 AsyncNameStore
    - 提供搜索与更新功能
    - 为 FastAPI 提供统一的数据访问层
    """

    def __init__(self, db_loader: Callable[[], Awaitable[Iterable[str]]]):
        self._db_loader = db_loader
        self.store = AsyncNameStore()
        self._lock = Lock()

    async def load_from_db(self):
        async with self._lock:
            names = await self._db_loader()
            await self.store.load(names)

    async def reload(self):
        async with self._lock:
            names = await self._db_loader()
            await self.store.load(names)

    async def add_name(self, name: str):
        await self.store.add(name)

    async def remove_name(self, name: str):
        await self.store.remove(name)

    async def all_names(self) -> set[str]:
        return await self.store.all()

    async def search(self, keyword: str, matcher: Callable[[str, str], Any]):
        names = await self.store.all()
        results = []
        for n in names:
            score = matcher(n, keyword)
            if score is not None:
                results.append((n, score))
                results.sort(key=lambda x: x[1], reverse=True)
                return results



# --- 异步自动刷新版本 ---
class AsyncAutoRefreshDataManager(AsyncDataManager):
    def __init__(self, db_loader: Callable[[], Awaitable[Iterable[str]]], interval_seconds: int = 300):
        super().__init__(db_loader)
        self._interval = interval_seconds
        self._refresh_task: Task | None = None
        self._stop = False

    async def _auto_refresh_loop(self):
        while not self._stop:
            try:
                await self.reload()
            except Exception as e:
                print("[AsyncAutoRefresh] Error during reload:", e)
            await sleep(self._interval)


    async def start_auto_refresh(self):
        if self._refresh_task is None:
            self._stop = False
            self._refresh_task = create_task(self._auto_refresh_loop())

    async def stop_auto_refresh(self):
        self._stop = True
        if self._refresh_task:
            await self._refresh_task
        self._refresh_task = None