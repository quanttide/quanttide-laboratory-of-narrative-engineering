# style/ — 风格提取与评审管线

从文本中提取风格特征，以作者审美框架评审新场景。

| 模块 | 来源 | 功能 |
|------|------|------|
| `p03_style_extraction.py` | p03 | 风格特征提取 → 聚类 → 归因 |
| `p09_aesthetic_review.py` | p09 | 内化 style.yaml 审美 → 10 维度评分 |

## 用法

```bash
uv run python src/p03_style_extraction.py
uv run python src/p09_aesthetic_review.py
```
