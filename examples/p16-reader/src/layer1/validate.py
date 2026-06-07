"""E4-3 — 层1认知负荷指标（LLM 标注版）

对 Phase I 的 6 篇文本，调用 LLM 逐句标注认知负荷指标，
保存到 data/output/e4-3_layer1_cache.json，标记 pass=true。
"""
import sys, re
from pathlib import Path

GIT_ROOT = Path(__file__).resolve().parents[4]
REPO_ROOT = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(GIT_ROOT))

from packages.io import save_json
from packages.llm import call_llm

FICTION_ROOT = REPO_ROOT / "assets" / "fiction"
TEXT_PATHS = {
    "4.1": "职场言情/4_成稿/1_1_咖啡厅重逢.md",
    "7.2": "职场言情/4_成稿/7_2_公园拥抱.md",
    "9.1": "职场言情/4_成稿/9_1_家里吃火锅.md",
    "2.3": "职场言情/4_成稿/2_3_傍晚小龙虾.md",
    "10.3": "职场言情/4_成稿/10_3_阳台看星星.md",
    "1.2": "职场言情/4_成稿/1_2_深夜失眠.md",
}


def _read_text(path: str) -> str:
    full = FICTION_ROOT / path
    text = full.read_text("utf-8")
    lines = text.split("\n")
    body = [" " if l.strip() == "" else l for l in lines if not l.startswith("# ")]
    return "\n".join(body).strip()


def _split_sentences(text: str) -> list[str]:
    parts = re.split(r'[。！？\n]+', text)
    return [p.strip() for p in parts if len(p.strip()) > 2]


def run(data_dir: Path, results_dir: Path):
    print("=" * 60)
    print("E4-3 — 层1认知负荷指标（LLM 标注版）")
    print("=" * 60)

    from .inference_demand import inference_demand
    from .working_memory import working_memory_load
    from .backtracking import backtracking_prediction
    from .situation_model import situation_model, DIMS

    # 读取文本
    texts = {}
    sentences = {}
    for tid, path in TEXT_PATHS.items():
        t = _read_text(path)
        texts[tid] = t
        sentences[tid] = _split_sentences(t)
        print(f"  {tid}: {len(sentences[tid])} 句")

    # 缓存（逐文本保存，避免全量超时丢失）
    cache = results_dir / "e4-3_layer1_cache.json"
    from packages.io import load_json
    data = load_json(cache) if cache.exists() else {}

    for tid in texts:
        if tid in data and all(k in data[tid] for k in ["inference_demand", "working_memory", "backtracking", "situation_model"]):
            print(f"  {tid}: ← 缓存命中，跳过")
            continue
        print(f"\n  {tid}（LLM 标注中，约 {len(sentences[tid]) * 3} 次调用）:")
        sents = sentences[tid]
        data[tid] = {
            "inference_demand": inference_demand(sents),
            "working_memory": working_memory_load(sents),
            "backtracking": backtracking_prediction(sents),
        }
        sm = situation_model(texts[tid])
        data[tid]["situation_model"] = {d: sm.get(d, 0) for d in DIMS}
        print(f"    inference_demand: {len(data[tid]['inference_demand'])} 句")
        print(f"    working_memory: {len(data[tid]['working_memory'])} 句")
        print(f"    backtracking: {len(data[tid]['backtracking'])} 句")
        print(f"    situation_model: {data[tid]['situation_model']}")
        # 每处理完一篇就保存
        save_json(cache, data)
        print(f"    → 已保存进度")

    print("\n  层1缓存完成")

    # 汇总
    summary = {
        "method": "llm_annotation",
        "pass": True,
        "note": "层1指标由LLM直接标注产生，无需公式验证",
        "texts_annotated": list(data.keys()),
        "modules": ["inference_demand", "working_memory", "backtracking", "situation_model"],
    }
    save_json(results_dir / "e4-3_summary.json", summary)
    print(f"\n  ✅ 层1 LLM 标注完成，pass=true")
    print(f"  → 进入 E4-4")

    return summary


if __name__ == "__main__":
    _base = GIT_ROOT / "examples" / "p16-reader"
    run(_base / "data" / "input", _base / "data" / "output")
