"""p17-reader-revision — 写作契约 vs 读者回响：单点反思

用法：
    python -m src               # 批处理模式：Step 1-3（无反馈）
    python -m src feedback      # 反馈模式：逐点展示已保存的材料并收集反馈
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))


def main():
    if len(sys.argv) >= 2:
        command = sys.argv[1]
    else:
        command = "batch"

    if command == "batch" or command == "all":
        from .pipeline import run_batch
        run_batch()
    elif command == "feedback":
        from .pipeline import run_feedback
        run_feedback()
    else:
        print(f"未知命令: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
