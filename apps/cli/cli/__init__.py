#!/usr/bin/env python3
"""
qtcloud-3r — 3R writing toolchain for AI.
"""

import json
import os
import sys
import argparse
from pathlib import Path

import requests

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
API_URL = "https://api.deepseek.com/chat/completions"
DEFAULT_MODEL = "deepseek-chat"


def read_input(file: str | None) -> str:
    if file and file != "-":
        return Path(file).read_text("utf-8")
    return sys.stdin.read()


def write_output(data, fmt: str):
    out = json.dumps(data, ensure_ascii=False, indent=2) if fmt == "json" else str(data)
    print(out)


def call_llm(prompt: str, system: str = "", model: str = DEFAULT_MODEL, temp: float = 0.3) -> str:
    if not DEEPSEEK_API_KEY:
        print("错误：请设置 DEEPSEEK_API_KEY 环境变量", file=sys.stderr)
        sys.exit(1)
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    resp = requests.post(
        API_URL,
        headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"},
        json={"model": model, "messages": messages, "temperature": temp},
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def clean_json(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    return raw


# ── prompts ──

REVIEW_PROMPT = """请阅读下面的文章片段，从写作意图的角度分析它。

不需要找问题。只需要理解这段文本在做什么。

输出 JSON：
{{
  "genre": "场景体裁分类（如：重逢场景/日常对话/情感释放/事件驱动），10字以内",
  "intent": "作者的创作意图（如：营造暧昧氛围/推进人物关系/展示角色性格），20字以内",
  "stage": "根据文本呈现出来的完成度，判断这是初稿还是成稿，以及一句话依据",
  "summary": "一句话总结这段文本在干什么（30字以内）"
}}

文章：
{text}"""

REFLECT_PROMPT = """你是一个写作诊断专家。以下是对当前文本的意图理解：

体裁：{genre}
意图：{intent}
阶段：{stage}

请检测文本中的写作空隙，并对每个空隙从 4 个角度分析深层原因。

空隙类型（5 种）：
- time_jump：时间跳跃没有过渡标记
- dialog_gap：对话之间缺少反应或沉默描写
- action_gap：动作之间缺少衔接
- perspective_shift：视角切换缺少锚点
- transition：场景转换缺少桥梁

必须输出 JSON 数组，格式如下（不要额外文字）：
[
  {{
    "gap_type": "time_jump",
    "location": "具体的段落位置描述",
    "detail": "问题说明",
    "structure": "叙事结构角度的归因",
    "psychology": "人物心理角度的归因",
    "reader": "读者期待角度的归因",
    "craft": "有意识留白 或 无意识忽略",
    "root_cause": "一句话总结根本原因"
  }}
]

文本：
{text}"""

REWRITE_PROMPT = """当前文本的定位：
体裁：{genre}
意图：{intent}

对文本中空隙的诊断：
{analysis}

请带着以上理解重新修改文章。注意：
- 如果空隙被判定为"有意识留白"，不需要修改
- 如果空隙被判定为"无意识忽略"，针对性地补写
- 保持原文的风格和节奏

输出格式：直接输出修改后的完整文章。

原文：
{text}"""


# ── commands ──


def cmd_review(text: str, model: str, temp: float) -> dict:
    raw = call_llm(REVIEW_PROMPT.format(text=text), model=model, temp=temp)
    return json.loads(clean_json(raw))


def cmd_reflect(text: str, model: str, temp: float) -> list[dict]:
    review = cmd_review(text, model, temp)
    prompt = REFLECT_PROMPT.format(
        genre=review.get("genre", ""),
        intent=review.get("intent", ""),
        stage=review.get("stage", ""),
        text=text,
    )
    raw = call_llm(prompt, model=model, temp=temp)
    result = json.loads(clean_json(raw))
    if isinstance(result, list):
        return result
    if isinstance(result, dict) and "analysis" in result:
        return result["analysis"]
    return []


def cmd_rewrite(text: str, model: str, temp: float) -> str:
    review = cmd_review(text, model, temp)
    analysis = cmd_reflect(text, model, temp)
    if not analysis:
        return text
    analysis_text = "\n".join(
        f"{i+1}. [{a['gap_type']}] {a.get('detail', '')}\n"
        f"   叙事结构: {a.get('structure', '')}\n"
        f"   人物心理: {a.get('psychology', '')}\n"
        f"   读者期待: {a.get('reader', '')}\n"
        f"   写作技法: {a.get('craft', '')}\n"
        f"   根本原因: {a.get('root_cause', '')}"
        for i, a in enumerate(analysis)
    )
    prompt = REWRITE_PROMPT.format(
        genre=review.get("genre", ""),
        intent=review.get("intent", ""),
        analysis=analysis_text,
        text=text,
    )
    return clean_json(call_llm(prompt, model=model, temp=temp))


# ── entry point ──


def main():
    parser = argparse.ArgumentParser(description="qtcloud-3r — 3R writing toolchain")
    parser.add_argument("command", choices=["review", "reflect", "rewrite", "3r"])
    parser.add_argument("file", nargs="?", default="-", help="输入文件（默认 stdin）")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--temp", type=float, default=0.3)
    parser.add_argument("--format", choices=["json", "text"], default="json")

    args = parser.parse_args()
    text = read_input(args.file)
    if not text.strip():
        print("错误：输入为空", file=sys.stderr)
        sys.exit(1)

    if args.command == "review":
        write_output(cmd_review(text, args.model, args.temp), args.format)
    elif args.command == "reflect":
        write_output(cmd_reflect(text, args.model, args.temp), args.format)
    elif args.command == "rewrite":
        result = cmd_rewrite(text, args.model, args.temp)
        write_output(result, "text" if args.format == "text" else "json")
    elif args.command == "3r":
        result = {
            "review": cmd_review(text, args.model, args.temp),
            "reflect": cmd_reflect(text, args.model, args.temp),
            "rewrite": cmd_rewrite(text, args.model, args.temp),
        }
        write_output(result, args.format)
