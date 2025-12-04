from dataclasses import dataclass
from typing import Iterable

@dataclass
class SearchMatch:
    word: str
    accuracy: int


def accurate_search(keyword: str, names: Iterable[str]) -> list[SearchMatch]:
    words = list(filter(lambda x: keyword in x, names))
    return list(map(lambda x: SearchMatch(x, 1), words))

