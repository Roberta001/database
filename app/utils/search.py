from dataclasses import dataclass
from typing import Iterable

@dataclass
class SearchMatch:
    text: str
    accuracy: int


def accurate_search(keyword: str, names: Iterable[str]) -> tuple[SearchMatch, ...]:
    words = list(filter(lambda x: keyword in x, names))
    return tuple(map(lambda x: SearchMatch(x, 1), words))

