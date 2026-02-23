# app/crud/edit.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from app.models import TABLE_MAP, REL_MAP, Video
from app.utils.task import task_manager
from app.session import engine
from sqlalchemy.ext.asyncio import async_sessionmaker

SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def check_artist(type: str, id: int, name: str, session: AsyncSession):
    if type not in TABLE_MAP:
        raise ValueError("无效的artist类型")
    table = TABLE_MAP[type]
    result = await session.execute(select(table).where(table.id == id))
    artist = result.scalars().first()
    if artist is None:
        raise ValueError("未找到artist")

    result = await session.execute(select(table).where(table.name == name))
    existing_artist = result.scalars().first()
    if existing_artist:
        if existing_artist.id == artist.id:
            raise ValueError("同一artist，无效编辑")
        else:
            # 合并artist
            task_id = task_manager.add_task(merge_artist(type, id, name))
    else:
        # 改名
        task_id = task_manager.add_task(edit_artist(type, id, name))

    return {"task_id": task_id, "old_artist": artist, "new_artist": existing_artist}


async def merge_artist(type: str, id: int, name: str):
    table = TABLE_MAP[type]
    async with SessionLocal() as session:

        result = await session.execute(select(table).where(table.id == id))
        artist = result.scalars().first()
        result = await session.execute(select(table).where(table.name == name))
        existing_artist = result.scalars().first()
        if not artist:
            raise ValueError("未找到id对应的artist")
        if not existing_artist:
            raise ValueError("未找到name对应的artist")
        if type == "uploader":
            await session.execute(
                update(Video)
                .where(Video.uploader_id == artist.id)
                .values(uploader_id=existing_artist.id)
            )
            await session.execute(delete(table).where(table.id == artist.id))
        else:
            rel = REL_MAP[type]
            await session.execute(
                update(rel)
                .where(rel.c.artist_id == artist.id)
                .values(artist_id=existing_artist.id)
            )
            await session.execute(delete(table).where(table.id == artist.id))
        await session.commit()


async def edit_artist(
    type: str,
    id: int,
    name: str,
):
    async with SessionLocal() as session:
        table = TABLE_MAP[type]
        result = await session.execute(select(table).where(table.id == id))
        artist = result.scalars().first()
        if artist is None:
            raise ValueError("未找到artist")

        await session.execute(
            update(table).where(table.id == artist.id).values(name=name)
        )

        await session.commit()
