"""E4-4 — 权重映射标定与验证入口"""
import sys
from pathlib import Path
GIT_ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(GIT_ROOT))
from .weight_mapping import run as _run_mapping


def run(data_dir: Path, results_dir: Path):
    return _run_mapping(results_dir)


if __name__ == "__main__":
    _base = GIT_ROOT / "examples" / "reader" / "p16-reader"
    from packages.python.io import ensure_dir
    run(_base / "data" / "input", ensure_dir(_base / "data" / "output"))
