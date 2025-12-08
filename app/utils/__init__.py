import pandas  as pd
from fastapi import HTTPException

def validate_excel(df: pd.DataFrame):
    df['__row__'] = df.index + 2
    errors: list[str] = []
    
    if 'title' in df.columns:
        df['title'] = df['title'].fillna('')
    for column_name in df.columns:
        invalid_title = df[df[column_name].isna()]
        if not invalid_title.empty:
            for _, row in invalid_title.iterrows():
                message = f"第 {row['__row__']} 行的 {column_name} 为空"
                errors.append(message)
    
    return errors
        
def read_excel(filepath: str) -> pd.DataFrame:
    """
    读取是标准的数据文件或排名文件。对常用字段进行预处理。
    """
    df = pd.read_excel(filepath, dtype={
        'title': str,
        'name': str, 
        'type':str, 
        'author':str, 
        'synthesizer': str,
        'vocal': str,
        'uploader': str
    })
    df['pubdate'] = pd.to_datetime(
        df['pubdate'],
        format='%Y-%m-%d %H:%M:%S',   # 如果格式固定，指定 format 会更快
        errors='coerce'              # 格式不对的会变成 NaT，便于后续发现与处理
    )
    df['title'] = df['title'].fillna('')      # 如果标题为空，那就空字符串
    
    return df

    
def modify_text(name: str):
    """
    把文本转换为便于搜索的格式
    """
    return name.lower()

    
def ensure_columns(df: pd.DataFrame, columns: list):
    """
    确保 DataFrame 中存在指定列，如果不存在就创建，默认值为 None。
    
    Parameters:
        df (pd.DataFrame): 要处理的 DataFrame
        columns (list): 需要确保存在的列名列表
    
    Returns:
        pd.DataFrame: 修改后的 DataFrame
    """
    for col in columns:
        if col not in df.columns:
            df[col] = None
    return df

def normalize_nullable_int_columns(df: pd.DataFrame, columns: list):
    """
    将指定列转换为可空整型 Int32，并把 NaN 处理为 None。
    
    Args:
        df: DataFrame
        columns: 要处理的列名列表
    """
    for col in columns:
        # 列不存在则先创建
        if col not in df.columns:
            df[col] = pd.Series([None] * len(df), dtype="Int32")
            continue
        
        # 转换为可空整型
        df[col] = df[col].astype("Int32") 
        
        # 把空值变成 pandas 可识别的 NA
        df[col] = df[col].replace({pd.NA: None})

    return df

def normalize_nullable_str_columns(df: pd.DataFrame, columns: list):
    """
    把指定列的 NaN 处理为 None。
    
    Args:
        df: DataFrame
        columns: 要处理的列名列表
    """
    for col in columns:
        # 列不存在则先创建
        if col not in df.columns:
            df[col] = pd.Series([None] * len(df), dtype="string")
            continue
        
        # 先把空值变成 pandas 可识别的 NA
        df[col] = df[col].replace({pd.NA: None})

    return df
