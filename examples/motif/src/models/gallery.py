"""知识库实体 — MotifProfile, Gallery"""

from dataclasses import dataclass, field

from src.models.types import Series
from src.models.motif import Motif
from src.models.style import StyleDimension


@dataclass
class MotifProfile:
    """系列母题配置"""
    shared: list[Motif] = field(default_factory=list)
    urban: list[Motif] = field(default_factory=list)
    campus: list[Motif] = field(default_factory=list)

    def for_series(self, series: Series) -> list[Motif]:
        return self.shared + (self.urban if series == "urban" else self.campus)


@dataclass
class Gallery:
    """知识库聚合根 — motif.yaml + style.yaml 的统一接口"""
    motifs: MotifProfile = field(default_factory=MotifProfile)
    style_dimensions: list[StyleDimension] = field(default_factory=list)
