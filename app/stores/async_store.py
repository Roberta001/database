from app.stores.data_manager import AsyncAutoRefreshDataManager
from typing import Dict, Iterable,  Awaitable, Callable
from app.session import engine
from sqlalchemy.ext.asyncio import async_sessionmaker
import asyncio

SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

class AsyncStore:
    """
    这是一个可以在FastAPI的整个生命周期中使用的缓存。
    通过 `add` 方法添加数据源， `get` 方法获取数据。
    """
    def __init__(self, ):
        self._managers_map: Dict[str, AsyncAutoRefreshDataManager] = {}
        self._lock = asyncio.Lock()  # 防止并发重复创建 manager
        
    

    async def _create_manager_if_not_exists(self, key: str, loader: Callable[[], Awaitable]):
        async with self._lock:
            # 双重检查，防止并发重复创建
            manager = self._managers_map.get(key)
            if manager is None:
                manager = AsyncAutoRefreshDataManager(loader)
                self._managers_map[key] = manager

                await manager.load()
                await manager.start_auto_refresh()
                
            return manager
        
    async def add(self, key: str, loader: Callable[[], Awaitable]) -> None:
        await self._create_manager_if_not_exists(key, loader)

    async def get(self, key: str):
        manager = self._managers_map.get(key)
        if manager is None:
            raise KeyError(f"{key} not exists")
        return await manager.get()

    def has(self, key: str):
        return key in self._managers_map

    async def shutdown(self):
        for manager in self._managers_map.values():
            await manager.stop_auto_refresh()

