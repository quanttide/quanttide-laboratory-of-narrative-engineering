# motif/ — 母题分析管线

从文本中提取母题 → 跨作品识别 → 约束验证 → 缝隙分析 → 风格合成。

## 目录结构

```
src/
├── models/          ← 领域模型实体
│   ├── types.py     — Literal 类型别名
│   ├── motif.py     — Motif, SubMotif, Variant
│   ├── article.py   — Article, SceneTemplate, ArticleAnalysis
│   ├── analysis.py  — GapItem/Report/Attribution, Suggestion, DIRECTIONS
│   ├── style.py     — StyleDimension, StyleMotifLink, StyleReview, FixGroup
│   ├── eval.py      — MatchItem, CoverageReport, EvaluationScore, MotifSimilarityPair
│   └── gallery.py   — MotifProfile, Gallery
├── services/        ← 应用服务（统一导出 infra + prompts）
├── infra/           ← 基础设施委托（→ packages/python 共享包）
├── prompts.py       ← prompt 模板加载
├── config.py        ← 路径配置
├── p05_extract.py   ← 实验：母题可提取性（保留）
├── p06_cross_work.py
├── p07_consistency.py
├── p08_gap_analysis.py
├── p10_synthesize.py
└── p11_hierarchy.py
examples/            ← 实验文件副本（含独立 sys.path）
├── p05_extract.py
├── p06_cross_work.py
└── ...
```

## 用法

```bash
# 从 src/ 运行
uv run python src/examples/p05_extract.py
uv run python src/p06_cross_work.py

# 或从 examples/ 运行（含独立 sys.path）
uv run python examples/p05_extract.py
```
