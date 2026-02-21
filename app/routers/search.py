# app/routers/search.py
from fastapi import APIRouter, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.session import get_async_session
from app.crud.search import normal_search, suggest_search
from typing import Literal

router = APIRouter(prefix='/search', tags=['search'])


@router.get("/suggest")
async def suggest(
    q: str = Query(..., min_length=1, max_length=50),
    types: str = Query("song,vocalist,producer"),
    limit: int = Query(10, ge=1, le=20)
):
    type_list = [t.strip() for t in types.split(',') if t.strip()]
    valid_types = ['song', 'video', 'producer', 'vocalist', 'synthesizer', 'uploader']
    type_list = [t for t in type_list if t in valid_types]
    return await suggest_search(q, type_list or None, limit)

@router.get("/{type}")
async def search(
    type: Literal['song', 'video', 'producer', 'vocalist', 'synthesizer', 'uploader'],
    keyword: str = Query(..., min_length=1, max_length=100),
    includeEmpty: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_async_session)
):
    return await normal_search(type, keyword, includeEmpty, page, page_size, session)
