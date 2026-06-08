"""类型转换器 — dict↔dataclass 互转，统一处理接口"""

from src.models import Motif, GapItem, GapReport, StyleDimension, MatchItem


def to_motifs(items) -> list[Motif]:
    """将 LLM 返回或缓存读取的原始 dict 数据转为 list[Motif]（幂等）。"""
    if not items:
        return []
    if isinstance(items[0], Motif):
        return items
    return [Motif(title=m["title"], description=m.get("description", ""), weight=m.get("weight", 5)) for m in items]


def motifs_to_dicts(motifs: list[Motif]) -> list[dict]:
    """list[Motif] → list[dict]（JSON 序列化用）。"""
    return [vars(m) for m in motifs]


def to_dims(data) -> list[StyleDimension]:
    """原始 dict 或 StyleDimension 混合输入 → list[StyleDimension]（幂等）。"""
    if not data:
        return []
    if isinstance(data[0], StyleDimension):
        return data
    return [StyleDimension(title=d["title"], score=d.get("score", 5),
                           evidence=d.get("evidence", []), note=d.get("note", "")) for d in data]


def dims_to_dicts(dims: list[StyleDimension]) -> list[dict]:
    """list[StyleDimension] → list[dict]（JSON 序列化用）。"""
    return [vars(d) for d in dims]


def to_gap_report(data) -> GapReport:
    """原始 dict 或 GapReport → GapReport（幂等，兼容缓存）。"""
    if isinstance(data, GapReport):
        return data
    def _items(items):
        if not items:
            return []
        if isinstance(items[0], GapItem):
            return items
        return [GapItem(title=i["title"], target_weight=i["target_weight"],
                        extracted_weight=i.get("extracted_weight"), description=i.get("description", ""),
                        matched_via=i.get("matched_via")) for i in items]
    return GapReport(covered=_items(data.get("covered", [])), missing=_items(data.get("missing", [])),
                     weak=_items(data.get("weak", [])),
                     extracted_motifs=to_motifs(data.get("extracted_motifs", [])))


def gap_report_to_dict(r: GapReport) -> dict:
    """GapReport → dict（JSON 序列化用）。"""
    return {
        "covered": [{"title": i.title, "target_weight": i.target_weight, "extracted_weight": i.extracted_weight,
                      "description": i.description, "matched_via": i.matched_via} for i in r.covered],
        "missing": [{"title": i.title, "target_weight": i.target_weight, "extracted_weight": i.extracted_weight,
                      "description": i.description, "matched_via": i.matched_via} for i in r.missing],
        "weak": [{"title": i.title, "target_weight": i.target_weight, "extracted_weight": i.extracted_weight,
                   "description": i.description, "matched_via": i.matched_via} for i in r.weak],
        "extracted_motifs": motifs_to_dicts(r.extracted_motifs),
    }


def pairs_to_dicts(pairs: list) -> list[dict]:
    """list[MotifSimilarityPair] → list[dict]（JSON 序列化用）。"""
    if not pairs:
        return []
    if isinstance(pairs[0], dict):
        return pairs
    return [vars(p) for p in pairs]
