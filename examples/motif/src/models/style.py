"""风格诊断实体 — StyleDimension, StyleReview, FixGroup"""

from dataclasses import dataclass, field
from typing import Optional

from src.models.types import Confidence


@dataclass
class StyleDimension:
    """风格评价维度"""
    title: str
    description: str = ""
    score: int = 5
    evidence: list[str] = field(default_factory=list)
    note: str = ""

    def __post_init__(self):
        assert 1 <= self.score <= 10, f"score 必须在 1-10 之间，实际为 {self.score}"

    def is_weak(self, threshold: int = 7) -> bool:
        return self.score <= threshold


@dataclass
class StyleMotifLink:
    """风格-母题关联诊断"""
    weak_dimension: str
    related_missing_motif: Optional[str] = None
    confidence: Confidence = "medium"
    hypothesis: str = ""

    def __post_init__(self):
        valid = ("high", "medium", "low")
        assert self.confidence in valid, f"confidence 必须为 {valid}，实际为 {self.confidence}"


@dataclass
class StyleReview:
    """风格评审结果（Article 聚合的一部分）"""
    dimension_scores: list[StyleDimension] = field(default_factory=list)
    diagnoses: list[StyleMotifLink] = field(default_factory=list)


@dataclass
class FixGroup:
    """三组改法对比"""
    combined: str = ""
    style_only: str = ""
    motif_only: str = ""
