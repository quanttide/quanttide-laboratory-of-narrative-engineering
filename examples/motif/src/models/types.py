"""类型别名 — 领域模型共享的 Literal 类型 + Enum 常量"""

from enum import Enum
from typing import Literal

# ─── Literal 类型别名（类型检查用）───

Series = Literal["urban", "campus"]
ArticleType = Literal["初稿", "成稿", "盲测初稿"]
SceneType = Literal["静态室内", "动态室外", "动态室内", "任意"]
Direction = Literal["amplify", "introduce", "borrow", "transform", "restrain", "reverse"]
GapType = Literal["scene_incompatible", "alternative_used", "genuine_miss"]
Confidence = Literal["high", "medium", "low"]
PairType = Literal["cross-series_same-motif", "cross-series_diff-motif", "intra-series_diff-motif"]

# ─── 运行时 Enum ───

class SeriesEnum(str, Enum):
    URBAN = "urban"
    CAMPUS = "campus"

    def display_name(self) -> str:
        return "都市言情" if self == SeriesEnum.URBAN else "校园言情"


# ─── 语义常量 ───

SIMILARITY_CUTOFF: float = 0.7
"""语义相似度阈值：高于此值认为两个母题描述匹配"""
