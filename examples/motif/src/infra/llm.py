"""LLM 调用基础设施: 统一 call_llm, clean_json, embedding"""

import json
import os
from pathlib import Path

import requests


def call_llm(
    prompt: str,
    system: str = "你是一个专业的叙事学分析助手。只输出 JSON。",
    temperature: float = 0.3,
    retries: int = 3,
) -> str:
    """调用 DeepSeek API，支持重试 + JSON 验证。"""
    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    api_url = "https://api.deepseek.com/chat/completions"
    if not api_key:
        print("错误：请设置 DEEPSEEK_API_KEY 环境变量")
        raise ValueError("DEEPSEEK_API_KEY 未设置")

    for attempt in range(retries):
        resp = requests.post(
            api_url,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                "temperature": temperature,
            },
            timeout=180,
        )
        resp.raise_for_status()
        raw = resp.json()["choices"][0]["message"]["content"]
        try:
            cleaned = clean_json(raw)
            json.loads(cleaned)
            return raw
        except json.JSONDecodeError:
            if attempt < retries - 1:
                continue
    raise RuntimeError(f"JSON parse failed after {retries} retries")


def call_llm_text(
    prompt: str,
    system: str = "你是一个创作顾问。",
    temperature: float = 0.3,
) -> str:
    """调用 DeepSeek API 返回纯文本（无 JSON 验证）。"""
    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    api_url = "https://api.deepseek.com/chat/completions"
    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY 未设置")

    resp = requests.post(
        api_url,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "temperature": temperature,
        },
        timeout=180,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def call_llm_openai(
    prompt: str,
    system: str = "你是一个专业的叙事学分析助手。只输出 JSON。",
    temperature: float = 0.3,
    model: str = "gpt-4o-mini",
) -> str:
    """调用 OpenAI 兼容 API（用于交叉验证，消除同源偏差）。"""
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        raise ValueError("请设置 OPENAI_API_KEY 环境变量")
    resp = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "temperature": temperature,
        },
        timeout=180,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def clean_json(raw: str) -> str:
    """移除 LLM 输出中的 markdown 代码围栏。"""
    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.split("\n")
        lines = lines[1:] if lines[0].startswith("```") else lines
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        raw = "\n".join(lines)
    return raw.strip()


def get_embedding(text: str) -> list[float]:
    """调用 embedding API 获取文本向量。"""
    api_key = os.environ.get("OPENAI_API_KEY", "")
    api_url = os.environ.get("EMBEDDING_API_URL", "https://api.openai.com/v1/embeddings")
    model = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")
    if not api_key:
        raise ValueError("请设置 OPENAI_API_KEY 环境变量以使用 embedding 匹配")
    resp = requests.post(
        api_url,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"input": text, "model": model},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["data"][0]["embedding"]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """计算两个向量的余弦相似度。"""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(y * y for y in b) ** 0.5
    return dot / (norm_a * norm_b) if norm_a and norm_b else 0.0


def semantic_similarity(desc_a: str, desc_b: str) -> float:
    """用 embedding 余弦相似度判断两个描述的语义相似度 (0-1)。"""
    try:
        emb_a = get_embedding(desc_a)
        emb_b = get_embedding(desc_b)
        return max(0.0, min(1.0, cosine_similarity(emb_a, emb_b)))
    except Exception:
        return 0.0
