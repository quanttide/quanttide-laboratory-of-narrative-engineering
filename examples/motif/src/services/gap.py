"""缝隙分析服务 — 检测母题缺口、归因、生成改进建议"""

import json

from src.infra import call_llm, clean_json
from src.prompts import load_prompt
from src.services.converter import to_motifs
from src.models import Motif, GapItem, GapReport, GapAttribution, Suggestion


CROSS_WORK_MIRRORS = {
    "手势": ["校园: 纸巾擦眼泪→拆开鬼使神差擦上去", "校园: 披外套→扣扣子→拉进怀里"],
    "雨": ["校园: 无对应（校园无雨母题）"],
    "十年": ["校园: 无对应（校园无时间跨度母题）"],
    "孤独": ["校园: 无对应"],
    "歌声": ["校园: 无对应"],
    "论坛": ["都市: 无对应"],
    "协作书写": ["都市: 无对应"],
    "旁观者": ["都市: 封闭二人空间（反向: 缺席即在场）"],
    "随身携带的温柔": ["都市: 超市新买的毛巾→不知不觉伸出去擦头发"],
}


def compute_gap_report(extracted: list[Motif], target_motifs: list[dict]) -> GapReport:
    """对比提取母题与目标母题库，生成缝隙报告。"""
    extracted_titles = {m.title for m in extracted}
    covered, missing, weak = [], [], []
    for tm in target_motifs:
        t = tm["title"]
        if t in extracted_titles:
            ext = next(m for m in extracted if m.title == t)
            if ext.weight < tm.get("weight", 5) * 0.5:
                weak.append(GapItem(title=t, target_weight=tm["weight"], extracted_weight=ext.weight))
            else:
                covered.append(GapItem(title=t, target_weight=tm["weight"], extracted_weight=ext.weight))
        else:
            found = False
            for et in extracted:
                if et.matches_title(t):
                    if et.weight < tm["weight"] * 0.5:
                        weak.append(GapItem(title=t, target_weight=tm["weight"], extracted_weight=et.weight, matched_via=et.title))
                    else:
                        covered.append(GapItem(title=t, target_weight=tm["weight"], extracted_weight=et.weight, matched_via=et.title))
                    found = True
                    break
            if not found:
                missing.append(GapItem(title=t, target_weight=tm["weight"], description=tm.get("description", "")))
    return GapReport(covered=covered, missing=missing, weak=weak, extracted_motifs=extracted)


def gap_attribution(article_name: str, text_sample: str, missing_motif: GapItem) -> GapAttribution:
    """分析母题缺失原因。"""
    prompt = load_prompt("p08/gap_attribution",
        article_name=article_name, missing_title=missing_motif.title,
        missing_description=missing_motif.description or "", sample=text_sample[:2000])
    raw = call_llm(prompt, "你是一个叙事编辑。只输出 JSON。", temperature=0.2)
    result = json.loads(clean_json(raw))
    return GapAttribution(
        gap_types=result.get("gap_types"),
        alternative_motif=result.get("alternative_motif"),
        reasoning=result.get("reasoning", ""),
    )


def generate_suggestions(article_name: str, text_sample: str, gap: GapItem, gap_types: list[str], target_motif: dict) -> list[Suggestion]:
    """从 6 个方向生成改进建议。"""
    mirrors = CROSS_WORK_MIRRORS.get(target_motif["title"], [])
    mirror_text = "跨作品/跨场景变体参考：\n" + "\n".join(f"  - {m}" for m in mirrors) if mirrors else ""
    prompt = load_prompt("p08/generate_suggestions",
        article_name=article_name, target_title=target_motif["title"],
        target_description=target_motif.get("description", ""),
        gap_types_str=", ".join(gap_types), mirror_text=mirror_text,
        sample=text_sample[:2500])
    try:
        raw = call_llm(prompt, temperature=0.7)
        items = json.loads(clean_json(raw)).get("suggestions", [])
        return [Suggestion(direction=s["direction"], text=s.get("text", ""),
                           paragraph_ref=s.get("paragraph_ref", ""),
                           reverse_risk=s.get("reverse_risk"))
                for s in items]
    except Exception:
        return []


def evaluate_suggestions(suggestions: list[Suggestion], gap_title: str, article_name: str) -> list[dict]:
    """对改进建议做 4 维度评分。"""
    items = "\n".join(f"[{s.direction}] {s.text[:120]}" for s in suggestions)
    prompt = load_prompt("p08/evaluate_suggestions", article_name=article_name, gap_title=gap_title, items=items)
    try:
        raw = call_llm(prompt, temperature=0.1)
        return json.loads(clean_json(raw)).get("evaluations", [])
    except Exception:
        return []
