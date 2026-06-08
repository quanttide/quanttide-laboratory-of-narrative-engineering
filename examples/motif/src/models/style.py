"""风格诊断实体 — StyleDimension, StyleReview, FixGroup"""

from dataclasses import dataclass, field
from typing import Optional

from src.models.types import Confidence


@dataclass(frozen=True)
class StyleDimension:
    """风格评价维度（值对象）"""
    title: str
    description: str = ""
    score: int = 5
    evidence: list[str] = field(default_factory=list)
    note: str = ""

    def __post_init__(self):
        if not 1 <= self.score <= 10:
            raise ValueError(f"score 必须在 1-10 之间，实际为 {self.score}")

    def is_weak(self, threshold: int = 7) -> bool:
        return self.score <= threshold


@dataclass(frozen=True)
class StyleMotifLink:
    """风格-母题关联诊断（值对象）"""
    weak_dimension: str
    related_missing_motif: Optional[str] = None
    confidence: Confidence = "medium"
    hypothesis: str = ""

    def __post_init__(self):
        valid = ("high", "medium", "low")
        if self.confidence not in valid:
            raise ValueError(f"confidence 必须为 {valid}，实际为 {self.confidence}")


@dataclass
class StyleReview:
    """风格评审结果（Article 聚合的一部分，实体）"""
    dimension_scores: list[StyleDimension] = field(default_factory=list)
    diagnoses: list[StyleMotifLink] = field(default_factory=list)


@dataclass(frozen=True)
class FixGroup:
    """三组改法对比（值对象）"""
    combined: str = ""
    style_only: str = ""
    motif_only: str = ""
