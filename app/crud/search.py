# app/crud/search.py
from dataclasses import dataclass
from typing import Literal, Any
from collections import defaultdict

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, exists
from sqlalchemy.orm import selectinload

from app.models import Song, Video, Uploader, Producer, Vocalist, Synthesizer
from app.models import TABLE_MAP, REL_MAP, song_load_full
from app.stores.async_store import SessionLocal
from app.stores import data_store
from app.utils.text_forms import (
    generate_all_forms, generate_search_variants, normalize_text,
    chinese_to_pinyin_initials, extract_kanji
)
from app.utils.similarity import is_mainly_cjk, levenshtein_distance, build_ngrams


TABLE_CONFIG = {
    'song': {'model': Song, 'id_col': 'id', 'name_col': 'name'},
    'video': {'model': Video, 'id_col': 'bvid', 'name_col': 'title'},
    'producer': {'model': Producer, 'id_col': 'id', 'name_col': 'name'},
    'vocalist': {'model': Vocalist, 'id_col': 'id', 'name_col': 'name'},
    'synthesizer': {'model': Synthesizer, 'id_col': 'id', 'name_col': 'name'},
    'uploader': {'model': Uploader, 'id_col': 'id', 'name_col': 'name'},
}


@dataclass
class SearchMatch:
    entity_id: Any
    name: str
    score: float
    match_type: str


def create_search_index_factory(table_name: str):
    async def load_search_index():
        config = TABLE_CONFIG[table_name]
        model, id_col, name_col = config['model'], config['id_col'], config['name_col']
        
        print(f"[SearchIndex] Loading {table_name}...")
        
        async with SessionLocal() as session:
            result = await session.execute(select(getattr(model, id_col), getattr(model, name_col)))
            rows = result.all()
        
        exact_index: dict[str, list[tuple]] = defaultdict(list)
        prefix_index: dict[str, list[tuple]] = defaultdict(list)
        ngram_index: dict[str, list[int]] = defaultdict(list)
        fuzzy_candidates: list[tuple] = []
        id_to_name: dict[Any, str] = {}
        
        for i, (entity_id, name) in enumerate(rows):
            if not name:
                continue
            
            if i > 0 and i % 5000 == 0:
                print(f"[SearchIndex] {table_name}: {i}/{len(rows)}")
            
            id_to_name[entity_id] = name
            name_normalized = normalize_text(name)
            is_cjk = is_mainly_cjk(name)
            
            forms = generate_all_forms(name)
            
            for form in forms:
                exact_index[form].append((entity_id, name, name_normalized))
                if len(form) >= 2:
                    prefix_index[form[:2]].append((form, entity_id, name, name_normalized))
            
            # 原文加入模糊候选
            if len(name_normalized) >= 2:
                idx = len(fuzzy_candidates)
                fuzzy_candidates.append((name_normalized, entity_id, name, is_cjk))
                for gram in build_ngrams(name_normalized, 2):
                    ngram_index[gram].append(idx)
            
            # 所有英文形式也加入模糊候选
            seen = {name_normalized}
            for form in forms:
                form_lower = form.lower()
                if len(form_lower) >= 2 and form_lower not in seen:
                    seen.add(form_lower)
                    idx = len(fuzzy_candidates)
                    fuzzy_candidates.append((form_lower, entity_id, name, False))
                    for gram in build_ngrams(form_lower, 2):
                        ngram_index[gram].append(idx)
        
        print(f"[SearchIndex] {table_name}: {len(id_to_name)} items, {len(exact_index)} exact, {len(ngram_index)} ngrams")
        
        return {
            'exact_index': dict(exact_index), 
            'prefix_index': dict(prefix_index),
            'ngram_index': dict(ngram_index),
            'fuzzy_candidates': fuzzy_candidates, 
            'id_to_name': id_to_name,
        }
    
    return load_search_index


def search_in_index(exact_index, prefix_index, ngram_index, fuzzy_candidates, 
                    id_to_name, keyword: str, limit: int = 500) -> list[SearchMatch]:
    
    search_variants = generate_search_variants(keyword)
    matches = _do_search(exact_index, prefix_index, ngram_index, fuzzy_candidates, 
                         search_variants, keyword, limit)
    
    return _finalize(matches, limit)


