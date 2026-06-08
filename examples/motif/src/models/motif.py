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
        if not 1 <= self.weight <= 10:
            raise ValueError(f"weight 必须在 1-10 之间，实际为 {self.weight}")

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Motif):
            return NotImplemented
        return self.title == other.title

    def __hash__(self) -> int:
        return hash(self.title)

    def is_strong(self) -> bool:
        return self.weight >= 7

    def is_weak(self) -> bool:
        return self.weight <= 3

    def matches_title(self, other: str) -> bool:
        return self.title == other or other in self.title or self.title in other

    def merge(self, other: "Motif") -> "Motif":
        return Motif(
            title=self.title,
            description=self.description or other.description,
            weight=max(self.weight, other.weight),
            evidence=list(set(self.evidence + other.evidence)),
        )


@dataclass(frozen=True)
class SubMotif:
    """子母题 —— 同一母题下的不同变体类型"""
    parent_title: str
    name: str
    variant_descriptions: list[str] = field(default_factory=list)


@dataclass
class Variant:
    """变体 —— 同一母题在不同作品/场景中的不同表现"""
    motif: str
    series: Series
    scene: str
    description: str

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Variant):
            return NotImplemented
        return (self.motif, self.series, self.scene) == (other.motif, other.series, other.scene)

    def __hash__(self) -> int:
        return hash((self.motif, self.series, self.scene))

    def series_name(self) -> str:
        return "都市言情" if self.series == "urban" else "校园言情"
