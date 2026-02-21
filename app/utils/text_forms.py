# app/utils/text_forms.py
"""
文本多形式转换：拼音、罗马音、假名互转、简繁转换
"""
import re
from functools import lru_cache
from pypinyin import lazy_pinyin, Style
import pykakasi

_kks = None

def _get_kakasi():
    global _kks
    if _kks is None:
        _kks = pykakasi.kakasi()
    return _kks

try:
    from opencc import OpenCC
    _s2t = OpenCC('s2t')
    _t2s = OpenCC('t2s')
    HAS_OPENCC = True
except ImportError:
    HAS_OPENCC = False

_KATA_TO_HIRA = str.maketrans(
    'ァアィイゥウェエォオカガキギクグケゲコゴサザシジスズセゼソゾ'
    'タダチヂッツヅテデトドナニヌネノハバパヒビピフブプヘベペホボポ'
    'マミムメモャヤュユョヨラリルレロワヲンヴー',
    'ぁあぃいぅうぇえぉおかがきぎくぐけげこごさざしじすずせぜそぞ'
    'ただちぢっつづてでとどなにぬねのはばぱひびぴふぶぷへべぺほぼぽ'
    'まみむめもゃやゅゆょよらりるれろわをんゔー'
)

_HIRA_TO_KATA = str.maketrans(
    'ぁあぃいぅうぇえぉおかがきぎくぐけげこごさざしじすずせぜそぞ'
    'ただちぢっつづてでとどなにぬねのはばぱひびぴふぶぷへべぺほぼぽ'
    'まみむめもゃやゅゆょよらりるれろわをんゔー',
    'ァアィイゥウェエォオカガキギクグケゲコゴサザシジスズセゼソゾ'
    'タダチヂッツヅテデトドナニヌネノハバパヒビピフブプヘベペホボポ'
    'マミムメモャヤュユョヨラリルレロワヲンヴー'
)

_FULL_TO_HALF = str.maketrans(
    'ａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ０１２３４５６７８９',
    'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
)

_CJK_PATTERN = re.compile(r'[\u4e00-\u9fff]')
_KANA_PATTERN = re.compile(r'[\u3040-\u309f\u30a0-\u30ff]')
_CLEAN_PATTERN = re.compile(r'[\s\-_＿·・×/\\【】\[\]「」『』《》\(\)（）"\']+')


def normalize_text(text: str) -> str:
    if not text:
        return ""
    return _CLEAN_PATTERN.sub('', text.translate(_FULL_TO_HALF).lower())

def kata_to_hira(text: str) -> str:
    return text.translate(_KATA_TO_HIRA)

def hira_to_kata(text: str) -> str:
    return text.translate(_HIRA_TO_KATA)

def extract_kanji(text: str) -> str:
    return ''.join(_CJK_PATTERN.findall(text))

def extract_kana(text: str) -> str:
    return ''.join(_KANA_PATTERN.findall(text))

@lru_cache(maxsize=50000)
def to_simplified(text: str) -> str:
    if not HAS_OPENCC or not text:
        return text
    return _t2s.convert(text)

@lru_cache(maxsize=50000)
def to_traditional(text: str) -> str:
    if not HAS_OPENCC or not text:
        return text
    return _s2t.convert(text)

@lru_cache(maxsize=50000)
def chinese_to_pinyin(text: str) -> str:
    return ''.join(lazy_pinyin(text))

@lru_cache(maxsize=50000)
def chinese_to_pinyin_initials(text: str) -> str:
    return ''.join(lazy_pinyin(text, style=Style.FIRST_LETTER))

@lru_cache(maxsize=50000)
def japanese_to_romaji(text: str) -> str:
    return ''.join(item['hepburn'] for item in _get_kakasi().convert(text))

@lru_cache(maxsize=50000)
def japanese_to_hiragana(text: str) -> str:
    return ''.join(item['hira'] for item in _get_kakasi().convert(text))


@lru_cache(maxsize=100000)
def generate_all_forms(text: str) -> frozenset[str]:
    """为名称生成所有可搜索变体"""
    if not text:
        return frozenset()
    
    forms = {text, text.lower()}
    text_normalized = normalize_text(text)
    if text_normalized:
        forms.add(text_normalized)
    
    kanji = extract_kanji(text)
    kana = extract_kana(text)
    has_kana = bool(kana) or _KANA_PATTERN.search(text)
    
    if kanji:
        forms.add(kanji)
        pinyin = chinese_to_pinyin(kanji)
        if pinyin:
            forms.add(pinyin)
        initials = chinese_to_pinyin_initials(kanji)
        if len(initials) >= 2:
            forms.add(initials)
        for variant in (to_simplified(kanji), to_traditional(kanji)):
            if variant and variant != kanji:
                forms.add(variant)
                forms.add(normalize_text(variant))
        ja_romaji = japanese_to_romaji(kanji)
        if ja_romaji:
            forms.add(ja_romaji.lower())
    
    if has_kana:
        romaji = japanese_to_romaji(text)
        if romaji:
            forms.add(romaji.lower())
        hiragana = japanese_to_hiragana(text)
        if hiragana:
            forms.add(hiragana)
        hira = kata_to_hira(text)
        kata = hira_to_kata(text)
        if hira != text:
            forms.add(hira)
        if kata != text:
            forms.add(kata)
    
    alpha_only = ''.join(re.findall(r'[a-zA-Z]+', text)).lower()
    if alpha_only and len(alpha_only) >= 2:
        forms.add(alpha_only)
    
    return frozenset(f for f in forms if f and len(f) >= 1)


def generate_search_variants(keyword: str) -> set[str]:
    """为搜索词生成变体（无翻译）"""
    variants = set()
    keyword_normalized = normalize_text(keyword)
    
    variants.add(keyword)
    variants.add(keyword.lower())
    if keyword_normalized:
        variants.add(keyword_normalized)
    
    kanji = extract_kanji(keyword)
    kana = extract_kana(keyword)
    has_kana = bool(kana) or _KANA_PATTERN.search(keyword)
    
    if kanji:
        variants.add(chinese_to_pinyin(kanji))
        initials = chinese_to_pinyin_initials(kanji)
        if len(initials) >= 2:
            variants.add(initials)
        variants.add(to_simplified(kanji))
        variants.add(to_traditional(kanji))
        variants.add(japanese_to_romaji(kanji).lower())
    
    if has_kana:
        variants.add(japanese_to_romaji(keyword).lower())
        variants.add(kata_to_hira(keyword))
        variants.add(hira_to_kata(keyword))
    
    return {v for v in variants if v}
