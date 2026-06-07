"""p17-reader-revision — 写作契约 vs 读者回响：单点反思

用法：
    python -m src                         # 批处理 Step 1-3
    python -m src feedback                # 生成 feedback.html 并打开
    python -m src feedback writeback      # 将导出的反馈写回 JSON
    python -m src feedback writeback <p>  # 写回指定文件
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))


def main():
    args = sys.argv[1:]

    if not args or args[0] == "batch":
        from .pipeline import run_batch
        run_batch()
    elif args[0] == "feedback":
        from .feedback import generate, write_back, write_file
        if len(args) >= 3 and args[1] == "writeback":
            if len(args) >= 3 and Path(args[2]).exists():
                write_file(args[2])
            else:
                print("用法: python -m src feedback writeback <导出文件.json>")
        else:
            generate()
    else:
        print(f"未知命令: {args[0]}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
