"""E4-1 Pilot — 调用次数校准

选取 P1（甜宠少女）和 P3（资深老书虫）在文本 4.1 上各跑 10 次，
计算 ICC 和文笔评分的 Cohen's d，确定正式实验所需调用次数。
"""
import sys
from pathlib import Path

GIT_ROOT = Path(__file__).resolve().parents[5]
REPO_ROOT = Path(__file__).resolve().parents[7]
sys.path.insert(0, str(GIT_ROOT))

import numpy as np
from packages.python.llm import call_llm
from packages.python.io import save_json, load_json
from packages.python.stats import icc, cohens_d

FICTION_ROOT = REPO_ROOT / "assets" / "fiction"


def read_text(article_path: str) -> str:
    full = FICTION_ROOT / article_path
    text = full.read_text("utf-8")
    lines = text.split("\n")
    body = [" " if l.strip() == "" else l for l in lines if not l.startswith("# ")]
    return "\n".join(body).strip()


def run(data_dir: Path, results_dir: Path):
    print("=" * 60)
    print("E4-1 Pilot — 调用次数校准")
    print("=" * 60)

    profiles = load_json(data_dir / "profiles.json")
    p1 = [p for p in profiles if p["id"] == "P1"][0]
    p3 = [p for p in profiles if p["id"] == "P3"][0]
    text = read_text("职场言情/4_成稿/1_1_咖啡厅重逢.md")

    from .prompt_templates import build_evaluation_prompt

    cache = results_dir / "e4-1_pilot.json"
    if cache.exists():
        data = load_json(cache)
        print("← 读取缓存")
    else:
        data = []
        for profile, label in [(p1, "P1"), (p3, "P3")]:
            print(f"  画像 {label}...")
            for i in range(10):
                prompt = build_evaluation_prompt(profile, text)
                raw = call_llm(prompt, temperature=0.3)
                import json
                try:
                    resp = json.loads(raw)
                except json.JSONDecodeError:
                    print(f"    call {i}: JSON 解析失败，跳过")
                    continue
                resp["profile"] = label
                resp["call"] = i
                data.append(resp)
                print(f"    call {i}: 情感={resp.get('emotional_impact', '?')}, 难度={resp.get('reading_difficulty', '?')}")
        save_json(cache, data)
        print("  已保存")

    print("\n  样本响应字段:", list(data[0].keys()) if data else "无数据")

    # 适配实际字段名
    field = "emotional_impact"

    x = np.array([d[field] for d in data if d["profile"] == "P1"], dtype=float)
    y = np.array([d[field] for d in data if d["profile"] == "P3"], dtype=float)
    d_val = cohens_d(x, y)
    icc_val = icc(np.vstack([x.reshape(1, -1), y.reshape(1, -1)]))  # (2 raters × 10 targets)

    print(f"\n  字段: {field}")
    print(f"  P1 (甜宠少女) mean={x.mean():.2f}, sd={x.std(ddof=1):.2f}")
    print(f"  P3 (资深老书虫) mean={y.mean():.2f}, sd={y.std(ddof=1):.2f}")
    print(f"  Cohen's d = {d_val:.3f}")
    print(f"  ICC = {icc_val:.3f}")

    if abs(d_val) >= 1.0:
        n = 3
    elif abs(d_val) >= 0.5:
        n = 5
    else:
        n = 10

    result = {
        "field": field,
        "p1_mean": round(float(x.mean()), 2),
        "p1_sd": round(float(x.std(ddof=1)), 2),
        "p3_mean": round(float(y.mean()), 2),
        "p3_sd": round(float(y.std(ddof=1)), 2),
        "cohens_d": round(float(d_val), 3),
        "icc": round(float(icc_val), 3),
        "recommended_n_calls": n,
    }
    save_json(results_dir / "e4-1_pilot_result.json", result)
    print(f"\n  推荐 n_calls = {n}")


if __name__ == "__main__":
    _base = GIT_ROOT / "examples" / "reader" / "p16-reader"
    run(_base / "data" / "input", _base / "data" / "output")
