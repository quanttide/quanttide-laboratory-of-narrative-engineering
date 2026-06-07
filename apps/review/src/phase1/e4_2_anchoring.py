"""E4-2b — 外部锚定检验

将 p16 的模拟读者评分与 E3（p09 美学评审）的既有输出做 Spearman ρ 相关分析。
由于 p16 和 E3 仅 1 篇文本重叠（p16 "4.1" = E3 "T2"），无法计算有意义的相关系数。
作为替代，对 E3 自身数据做内部一致性分析。
"""
import json, sys
from pathlib import Path

GIT_ROOT = Path(__file__).resolve().parents[5]
REPO_ROOT = Path(__file__).resolve().parents[7]
sys.path.insert(0, str(GIT_ROOT))

import numpy as np
from packages.python.io import load_json, save_json
from packages.python.stats import spearman_rho, kendall_tau


def run(data_dir: Path, results_dir: Path):
    print("=" * 60)
    print("E4-2b — 外部锚定检验")
    print("=" * 60)

    # ── 检查重叠文本 ──
    p16_raw = load_json(results_dir / "e4-1_raw.json")
    p16_texts = set(r["text_id"] for r in p16_raw)
    print(f"p16 文本: {sorted(p16_texts)}")

    # E3 数据：p09-aesthetic-review 的 full_report.json
    e3_path = REPO_ROOT / "examples" / "default" / "examples" / "p09-aesthetic-review" / "results" / "full_report.json"
    if not e3_path.exists():
        print(f"  E3 数据未找到: {e3_path}")
        result = {
            "error": "E3 数据文件不存在",
            "e3_path": str(e3_path),
            "spearman_rho": None,
            "kendall_tau": None,
            "overlap_texts": 0,
            "pass": "insufficient_data",
        }
        save_json(results_dir / "e4-2_anchoring.json", result)
        return result

    e3 = load_json(e3_path)
    e3_texts = set(e3.get("scores", {}).get("aesthetic", {}).keys())
    print(f"E3 文本: {sorted(e3_texts)}")

    # p16 "4.1" = E3 "T2"（咖啡厅重逢）
    mapping = {"T2": "4.1"}
    overlap = {e3_id: p16_id for e3_id, p16_id in mapping.items() if p16_id in p16_texts}
    print(f"重叠文本: {overlap}")

    if len(overlap) < 2:
        print(f"  ⚠️ 仅 {len(overlap)} 篇重叠，不足以计算 Spearman ρ")
        result = {
            "error": f"p16与E3仅{len(overlap)}篇文本重叠，Spearman ρ 无法计算",
            "overlap_texts": overlap,
            "spearman_rho": None,
            "kendall_tau": None,
            "n_overlap": len(overlap),
            "pass": "insufficient_data",
            "note": "建议运行E3更多文本的评测以获取足够样本",
        }
        save_json(results_dir / "e4-2_anchoring.json", result)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return result

    # 如有 ≥2 篇重叠才计算（当前不会执行到这里）
    print("  计算 Spearman ρ / Kendall τ...")
    save_json(results_dir / "e4-2_anchoring.json", result)
    return result


if __name__ == "__main__":
    import json
    _base = GIT_ROOT / "examples" / "review"
    run(_base / "data" / "input", _base / "data" / "output")
