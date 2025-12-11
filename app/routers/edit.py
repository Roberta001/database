from fastapi import APIRouter, Body, Depends, HTTPException

from sqlalchemy.ext.asyncio import AsyncSession
from app.models import TABLE_MAP, REL_MAP, Video
from app.session import get_async_session
from app.crud.edit import check_artist
from app.schemas.edit import ConfirmRequest
from app.utils.task import task_manager

router = APIRouter(prefix='/edit', tags=['edit'])

@router.post("/artist/check")
async def edit_artist(
    type: str = Body(),
    id: int = Body(),
    name: str = Body(),
    session: AsyncSession = Depends(get_async_session)
):
    return await check_artist(type, id, name, session)

@router.post("/artist/confirm")
async def confirm_edit_artist(
    request: ConfirmRequest = Body(),
    session: AsyncSession = Depends(get_async_session)
):
    token = request.task_id
    
    task = task_manager.get_task(token)
    
    if not task:
        return HTTPException(status_code=404, detail="任务不存在")
    
    return await task