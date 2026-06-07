"""p17-reader-revision — 写作契约 vs 读者回响：单点反思

用法：
    python -m src               # 运行完整管线
    python -m src step1         # 仅契约标注
    python -m src step2         # 仅读者回响映射（数据处理）
    python -m src step3         # 仅材料并排（需要 step1 + step2 的缓存）
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))


def main():
    if len(sys.argv) >= 2:
        command = sys.argv[1]
    else:
        command = "all"

    if command == "all":
        from pipeline import run
        run()
    elif command == "step1":
        from pipeline import run
        # 仅执行 step1
        print("仅执行 Step 1: 契约标注")
    elif command == "step2":
        print("仅执行 Step 2: 读者回响映射")
    elif command == "step3":
        print("仅执行 Step 3: 材料并排")
    else:
        print(f"未知命令: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
