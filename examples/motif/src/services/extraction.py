"""母题提取服务 — 统一 LLM 调用与实体转换"""

import json
from collections import defaultdict

from src.infra import call_llm, call_llm_openai, clean_json
from src.prompts import load_prompt
from src.infra.acl import to_motifs
from src.models import Motif


def extract_motifs(text: str, article_name: str, prompt_key: str = "p10/extract_motifs_style") -> list[Motif]:
    """从单篇文章中提取母题。

    Args:
        text: 文章文本
        article_name: 文章名
        prompt_key: 使用的 prompt 模板名（p05/p08/p10 各有略微不同的措辞）
    """
    sample = text[:3000]
    prompt = load_prompt(prompt_key, article_name=article_name, sample=sample)
    raw = call_llm(prompt)
    items = json.loads(clean_json(raw)).get("motifs", [])
    return to_motifs(items)


def extract_motifs_joint(texts: list[dict], series_name: str) -> list[Motif]:
    """从多篇合并文本中联合提取母题。"""
    combined_parts = [f"--- 文章: {t['name']} ---\n{t['text'][:2000]}" for t in texts]
    combined = "\n\n".join(combined_parts)
    prompt = load_prompt("p05/extract_joint_motif", series_name=series_name, combined=combined)
    raw = call_llm(prompt)
    items = json.loads(clean_json(raw)).get("motifs", [])
    return to_motifs(items)


def extract_motifs_from_text(text: str) -> list[Motif]:
    """场景级母题提取（供 p07 用）。"""
    sample = text[:2000]
    prompt = load_prompt("p07/extract_motifs_scene", sample=sample)
    raw = call_llm(prompt, "你是一个专业的叙事学分析助手。只输出 JSON。", temperature=0.3)
    items = json.loads(clean_json(raw)).get("motifs", [])
    return to_motifs(items)


def extract_motifs_cross_validate(text: str) -> list[Motif]:
    """用 GPT-4o-mini 做交叉验证提取（消除同源偏差）。"""
    sample = text[:2000]
    prompt = load_prompt("p07/extract_motifs_scene", sample=sample)
    try:
        raw = call_llm_openai(prompt, "你是一个专业的叙事学分析助手。只输出 JSON。", temperature=0.3)
        items = json.loads(clean_json(raw)).get("motifs", [])
        return to_motifs(items)
    except Exception:
        return []
