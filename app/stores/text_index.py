# app/stores/text_index.py
from dataclasses import dataclass
from typing import Any
from collections import defaultdict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.session import engine
from app.models import Song, Video, Producer, Vocalist, Synthesizer, Uploader
from app.utils.text_forms import (
    generate_all_forms,
    generate_search_variants,
    normalize_text,
)

SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

TABLE_CONFIG = {
    "song": {"model": Song, "id_col": "id", "name_col": "name"},
    "video": {"model": Video, "id_col": "bvid", "name_col": "title"},
    "producer": {"model": Producer, "id_col": "id", "name_col": "name"},
    "vocalist": {"model": Vocalist, "id_col": "id", "name_col": "name"},
    "synthesizer": {"model": Synthesizer, "id_col": "id", "name_col": "name"},
    "uploader": {"model": Uploader, "id_col": "id", "name_col": "name"},
}


@dataclass
class TextSearchResult:
    entity_id: Any
    name: str
    score: float
    match_type: str


class TextSearchIndex:

    def __init__(self):
        self.form_to_ids: dict[str, dict[str, list[tuple]]] = {}
        self.id_to_name: dict[str, dict[Any, str]] = {}
        self._loaded: set[str] = set()

    async def build_all(self):
        for table_name in TABLE_CONFIG:
            await self.build_table(table_name)

    async def build_table(self, table_name: str):
        config = TABLE_CONFIG[table_name]
        model = config["model"]
        id_col = config["id_col"]
        name_col = config["name_col"]

        async with SessionLocal() as session:
            stmt = select(getattr(model, id_col), getattr(model, name_col))
            result = await session.execute(stmt)
            rows = result.all()

        form_to_ids: dict[str, list[tuple]] = defaultdict(list)
        id_to_name: dict[Any, str] = {}

        for entity_id, name in rows:
            if not name:
                continue
            id_to_name[entity_id] = name
            for form in generate_all_forms(name):
                form_to_ids[form].append((entity_id, name))

        self.form_to_ids[table_name] = dict(form_to_ids)
        self.id_to_name[table_name] = id_to_name
        self._loaded.add(table_name)

        print(
            f"[TextIndex] {table_name}: {len(id_to_name)} items, {len(form_to_ids)} forms"
        )

    def search(
        self, table_name: str, keyword: str, limit: int = 200
    ) -> list[TextSearchResult]:
        if table_name not in self._loaded:
            return []

        form_to_ids = self.form_to_ids[table_name]
        search_variants = generate_search_variants(keyword)
        keyword_normalized = normalize_text(keyword)

        matches: dict[Any, tuple[float, str, str]] = {}

        for form, items in form_to_ids.items():
            for entity_id, name in items:
                score = 0.0
                match_type = ""

                if form in search_variants:
                    if form == keyword.lower() or form == keyword_normalized:
                        score, match_type = 100.0, "exact"
                    else:
                        score, match_type = 90.0, "form_exact"
                elif any(form.startswith(sv) for sv in search_variants if len(sv) >= 2):
                    ratio = max(
                        len(sv) / len(form)
                        for sv in search_variants
                        if form.startswith(sv) and len(sv) >= 2
                    )
                    score, match_type = 70.0 + ratio * 15, "prefix"
                elif any(sv in form for sv in search_variants if len(sv) >= 2):
                    ratio = max(
                        len(sv) / len(form)
                        for sv in search_variants
                        if sv in form and len(sv) >= 2
                    )
                    score, match_type = 50.0 + ratio * 15, "contains"
                elif any(form in sv for sv in search_variants if len(form) >= 2):
                    score, match_type = 40.0, "contained"

                if score > 0 and (
                    entity_id not in matches or score > matches[entity_id][0]
                ):
                    matches[entity_id] = (score, name, match_type)

        sorted_results = sorted(matches.items(), key=lambda x: -x[1][0])[:limit]

        return [
            TextSearchResult(entity_id=eid, name=name, score=score, match_type=mt)
            for eid, (score, name, mt) in sorted_results
        ]

    def is_loaded(self, table_name: str) -> bool:
        return table_name in self._loaded


text_index = TextSearchIndex()
