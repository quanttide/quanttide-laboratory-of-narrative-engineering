"""
DeepSeek LLM 客户端。

从 p09（类型注解 + temperature 参数化）和 p14（重试 + JSON 校验）中合并提炼。
"""
import json
import os
import sys

import requests

API_URL = "https://api.deepseek.com/chat/completions"


def get_api_key() -> str:
    key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not key:
        print("错误：请设置 DEEPSEEK_API_KEY 环境变量")
        sys.exit(1)
    return key


def call_llm(
    prompt: str,
    system: str = "只输出 JSON。",
    temperature: float = 0.3,
    max_retries: int = 3,
) -> str:
    """调用 DeepSeek API，带重试和 JSON 校验。

    参数：
        prompt: 用户提示词
        system: 系统提示词
        temperature: 采样温度 (0.0–1.0)
        max_retries: JSON 解析失败时的最大重试次数

    返回：
        LLM 返回的原始文本（已去除 markdown 代码块标记）

    异常：
        所有重试用尽后仍未返回有效 JSON 时，最后一次 `requests.post` 的异常会向外传播。
    """
    api_key = get_api_key()
    last_raw = ""

    for attempt in range(max_retries):
        try:
            resp = requests.post(
                API_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
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
            last_raw = resp.json()["choices"][0]["message"]["content"]
            last_raw = clean_json(last_raw)

            # 仅在要求 JSON 时校验（system 含 "JSON" 字样则校验）
            if "JSON" in system:
                json.loads(last_raw)
            return last_raw

        except (json.JSONDecodeError, requests.RequestException, KeyError):
            if attempt == max_retries - 1:
                raise
            continue

    return last_raw


def clean_json(raw: str) -> str:
    """去除 LLM 输出中的 markdown 代码块标记 (```json ... ```)。"""
    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.split("\n")
        lines = lines[1:] if lines[0].startswith("```") else lines
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        raw = "\n".join(lines)
    return raw.strip()
