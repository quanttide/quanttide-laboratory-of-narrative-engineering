"""Gallery 服务 — YAML 知识库加载与实体转换"""

from pathlib import Path

from src.config import GALLERY_ROOT
from src.infra import load_motif_yaml, load_yaml
from src.infra.acl import to_motifs
from src.models import Motif, MotifProfile, Gallery, StyleDimension


def load_motif_profile() -> MotifProfile:
    """从 YAML 加载三层母题库，返回类型安全的 MotifProfile。"""
    def _load(level: str) -> list[Motif]:
        path = GALLERY_ROOT / ("motif.yaml" if level == "shared" else f"{level}-romance/motif.yaml")
        if not path.exists():
            return []
        data = load_motif_yaml(path)
        return to_motifs(data.get("motifs", []))
    return MotifProfile(shared=_load("shared"), urban=_load("urban"), campus=_load("campus"))


def load_gallery() -> Gallery:
    """加载完整知识库（motif + style）。"""
    mp = load_motif_profile()
    style_path = GALLERY_ROOT / "urban-romance" / "style.yaml"
    dims = []
    if style_path.exists():
        style_data = load_yaml(style_path)
        dims = [StyleDimension(title=d["title"], description=d.get("description", ""))
                for d in style_data.get("dimensions", [])]
    return Gallery(motifs=mp, style_dimensions=dims)


def build_style_prompt(style: dict, samples_dir: Path) -> str:
    """构建风格评审 prompt（嵌入 style.yaml + 参考场景）。"""
    parts = [f"风格框架「{style.get('title','')}」——{style.get('description','')}"]
    dims = style.get("dimensions", [])
    parts.append(f"共 {len(dims)} 个评价维度：\n")
    for d in dims:
        parts.append(f"【{d['title']}】(confidence={d.get('confidence','?')})")
        parts.append(f"  {d.get('description','')}")
        if d.get("clues"):
            parts.append(f"  clues: {'; '.join(d['clues'][:2])}")
        if d.get("tensions"):
            parts.append(f"  tensions: {'; '.join(d['tensions'][:2])}")
        parts.append("")
    if samples_dir.exists():
        sample_files = sorted(samples_dir.glob("sample*.md"))[:3]
        parts.append(f"\n参考场景（{len(sample_files)} 篇）：")
        for sf in sample_files:
            parts.append(f"\n--- {sf.stem} ---\n{sf.read_text('utf-8')[:800]}\n")
    return "\n".join(parts)
