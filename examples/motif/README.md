# motif/ — 母题分析管线

从文本中提取母题 → 跨作品识别 → 约束验证 → 缝隙分析 → 风格合成。

| 模块 | 来源 | 功能 |
|------|------|------|
| `p05_extract.py` | p05 | 单篇/多篇母题提取 + 盲品归因 |
| `p06_cross_work.py` | p06 | 跨作品母题相似度矩阵 + 配对盲测 |
| `p07_consistency.py` | p07 | 母题约束生成 + 一致性检测 |
| `p08_gap_analysis.py` | p08 | 初稿母题缝隙检测 + 6 方向建议 |
| `p10_synthesize.py` | p10 | 风格-母题双层诊断 + 三组改法对比 |

## 用法

```bash
uv run python src/p05_extract.py
uv run python src/p06_cross_work.py
uv run python src/p07_consistency.py
uv run python src/p08_gap_analysis.py
uv run python src/p10_synthesize.py
```
