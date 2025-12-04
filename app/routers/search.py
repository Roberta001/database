from fastapi import APIRouter, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.session import get_async_session

router = APIRouter(prefix='/search', tags=['search'])

@router.get("/songs")
async def search_songs(
    keyword: str = Query(...),
    session: AsyncSession = Depends(get_async_session)
):
    return await search_songs(keyword, session)