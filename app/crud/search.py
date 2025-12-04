from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models import Song, Video, TABLE_MAP, song_load_full
from app.stores.async_store import AsyncStore, SessionLocal
from app.utils.search import accurate_search
from app.utils import modify_text
from app.stores import data_store

from typing import Literal

def create_load_modified_name_id_map_factory(table_name: str):
    async def load_modified_name_id_map():
        """
        这个函数的目的在于加载一个“标准化的名字”到id的映射表。
        """
        table = TABLE_MAP[table_name]
    
        id_col = 'bvid' if table_name == 'video' else 'id'
        name_col = 'title' if table_name == 'video' else 'name'
        
        stmt = select(getattr(table, id_col), getattr(table, name_col))
        
        async with SessionLocal() as session:
            result = await session.execute(stmt)
            rows = result.all()

        # 有潜在问题，因为标准化后的名称可能会重复，所以改成 name -> id[] 会更好，待改
        names_map: dict[str, list] = {}
        
        for id_value, name in rows:
            normalized = modify_text(name)
            names_map.setdefault(normalized, []).append(id_value)

        return names_map
            
    return load_modified_name_id_map



async def normal_search(
    table_name: Literal['song', 'video', 'producer', 'vocalist', 'synthesizer', 'uploader'] ,
    keyword: str,
    session: AsyncSession
):
    table = TABLE_MAP[table_name]
    id_attr = 'bvid' if table_name == 'video' else 'id'

    if not data_store.has(f"modified_{table_name}_name_id_map"):
        await data_store.add(f"modified_{table_name}_name_id_map", create_load_modified_name_id_map_factory(table_name))
    names_map = await data_store.get(f"modified_{table_name}_name_id_map")

    names_match = accurate_search(modify_text(keyword), list(names_map.keys()))
    id_accuracy_map = {}
    for match in names_match:
        if match.text not in names_map:
            continue
        for id_value in names_map[match.text]:
            id_accuracy_map[id_value] = match.accuracy
    ids = list(id_accuracy_map.keys())
    
    if table == Song:
        stmt = (
            select(Song)
            .where(Song.id.in_(ids))
            .options(*song_load_full)
        )
    elif table == Video:
        stmt = (
            select(Video)
            .where(Video.bvid.in_(ids))
            .options(
                selectinload(Video.uploader),
                selectinload(Video.song)
            )
        )
    else:
        stmt = (
            select(table)
            .where(table.id.in_(ids))
        )

    result = await session.execute(stmt)
    data = result.scalars().all()
    
    return sorted(
        data, 
        key=lambda x: id_accuracy_map[getattr(x, id_attr)], 
        reverse=True
    )
