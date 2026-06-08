"""文章实体 — Article, SceneTemplate, ArticleAnalysis"""

import dataclasses
from dataclasses import dataclass, field
from typing import Optional

from src.models.types import Series, ArticleType, SceneType
from src.models.motif import Motif
from src.models.analysis import GapReport, Suggestion
from src.models.style import StyleReview, FixGroup


@dataclass
class Article:
    """文章 / 场景 —— 被分析的基本文本单位"""
    id: str
    series: Series
    name: str
    path: str
    type: ArticleType = "初稿"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Article):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)


@dataclass
class SceneTemplate:
    """场景模板 —— 用于生成测试场景"""
    id: str
    name: str
    type: SceneType
    desc: str

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SceneTemplate):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)


@dataclass
class ArticleAnalysis:
    """一篇文章的完整分析结果（聚合根）"""
    article: Article
    motifs: list[Motif] = field(default_factory=list)
    gap_report: Optional[GapReport] = None
    suggestions: dict[str, list[Suggestion]] = field(default_factory=dict)
    style_review: Optional[StyleReview] = None
    fixes: dict[str, FixGroup] = field(default_factory=dict)

    def add_motif(self, motif: Motif) -> None:
        self.motifs.append(motif)

    def set_gap_report(self, report: GapReport) -> None:
        self.gap_report = report

    def add_suggestion(self, motif_title: str, suggestion: Suggestion) -> None:
        self.suggestions.setdefault(motif_title, []).append(suggestion)

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)
