"""infra: 基础设施 — 委托至 packages/python 共享包"""

import sys

from src.config import REPO_ROOT

# 共享包路径: examples/default/packages/
_packages_root = REPO_ROOT / "examples" / "default" / "packages"
if str(_packages_root) not in sys.path:
    sys.path.insert(0, str(_packages_root))

from python.llm import (
    call_llm,
    call_llm_text,
    call_llm_openai,
    clean_json,
    get_embedding,
    cosine_similarity,
    semantic_similarity,
)
from python.io import (
    read_article_text,
    load_motif_yaml,
    load_yaml,
    cache_or_compute,
    cache_or_compute_text,
    load_json,
    save_json,
    ensure_dir,
)
