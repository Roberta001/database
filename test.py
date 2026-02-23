# 检查数据库里有没有名字就是 "初音" 的
from app.utils.text_forms import generate_all_forms


# 打印 exact_index 里 "初音" 这个 key 有哪些实体
async def debug_search():
    idx = await data_store.get("search_index_vocalist")

    # 检查精确匹配
    if "初音" in idx["exact_index"]:
        print("exact_index['初音']:", idx["exact_index"]["初音"][:5])

    # 检查前缀索引
    if "初音" in idx["prefix_index"]:
        print("prefix_index['初音']:", idx["prefix_index"]["初音"][:5])
