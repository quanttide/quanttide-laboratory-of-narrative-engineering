"""
story 组共享配置。

所有模块通过 from src.config import REPO_ROOT, FICTION_ROOT, ... 引用。
"""
from pathlib import Path

GROUP_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = GROUP_ROOT.parent.parent
FICTION_ROOT = REPO_ROOT / "assets" / "fiction"
GALLERY_ROOT = REPO_ROOT / "docs" / "gallery" / "fiction"
DATA_DIR = GROUP_ROOT / "data" / "output"
