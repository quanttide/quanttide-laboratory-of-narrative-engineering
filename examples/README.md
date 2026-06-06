# 叙事工程实验室 — 概念验证

## 已完成

| PoC | 结论 | 状态 |
|-----|------|------|
| **p01** 叙事框架对比 | 起承转合、三幕、情感曲线弧线对齐。起承转合作默认框架 | ✅ 结论已应用 |
| **p02** 3R 效果度量 | Review→Reflect→Rewrite 管线验证通过 | ✅ 已封装为 CLI |
| **p03** 风格可提取性 | 聚类 100%、归因 100% | ✅ 待封装 |
| **p04** Review 可靠性 | 意图理解 15/15 稳定 | ✅ 已封装为 CLI |

## 待执行

| PoC | 假设 | 优先级 | 目录 |
|-----|------|--------|------|
| **p05** 母题可提取性 | LLM 可从文本中提取母题，且与人工标注的 motif.yaml 高度吻合 | 🔴 高 | [`p05-motif-extraction/`](p05-motif-extraction/) |
| **p06** 母题跨作品识别 | 同一母题在不同作品中的表现可被 LLM 识别和关联 | 🟡 中 | [`p06-cross-work-motif/`](p06-cross-work-motif/) |
| **p07** 母题一致性检验 | 以母题为约束生成多场景文本，检测母题是否在整个叙事中保持一致性 | 🟢 低 | [`p07-motif-consistency/`](p07-motif-consistency/) |
| **p08** 母题缝隙分析 | 检测初稿母题缝隙，从 6 个方向（增强/引入/借用/转化/克制/反向）提出差异化改进建议 | 🔴 高 | [`p08-motif-gap-analysis/`](p08-motif-gap-analysis/) |
| **p09** 复刻作者审美评审 | LLM 内化 style.yaml 中的人类作者审美框架，以该作者的审美标准评审新场景 | 🟡 中 | [`p09-aesthetic-review/`](p09-aesthetic-review/) |

## 已封装到 CLI

p02 和 p04 的实验代码已迁移到 `apps/cli/`，原始实验数据已删除。

## 保留的实验

| PoC | 保留理由 | 目录 |
|-----|---------|------|
| p01 叙事框架对比 | 实验数据支撑"起承转合作默认框架"的结论，未封装为 CLI 命令 | [`p01-narrative-frameworks/`](p01-narrative-frameworks/) |
| p03 风格可提取性 | 结论支持 StyleStore 策略，但未封装为 CLI 命令 | [`p03-style-extraction/`](p03-style-extraction/) |
