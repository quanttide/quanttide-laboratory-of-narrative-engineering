"""p16-reader — 模拟读者系统实验入口

用法：
    python -m src e4-0           # Prompt 操控性检验
    python -m src e4-1-pilot     # 分化验证 pilot（调用次数校准）
    python -m src e4-1           # 分化验证
    python -m src e4-2           # 跨文本泛化与外部锚定
    python -m src e4-3           # 层1自动化验证（Phase II）
    python -m src e4-4           # 权重映射标定（Phase II）
    python -m src e4-5           # 端到端集成验证（Phase II）
"""
import sys
from pathlib import Path

# git root = p16-reader/src/__main__.py → parents[3]
REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

DATA_DIR = REPO_ROOT / "examples" / "p16-reader" / "data" / "input"
RESULTS_DIR = REPO_ROOT / "examples" / "p16-reader" / "data" / "output"


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    commands = {
        "e4-0": "src.phase1.e4_0_manipulation",
        "e4-1-pilot": "src.phase1.e4_1_pilot",
        "e4-1": "src.phase1.e4_1_differentiation",
        "e4-2": "src.phase1.e4_2_generalization",
        "e4-2-g": "src.phase1.e4_2_generalization",
        "e4-2-a": "src.phase1.e4_2_anchoring",
        "e4-3": "src.layer1.validate",
        "e4-4": "src.layer2.validate",
        "e4-5": "src.pipeline",
    }

    if command not in commands:
        print(f"未知命令: {command}")
        sys.exit(1)

    mod = __import__(commands[command], fromlist=["run"])
    mod.run(DATA_DIR, RESULTS_DIR)


if __name__ == "__main__":
    main()
