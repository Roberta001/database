from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models import TABLE_MAP, song_load_full
from app.stores.names_store import async_names_store
from app.utils.search import accurate_search

from typing import Literal

async def normal_search(
    type: Literal['song', 'video', 'producer', 'vocalist', 'synthesizer', 'uploader'] ,
    keyword: str,
    session: AsyncSession
):
    name_attr = 'title' if type == 'video' else 'name'

    all_names = await async_names_store.get(type)
    matches = accurate_search(keyword, all_names)
    accuracy_map = {x.word: x.accuracy for x in matches}
    names = [x.word for x in matches]
    table = TABLE_MAP[type]
    
    if type == 'song':
        stmt = (
            select(table)
            .where(table.name.in_(names))
            .options(*song_load_full)
        )
    elif type == 'video':
        stmt = (
            select(table)
            .where(table.title.in_(names))
            .options(
                selectinload(table.uploader),
                selectinload(table.song)
            )
        )
    else:
        stmt = (
            select(table)
            .where(table.name.in_(names))
        )

    result = await session.execute(stmt)
    
    data = result.scalars().all()
    return sorted(data, key=lambda x: accuracy_map[getattr(x, name_attr)], reverse=True)
