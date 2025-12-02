from fastapi import APIRouter, Depends, Query, Body, HTTPException

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, and_
from sqlalchemy.dialects.postgresql import insert

from app.session import get_async_session
from app.models import Producer, Song

router = APIRouter(prefix="/producer", tags=["producer"])
