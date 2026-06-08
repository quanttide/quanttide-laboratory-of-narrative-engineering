"""风格评审服务 — 风格诊断、母题关联、改法生成"""

import json
import random
from pathlib import Path

from src.infra import call_llm, call_llm_text, clean_json
from src.prompts import load_prompt
from src.services.converter import to_motifs, dims_to_dicts, to_dims
from src.models import Motif, StyleReview, StyleDimension, StyleMotifLink, FixGroup
from src.models.gallery import MotifProfile


def style_review(text: str, article_name: str, style_prompt: str) -> StyleReview:
    """风格评审 — 对文章做 11 维度评分。"""
    sample = text[:2500]
    prompt = load_prompt("p10/style_review", style_prompt=style_prompt, article_name=article_name, sample=sample)
    raw = call_llm(prompt, temperature=0.0)
    items = json.loads(clean_json(raw)).get("dimension_scores", [])
    dims = [StyleDimension(title=d["dimension"], score=d.get("score", 5),
                           evidence=d.get("evidence", []), note=d.get("note", ""))
            for d in items]
    return StyleReview(dimension_scores=dims)


def diagnose_style_motif_links(
    style_scores: list[dict],
    extracted_motifs: list[Motif],
    target_motifs: list[dict],
    article_name: str,
) -> dict:
    """两步诊断：自由推理 → 匹配已知母题库。"""
    weak_dims = [d for d in style_scores if d.get("score", 10) <= 7]
    if not weak_dims:
        return {"links": []}

    wd_text = "\n".join(f"- {d['dimension']} (score={d['score']}): {d.get('note','')}" for d in weak_dims)
    free_prompt = load_prompt("p10/free_diagnosis", article_name=article_name, wd_text=wd_text)
    raw = call_llm(free_prompt, "你是一个叙事诊断专家。只输出 JSON。", temperature=0.2)
    free_analysis = json.loads(clean_json(raw))

    pool = "\n".join(f"- {m['title']}: {m.get('description','')}" for m in target_motifs)
    hypotheses = "\n".join(f"- {d['weak_dimension']}: {d['root_cause_hypothesis']}"
                          for d in free_analysis.get("free_analysis", []))
    match_prompt = load_prompt("p10/diagnosis_match", hypotheses=hypotheses, target_motif_pool=pool)
    raw = call_llm(match_prompt, "你是一个叙事编辑。只输出 JSON。", temperature=0.2)
    return json.loads(clean_json(raw))


def generate_combined_fix(article_name: str, text_sample: str, weak_dim: str, related_motif: str,
                          motif_desc: str, dim_desc: str) -> str:
    """组合改法（风格诊断 + 母题根因）。"""
    prompt = load_prompt("p10/fix_combined",
        article_name=article_name, weak_dim=weak_dim, dim_desc=dim_desc,
        related_motif=related_motif, motif_desc=motif_desc, sample=text_sample[:2000])
    return call_llm_text(prompt, "你是一个创作顾问。只输出建议文本，不要JSON包装。", temperature=0.3).strip()


def generate_style_only_fix(article_name: str, text_sample: str, weak_dim: str, dim_desc: str) -> str:
    """纯风格改法（不提母题）。"""
    prompt = load_prompt("p10/fix_style_only",
        article_name=article_name, weak_dim=weak_dim, dim_desc=dim_desc, sample=text_sample[:2000])
    return call_llm_text(prompt, "你是一个创作顾问。只输出建议文本。", temperature=0.3).strip()


def evaluate_pairwise(fix_a: tuple, fix_b: tuple, weak_dim: str, related_motif: str) -> dict:
    """盲评对比两条改法。"""
    label_a, text_a = fix_a
    label_b, text_b = fix_b
    if random.random() < 0.5:
        label_a, label_b, text_a, text_b = label_b, label_a, text_a, text_b
    prompt = load_prompt("p10/evaluate_pairwise",
        weak_dim=weak_dim, text_a=text_a[:400], text_b=text_b[:400], related_motif=related_motif)
    raw = call_llm(prompt, "你是一个叙事编辑。只输出 JSON。", temperature=0.1)
    return json.loads(clean_json(raw))
