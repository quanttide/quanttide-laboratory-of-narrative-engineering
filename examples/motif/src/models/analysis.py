"""缝隙分析与改进建议 — Gap, Suggestion"""

from dataclasses import dataclass, field
from typing import Optional

from src.models.types import Direction, GapType
from src.models.motif import Motif


@dataclass
class GapItem:
    """单个母题的缝隙状态"""
    title: str
    target_weight: int
    extracted_weight: Optional[int] = None
    description: str = ""
    matched_via: Optional[str] = None


@dataclass
class GapAttribution:
    """缝隙归因"""
    gap_types: Optional[list[GapType]] = None  # None = 未归因, [] = 已分析但无已知类型
    alternative_motif: Optional[str] = None
    reasoning: str = ""


@dataclass
class GapReport:
    """缝隙分析报告（Article 聚合的一部分）"""
    covered: list[GapItem] = field(default_factory=list)
    missing: list[GapItem] = field(default_factory=list)
    weak: list[GapItem] = field(default_factory=list)
    extracted_motifs: list[Motif] = field(default_factory=list)


@dataclass
class Suggestion:
    """改进建议（6 方向）"""
    direction: Direction
    text: str
    paragraph_ref: str = ""
    reverse_risk: Optional[int] = None


@dataclass
class SuggestionDirection:
    """改进方向定义"""
    id: Direction
    name: str
    desc: str
    trigger: str


DIRECTIONS: list[SuggestionDirection] = [
    SuggestionDirection("amplify",   "增强", "强化已存在但偏弱的母题",               "母题已被检测到但 weight 偏低"),
    SuggestionDirection("introduce", "引入", "添加一个完全缺失的母题",               "母题完全缺失"),
    SuggestionDirection("borrow",    "借用", "从跨作品母题镜像或同系列其他场景借用变体", "素材库有可用变体"),
    SuggestionDirection("transform", "转化", "将现有场景元素改造成母题载体",          "场景中已存在可承载母题的元素"),
    SuggestionDirection("restrain",  "克制", "建议不做某事，保持克制",               "weight ≤ 6 或已有 2+ 高 weight 母题"),
    SuggestionDirection("reverse",   "反向", "有意违抗母题以制造张力",               "无限制，需标风险"),
]

DIRECTION_MAP: dict[Direction, SuggestionDirection] = {d.id: d for d in DIRECTIONS}
