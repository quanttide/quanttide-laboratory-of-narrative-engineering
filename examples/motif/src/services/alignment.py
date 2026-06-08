"""母题吻合度服务 — 检测生成文本的母题一致性"""

from src.infra import call_llm
from src.prompts import load_prompt
from src.models import Motif


def llm_motif_match(detected_title: str, target_title: str, target_description: str) -> bool:
    """用 LLM 判断提取的母题是否体现了目标母题的含义。"""
    prompt = load_prompt("p07/llm_motif_match",
        detected_title=detected_title, target_title=target_title, target_description=target_description)
    try:
        raw = call_llm(prompt, "你是一个叙事学分析助手。只输出 yes 或 no。", temperature=0.1)
        return raw.strip().lower() == "yes"
    except Exception:
        return False


def compute_alignment(detected: list[Motif], target_titles: set[str], target_motifs: list[Motif] | None = None) -> float:
    """计算母题吻合度（基于 LLM 语义判断）。"""
    if not target_titles:
        return 0.0
    target_map = {m.title: m.description for m in (target_motifs or [])}
    detected_titles = [m.title for m in detected]
    matched = 0
    for target in target_titles:
        desc = target_map.get(target, "")
        if any(llm_motif_match(dt, target, desc) for dt in detected_titles):
            matched += 1
    return min(matched / len(target_titles), 1.0)
