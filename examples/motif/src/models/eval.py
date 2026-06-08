"""评估值对象 — EvaluationScore, MatchItem, CoverageReport, MotifSimilarityPair"""

from dataclasses import dataclass, field

from src.models.types import PairType


@dataclass(frozen=True)
class MatchItem:
    """母题匹配对（值对象）"""
    extracted: str
    gt: str
    similarity: float

    def __post_init__(self):
        if not 0.0 <= self.similarity <= 1.0:
            raise ValueError(f"similarity 必须在 0-1 之间，实际为 {self.similarity}")


@dataclass(frozen=True)
class CoverageReport:
    """覆盖率报告（值对象）"""
    extracted_count: int = 0
    matched_count: int = 0
    coverage: float = 0.0
    matches: list[MatchItem] = field(default_factory=list)

    def __post_init__(self):
        if not 0.0 <= self.coverage <= 1.0:
            raise ValueError(f"coverage 必须在 0-1 之间，实际为 {self.coverage}")


@dataclass(frozen=True)
class EvaluationScore:
    """建议/改法的多维评分（值对象）"""
    feasibility: int = 3
    motif_fit: int = 3
    naturalness: int = 3
    actionable: int = 3

    def __post_init__(self):
        for name, val in [("feasibility", self.feasibility), ("motif_fit", self.motif_fit),
                          ("naturalness", self.naturalness), ("actionable", self.actionable)]:
            if not 1 <= val <= 5:
                raise ValueError(f"{name} 必须在 1-5 之间，实际为 {val}")


@dataclass(frozen=True)
class MotifSimilarityPair:
    """母题相似度对（值对象）"""
    pair_a: str
    pair_b: str
    same_motif: bool = False
    same_gt_motif: bool = False
    similarity: float = 0.0
    shared_pattern: str = ""
    reasoning: str = ""
    pair_type: PairType = "cross-series_diff-motif"
