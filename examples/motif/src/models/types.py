"""类型别名 — 领域模型共享的 Literal 类型"""

from typing import Literal

Series = Literal["urban", "campus"]
ArticleType = Literal["初稿", "成稿", "盲测初稿"]
SceneType = Literal["静态室内", "动态室外", "动态室内", "任意"]
Direction = Literal["amplify", "introduce", "borrow", "transform", "restrain", "reverse"]
GapType = Literal["scene_incompatible", "alternative_used", "genuine_miss"]
Confidence = Literal["high", "medium", "low"]
PairType = Literal["cross-series_same-motif", "cross-series_diff-motif", "intra-series_diff-motif"]
