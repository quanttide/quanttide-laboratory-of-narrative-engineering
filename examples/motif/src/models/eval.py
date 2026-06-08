"""评估值对象 — EvaluationScore, MatchItem, CoverageReport, MotifSimilarityPair"""

from dataclasses import dataclass, field

from src.models.types import PairType


@dataclass
class MatchItem:
    """母题匹配对"""
    extracted: str
    gt: str
    similarity: float

    def __post_init__(self):
        assert 0.0 <= self.similarity <= 1.0, f"similarity 必须在 0-1 之间，实际为 {self.similarity}"


@dataclass
class CoverageReport:
    """覆盖率报告"""
    extracted_count: int = 0
    matched_count: int = 0
    coverage: float = 0.0
    matches: list[MatchItem] = field(default_factory=list)

    def __post_init__(self):
        assert 0.0 <= self.coverage <= 1.0, f"coverage 必须在 0-1 之间，实际为 {self.coverage}"


@dataclass
class EvaluationScore:
    """建议/改法的多维评分"""
    feasibility: int = 3
    motif_fit: int = 3
    naturalness: int = 3
    actionable: int = 3

    def __post_init__(self):
        for name, val in [("feasibility", self.feasibility), ("motif_fit", self.motif_fit),
                          ("naturalness", self.naturalness), ("actionable", self.actionable)]:
            assert 1 <= val <= 5, f"{name} 必须在 1-5 之间，实际为 {val}"


@dataclass
class MotifSimilarityPair:
    """母题相似度对"""
    pair_a: str
    pair_b: str
    same_motif: bool = False
    same_gt_motif: bool = False
    similarity: float = 0.0
    shared_pattern: str = ""
    reasoning: str = ""
    pair_type: PairType = "cross-series_diff-motif"
