from fastapi import APIRouter, Query
from app.utils.filename import extract_file_name
from fastapi import Depends
from app.session import get_async_session
from app.stores.names_store import async_names_store
from typing import Literal
from sqlalchemy.ext.asyncio import AsyncSession



router = APIRouter(prefix='/test', tags=['test'])

@router.get("/extract_filename")
def extract_filename(filename: str = Query(...)):
    return extract_file_name(filename)

@router.get("/get_names")
async def get_names(
    type: Literal['song', 'video', 'producer', 'vocalist', 'synthesizer', 'uploader'] = Query(...),
    session: AsyncSession = Depends(get_async_session)
):
    return await async_names_store.get(type)