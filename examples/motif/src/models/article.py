"""文章实体 — Article, SceneTemplate, ArticleAnalysis"""

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


@dataclass
class SceneTemplate:
    """场景模板 —— 用于生成测试场景"""
    id: str
    name: str
    type: SceneType
    desc: str


@dataclass
class ExtractedMotifResult:
    """单篇文章的母题提取结果。注：建议直接用 list[Motif]。"""
    motifs: list[Motif] = field(default_factory=list)


@dataclass
class ArticleAnalysis:
    """一篇文章的完整分析结果（聚合根）"""
    article: Article
    motifs: list[Motif] = field(default_factory=list)
    gap_report: Optional[GapReport] = None
    suggestions: dict[str, list[Suggestion]] = field(default_factory=dict)  # key = motif title
    style_review: Optional[StyleReview] = None
    fixes: dict[str, FixGroup] = field(default_factory=dict)
