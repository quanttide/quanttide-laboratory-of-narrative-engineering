"""领域模型实体定义 — 类型安全、约束完备、与实验代码集成"""

from dataclasses import dataclass, field
from typing import Literal, Optional

# ─── 类型别名 ───

Series = Literal["urban", "campus"]
ArticleType = Literal["初稿", "成稿", "盲测初稿"]
SceneType = Literal["静态室内", "动态室外", "动态室内", "任意"]
Direction = Literal["amplify", "introduce", "borrow", "transform", "restrain", "reverse"]
GapType = Literal["scene_incompatible", "alternative_used", "genuine_miss"]
Confidence = Literal["high", "medium", "low"]
PairType = Literal["cross-series_same-motif", "cross-series_diff-motif", "intra-series_diff-motif"]

# ─── 核心实体 ───


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
    """单篇文章的母题提取结果。
    注：建议直接用 list[Motif]，此包装已冗余。
    """
    motifs: list[Motif] = field(default_factory=list)


# ─── 缝隙分析 ───


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
class Suggestion:
    """改进建议（6 方向）"""
    direction: Direction
    text: str
    paragraph_ref: str = ""
    reverse_risk: Optional[int] = None


# ─── 风格诊断 ───


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


@dataclass
class StyleMotifLink:
    """风格-母题关联诊断"""
    weak_dimension: str
    related_missing_motif: Optional[str] = None
    confidence: Confidence = "medium"
    hypothesis: str = ""


# ─── 聚合根 ───


@dataclass
class GapReport:
    """缝隙分析报告（Article 聚合的一部分）"""
    covered: list[GapItem] = field(default_factory=list)
    missing: list[GapItem] = field(default_factory=list)
    weak: list[GapItem] = field(default_factory=list)
    extracted_motifs: list[Motif] = field(default_factory=list)


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


@dataclass
class ArticleAnalysis:
    """一篇文章的完整分析结果（聚合根）"""
    article: Article
    motifs: list[Motif] = field(default_factory=list)
    gap_report: Optional[GapReport] = None
    suggestions: dict[str, list[Suggestion]] = field(default_factory=dict)  # key = motif title
    style_review: Optional[StyleReview] = None
    fixes: dict[str, FixGroup] = field(default_factory=dict)


# ─── 值对象 ───


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


@dataclass
class SuggestionDirection:
    """改进方向定义"""
    id: Direction
    name: str
    desc: str
    trigger: str


# ─── 知识库（Gallery）───


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


# ─── 常量 ───

DIRECTIONS: list[SuggestionDirection] = [
    SuggestionDirection("amplify",   "增强", "强化已存在但偏弱的母题",               "母题已被检测到但 weight 偏低"),
    SuggestionDirection("introduce", "引入", "添加一个完全缺失的母题",               "母题完全缺失"),
    SuggestionDirection("borrow",    "借用", "从跨作品母题镜像或同系列其他场景借用变体", "素材库有可用变体"),
    SuggestionDirection("transform", "转化", "将现有场景元素改造成母题载体",          "场景中已存在可承载母题的元素"),
    SuggestionDirection("restrain",  "克制", "建议不做某事，保持克制",               "weight ≤ 6 或已有 2+ 高 weight 母题"),
    SuggestionDirection("reverse",   "反向", "有意违抗母题以制造张力",               "无限制，需标风险"),
]

DIRECTION_MAP: dict[Direction, SuggestionDirection] = {d.id: d for d in DIRECTIONS}
