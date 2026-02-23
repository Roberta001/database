# app/routers/test.py
from fastapi import APIRouter, Query, Depends
from app.utils.filename import extract_file_name
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import values, text, column, update, String, Integer
from app.session import get_async_session
from app.models import Video
import pandas as pd


router = APIRouter(prefix="/test", tags=["test"])


@router.get("/extract_filename")
def extract_filename(filename: str = Query(...)):
    return extract_file_name(filename)


@router.get("/init_streak")
async def init_streak(session: AsyncSession = Depends(get_async_session)):
    all_data = pd.read_excel(
        "收录曲目.xlsx", usecols=["bvid", "streak"], dtype={"bvid": str, "streak": int}
    )
    print(len(all_data))
    for start in range(0, len(all_data), 200):
        end = start + 200
        data = all_data.iloc[start:end]
        rows = data.to_dict(orient="records")

        # 用 SQLAlchemy 构造 values(...) 表
        v = (
            values(column("bvid", String), column("streak", Integer))  # 虚拟值表字段
            .data([(r["bvid"], r["streak"]) for r in rows])
            .alias("v")
        )

        # SQLAlchemy 的 UPDATE ... FROM 写法
        stmt = update(Video).where(Video.bvid == v.c.bvid).values(streak=v.c.streak)

        await session.execute(stmt)
        await session.commit()