def _do_search(exact_index, prefix_index, ngram_index, fuzzy_candidates,
               search_variants, keyword, limit, existing_matches=None) -> dict:
    
    keyword_lower = keyword.lower()
    keyword_normalized = normalize_text(keyword)
    
    matches = dict(existing_matches) if existing_matches else {}
    seen_ids = set(matches.keys())
    
    # === 阶段1: 精确匹配 ===
    for variant in search_variants:
        if variant not in exact_index:
            continue
        for eid, name, name_norm in exact_index[variant]:
            score = 100.0 if variant == keyword_lower else 90.0
            if eid not in matches or score > matches[eid][0]:
                matches[eid] = (score, name, "exact")
            seen_ids.add(eid)
    
    # === 阶段2: 前缀/包含匹配 ===
    checked_pk = set()
    for variant in search_variants:
        if len(variant) < 2:
            continue
        pk = variant[:2]
        if pk in checked_pk or pk not in prefix_index:
            continue
        checked_pk.add(pk)
        
        for form, eid, name, name_norm in prefix_index[pk]:
            if eid in seen_ids:
                continue
            
            score = 0.0
            if form.startswith(variant):
                score = 80.0
            elif variant in form:
                score = 70.0
            elif keyword_normalized in name_norm:
                score = 75.0
            
            if score > 0:
                if eid not in matches or score > matches[eid][0]:
                    matches[eid] = (score, name, "prefix")
                seen_ids.add(eid)
    
    # === 阶段3: 模糊匹配（放宽阈值） ===
    if len(keyword_normalized) >= 2:
        all_ngrams = set()
        for variant in search_variants:
            if len(variant) >= 2:
                all_ngrams.update(build_ngrams(variant.lower(), 2))
        
        if not all_ngrams:
            all_ngrams = build_ngrams(keyword_normalized, 2)
        
        candidate_hits: dict[int, int] = defaultdict(int)
        for gram in all_ngrams:
            if gram in ngram_index:
                for idx in ngram_index[gram]:
                    candidate_hits[idx] += 1
        
        # ★ 只要有任何 ngram 重叠就进入候选
        for idx, hits in candidate_hits.items():
            form, eid, name, is_cjk = fuzzy_candidates[idx]
            
            if eid in seen_ids:
                continue
            
            # 计算最小编辑距离
            best_dist = 999
            for variant in search_variants:
                if len(variant) >= 2:
                    dist = levenshtein_distance(variant.lower(), form, max_dist=5)  # ★ 放宽到5
                    best_dist = min(best_dist, dist)
            
            if best_dist <= 5:
                score = 70.0 - best_dist * 8  # d0=70, d1=62, d2=54, d3=46, d4=38, d5=30
                if eid not in matches or score > matches[eid][0]:
                    matches[eid] = (score, name, f"fuzzy_d{best_dist}")
                seen_ids.add(eid)
    
    return matches


def _finalize(matches: dict, limit: int) -> list[SearchMatch]:
    sorted_res = sorted(matches.items(), key=lambda x: (-x[1][0], x[1][1]))[:limit]
    return [SearchMatch(eid, name, score, mt) for eid, (score, name, mt) in sorted_res]


async def normal_search(
    table_name: Literal['song','video','producer','vocalist','synthesizer','uploader'],
    keyword: str, includeEmpty: bool, page: int, page_size: int, session: AsyncSession
) -> dict:
    keyword = keyword.strip()
    if not keyword:
        return {'data': [], 'total': 0}
    
    cache_key = f"search_index_{table_name}"
    if not data_store.has(cache_key):
        await data_store.add(cache_key, create_search_index_factory(table_name))
    
    idx = await data_store.get(cache_key)
    results = search_in_index(
        idx['exact_index'], idx['prefix_index'], 
        idx['ngram_index'], idx['fuzzy_candidates'],
        idx['id_to_name'], keyword
    )
    
    if not results:
        return {'data': [], 'total': 0}
    
    ids = [r.entity_id for r in results]
    total = len(ids)
    page_ids = ids[(page-1)*page_size : page*page_size]
    
    if not page_ids:
        return {'data': [], 'total': total}
    
    stmt = _build_query(TABLE_MAP[table_name], table_name, page_ids, includeEmpty)
    rows = (await session.execute(stmt)).scalars().all()
    
    id_col = TABLE_CONFIG[table_name]['id_col']
    id_to_row = {getattr(r, id_col): r for r in rows}
    
    return {'data': [id_to_row[i] for i in page_ids if i in id_to_row], 'total': total}


async def suggest_search(keyword: str, types: list[str] | None = None, limit: int = 10) -> list[dict]:
    if not keyword or not keyword.strip():
        return []
    keyword = keyword.strip()
    types = types or ['song', 'vocalist', 'producer']
    
    all_res = []
    for t in types:
        cache_key = f"search_index_{t}"
        if not data_store.has(cache_key):
            await data_store.add(cache_key, create_search_index_factory(t))
        idx = await data_store.get(cache_key)
        for r in search_in_index(
            idx['exact_index'], idx['prefix_index'], 
            idx['ngram_index'], idx['fuzzy_candidates'],
            idx['id_to_name'], keyword, limit * 3
        ):
            all_res.append({'type': t, 'id': r.entity_id, 'name': r.name, 'score': r.score})
    
    all_res.sort(key=lambda x: -x['score'])
    return all_res[:limit]


def _build_query(table, table_name: str, ids: list, include_empty: bool):
    if table_name == 'song':
        conds = [Song.id.in_(ids)]
        if not include_empty:
            conds.append(exists().where(Video.song_id == Song.id))
        return select(Song).where(*conds).options(*song_load_full)
    elif table_name == 'video':
        return select(Video).where(Video.bvid.in_(ids)).options(selectinload(Video.uploader), selectinload(Video.song))
    elif table_name == 'uploader':
        conds = [Uploader.id.in_(ids)]
        if not include_empty:
            conds.append(exists().where(Video.uploader_id == Uploader.id))
        return select(Uploader).where(*conds)
    else:
        rel = REL_MAP[table_name]
        conds = [table.id.in_(ids)]
        if not include_empty:
            conds.append(exists().where(rel.c.artist_id == table.id))
        return select(table).where(*conds)
