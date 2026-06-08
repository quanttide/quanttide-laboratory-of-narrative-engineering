"""类型转换器 — dict↔dataclass 互转、JSON 序列化"""

import dataclasses
import json
from typing import Any

from src.models import Motif, GapItem, GapReport, StyleDimension


class DataclassJSONEncoder(json.JSONEncoder):
    """支持 dataclass 的 JSON 编码器，自动调用 dataclasses.asdict()。"""
    def default(self, o: Any) -> Any:
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)


def to_motifs(items) -> list[Motif]:
    """将 LLM 返回或缓存读取的原始 dict 数据转为 list[Motif]（幂等）。"""
    if not items:
        return []
    if isinstance(items[0], Motif):
        return items
    return [Motif(title=m.get("title", ""), description=m.get("description", ""), weight=m.get("weight", 5)) for m in items]


def to_dims(data) -> list[StyleDimension]:
    """原始 dict 或 StyleDimension 混合输入 → list[StyleDimension]（幂等）。"""
    if not data:
        return []
    if isinstance(data[0], StyleDimension):
        return data
    return [StyleDimension(title=d["title"], score=d.get("score", 5),
                           evidence=d.get("evidence", []), note=d.get("note", "")) for d in data]


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
