from app.stores.data_manager import AsyncAutoRefreshDataManager
from typing import Dict, Iterable
from app.models import TABLE_MAP
from app.crud.select import get_names
from app.session import engine
from sqlalchemy.ext.asyncio import async_sessionmaker
import asyncio

SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

class AsyncNamesStore:
    def __init__(self, names: Iterable[str]):
        self._managers_map: Dict[str, AsyncAutoRefreshDataManager] = {}
        self._lock = asyncio.Lock()  # 防止并发重复创建 manager

    async def _create_manager_if_not_exists(self, name: str):
        async with self._lock:
            # 双重检查，防止并发重复创建
            manager = self._managers_map.get(name)
            if manager is None:
                async def get_names_task():
                    async with SessionLocal() as session:
                        return await get_names(name, session)

                manager = AsyncAutoRefreshDataManager(get_names_task)
                self._managers_map[name] = manager

                await manager.load_from_db()
                await manager.start_auto_refresh()
                
            return manager

    async def get(self, name: str) -> set[str]:
        manager = self._managers_map.get(name)
        if manager is None:
            manager = await self._create_manager_if_not_exists(name)

        # 这里最好使用同步方法，除非内部有锁
        return await manager.all_names()

        
async_names_store = AsyncNamesStore(TABLE_MAP.keys())