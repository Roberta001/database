# app/utils/similarity.py
"""
相似度计算：编辑距离、杰卡德相似度
"""
import re


def build_ngrams(text: str, n: int = 2) -> set[str]:
    if len(text) < n:
        return {text} if text else set()
    return {text[i : i + n] for i in range(len(text) - n + 1)}


def has_cjk(text: str) -> bool:
    """检查是否包含中日文字符"""
    return bool(re.search(r"[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff]", text))


def is_mainly_cjk(text: str) -> bool:
    cjk_count = len(re.findall(r"[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff]", text))
    return cjk_count > len(text) * 0.3


def levenshtein_distance(s1: str, s2: str, max_dist: int = 3) -> int:
    if abs(len(s1) - len(s2)) > max_dist:
        return max_dist + 1
    if len(s1) > len(s2):
        s1, s2 = s2, s1
    prev = list(range(len(s1) + 1))
    for i, c2 in enumerate(s2, 1):
        curr = [i]
        min_val = i
        for j, c1 in enumerate(s1, 1):
            curr.append(
                min(prev[j] + 1, curr[j - 1] + 1, prev[j - 1] + (0 if c1 == c2 else 1))
            )
            min_val = min(min_val, curr[-1])
        if min_val > max_dist:
            return max_dist + 1
        prev = curr
    return prev[-1]


def jaccard_similarity(s1: str, s2: str, n: int = 2) -> float:
    if not s1 or not s2:
        return 0.0
    set1 = build_ngrams(s1, n) if len(s1) >= n and len(s2) >= n else set(s1)
    set2 = build_ngrams(s2, n) if len(s1) >= n and len(s2) >= n else set(s2)
    inter = len(set1 & set2)
    union = len(set1 | set2)
    return inter / union if union else 0.0
