"""领域模型实体定义"""

from dataclasses import dataclass, field
from typing import Optional


# ─── 值对象 ───

@dataclass
class MotifEvidence:
    """母题的原文证据"""
    text: str


@dataclass
class Motif:
    """母题（Motif）—— 叙事中反复出现的主题元素"""
    title: str
    description: str
    weight: int = 5
    evidence: list[str] = field(default_factory=list)

    def __post_init__(self):
        assert 1 <= self.weight <= 10, f"weight must be 1-10, got {self.weight}"


@dataclass
class SubMotif:
    """子母题 —— 同一母题下的不同变体类型"""
    parent_title: str
    name: str
    variants: list[str] = field(default_factory=list)


@dataclass
class Variant:
    """变体 —— 同一母题在不同作品/场景中的不同表现"""
    motif: str
    series: str
    scene: str
    description: str


@dataclass
class Article:
    """文章 / 场景 —— 被分析的基本文本单位"""
    id: str
    series: str
    name: str
    path: str
    type: str = ""


@dataclass
class SceneTemplate:
    """场景模板 —— 用于生成测试场景"""
    id: str
    name: str
    type: str
    desc: str


@dataclass
class ExtractedMotifResult:
    """单篇文章的母题提取结果"""
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
class GapReport:
    """缝隙分析报告"""
    covered: list[GapItem] = field(default_factory=list)
    missing: list[GapItem] = field(default_factory=list)
    weak: list[GapItem] = field(default_factory=list)
    extracted_motifs: list[Motif] = field(default_factory=list)


@dataclass
class GapAttribution:
    """缝隙归因"""
    gap_types: list[str] = field(default_factory=list)
    alternative_motif: Optional[str] = None
    reasoning: str = ""


# ─── 改进建议 ───

@dataclass
class Suggestion:
    """改进建议（6 方向）"""
    direction: str  # amplify / introduce / borrow / transform / restrain / reverse
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


@dataclass
class StyleMotifLink:
    """风格-母题关联诊断"""
    weak_dimension: str
    related_missing_motif: Optional[str] = None
    confidence: str = "medium"
    hypothesis: str = ""


# ─── 评估 ───

@dataclass
class EvaluationScore:
    """建议/改法的多维评分"""
    feasibility: int = 3
    motif_fit: int = 3
    naturalness: int = 3
    actionable: int = 3


@dataclass
class CoverageReport:
    """覆盖率报告"""
    extracted_count: int = 0
    matched_count: int = 0
    coverage: float = 0.0
    matches: list[dict] = field(default_factory=list)


# ─── 跨作品分析 ───

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
    pair_type: str = ""  # cross-series_same-motif / cross-series_diff-motif / intra-series_diff-motif


# ─── 样式常量 ───

DIRECTIONS = [
    {"id": "amplify",  "name": "增强", "desc": "强化已存在但偏弱的母题",               "trigger": "母题已被检测到但 weight 偏低"},
    {"id": "introduce","name": "引入", "desc": "添加一个完全缺失的母题",               "trigger": "母题完全缺失"},
    {"id": "borrow",   "name": "借用", "desc": "从跨作品母题镜像或同系列其他场景借用变体", "trigger": "素材库有可用变体"},
    {"id": "transform","name": "转化", "desc": "将现有场景元素改造成母题载体",          "trigger": "场景中已存在可承载母题的元素"},
    {"id": "restrain", "name": "克制", "desc": "建议不做某事，保持克制",               "trigger": "weight ≤ 6 或已有 2+ 高 weight 母题"},
    {"id": "reverse",  "name": "反向", "desc": "有意违抗母题以制造张力",               "trigger": "无限制，需标风险"},
]
