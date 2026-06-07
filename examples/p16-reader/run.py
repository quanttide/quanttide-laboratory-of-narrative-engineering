"""
p16-reader — 模拟读者系统实验入口

用法：
    python run.py e4-0          # Prompt 操控性检验
    python run.py e4-1-pilot    # 分化验证 pilot（调用次数校准）
    python run.py e4-1          # 分化验证
    python run.py e4-2          # 跨文本泛化与外部锚定
    python run.py e4-3          # 层1自动化验证（Phase II）
    python run.py e4-4          # 权重映射标定（Phase II）
    python run.py e4-5          # 端到端集成验证（Phase II）
"""
import sys
from pathlib import Path

# 将 git root 加入 sys.path，使 from packages.xxx 可用
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

RESULTS_DIR = Path(__file__).parent / "results"


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]
    results_dir = RESULTS_DIR
    results_dir.mkdir(parents=True, exist_ok=True)

    if command == "e4-0":
        from phase1.e4_0_manipulation import run
        run(results_dir)
    elif command == "e4-1-pilot":
        from phase1.e4_1_pilot import run
        run(results_dir)
    elif command == "e4-1":
        from phase1.e4_1_differentiation import run
        run(results_dir)
    elif command == "e4-2":
        from phase1.e4_2_generalization import run
        run(results_dir)
    elif command == "e4-3":
        from src.e4_3_layer1 import run
        run(results_dir)
    elif command == "e4-4":
        from src.e4_4_weight_mapping import run
        run(results_dir)
    elif command == "e4-5":
        from src.e4_5_pipeline import run
        run(results_dir)
    else:
        print(f"未知命令: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
