"""母题实体 — Motif, SubMotif, Variant"""

from dataclasses import dataclass, field

from src.models.types import Series


@dataclass
class Motif:
    """母题（Motif）—— 叙事中反复出现的主题元素"""
    title: str
    description: str
    weight: int = 5
    evidence: list[str] = field(default_factory=list)

    def __post_init__(self):
        assert 1 <= self.weight <= 10, f"weight 必须在 1-10 之间，实际为 {self.weight}"


@dataclass
class SubMotif:
    """子母题 —— 同一母题下的不同变体类型"""
    parent_title: str
    name: str
    variant_descriptions: list[str] = field(default_factory=list)


@dataclass
class Variant:
    """变体 —— 同一母题在不同作品/场景中的不同表现"""
    motif: str  # TODO: 改为 Motif 引用（待 Gallery 聚合完善后）
    series: Series
    scene: str
    description: str
