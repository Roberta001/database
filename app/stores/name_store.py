from asyncio import Lock
from typing import Iterable

class AsyncNameStore:
    _names: set[str]
    _lock: Lock
    
    def __init__(self):
        self._names = set()
        self._lock = Lock()
        
    async def load(self, names: Iterable[str]) -> None:
        async with self._lock:
            self._names = set(names)
            
    async def add(self, name: str) -> None:
        async with self._lock:
            self._names.add(name)
            
    async def remove(self, name: str) -> None:
        async with self._lock:
            self._names.discard(name)
            
    async def all(self) -> set[str]:
        async with self._lock:
            return self._names.copy()

            
