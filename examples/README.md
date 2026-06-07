# 叙事工程实验室 — 概念验证

## 已完成

| PoC | 结论 | 状态 |
|-----|------|------|
| **p01** 叙事框架对比 | 起承转合、三幕、情感曲线弧线对齐。起承转合作默认框架 | ✅ 结论已应用（已归档） |
| **p02** 3R 效果度量 | Review→Reflect→Rewrite 管线验证通过 | ✅ 已封装为 CLI |
| **p03** 风格可提取性 | 聚类 100%、归因 100% | ✅ 待封装 |
| **p04** Review 可靠性 | 意图理解 15/15 稳定 | ✅ 已封装为 CLI |
| **p05** 母题可提取性 | LLM 可从文本中提取母题（56-58% 覆盖率），单篇信号足够 | 🟡 验收合格 |
| **p06** 母题跨作品识别 | 同一母题在不同作品中的变体可被 LLM 识别（F1=100% pairwise） | ✅ 验收优秀 |
| **p07** 母题一致性检验 | 母题可作为生成约束（都市 +20pp，校园 +45pp），具象母题强抽象母题弱 | 🟡 验收合格 |
| **p08** 母题缝隙分析 | LLM 可检测初稿母题缝隙并生成 6 方向差异化改进建议 | 🟡 验收合格 |
| **p09** 复刻作者审美评审 | LLM 可内化 style.yaml 审美框架，以作者审美标准评审新场景 | 🟡 验收合格 |
| **p10** 母题驱动的风格改进 | 三组改法各有优势——组合胜在具体性/自然度，母题单层胜在根因对准 | ✅ 验收合格 |
| **p14** 片段内部情节建议 | （进行中）验证 LLM 能否诊断场景内部的行为因果链和情感递进，生成可采纳的局部建议 | 🟡 进行中 |



## 已封装到 CLI

p02 和 p04 的实验代码已迁移到 `apps/cli/`，原始实验数据已删除。

## 保留的实验（按管线分组）

### motif/ — 母题分析管线

| PoC | 保留理由 | 目录 |
|-----|---------|------|
| p05 母题可提取性 | 母题提取基准数据 | [`motif/p05-motif-extraction/`](motif/p05-motif-extraction/) |
| p06 母题跨作品识别 | 跨作品母题映射验证 | [`motif/p06-cross-work-motif/`](motif/p06-cross-work-motif/) |
| p07 母题一致性检验 | 母题约束生成验证 | [`motif/p07-motif-consistency/`](motif/p07-motif-consistency/) |
| p08 母题缝隙分析 | 6 方向改法生成验证 | [`motif/p08-motif-gap-analysis/`](motif/p08-motif-gap-analysis/) |
| p10 母题驱动的风格改进 | 组合改法 vs 单层改法对比数据 | [`motif/p10-motif-style-synthesis/`](motif/p10-motif-style-synthesis/) |

### style/ — 风格提取与评审管线

| PoC | 保留理由 | 目录 |
|-----|---------|------|
| p03 风格可提取性 | 结论支持 StyleStore 策略，未封装 | [`style/p03-style-extraction/`](style/p03-style-extraction/) |
| p09 复刻作者审美评审 | 风格内化评估基准 | [`style/p09-aesthetic-review/`](style/p09-aesthetic-review/) |

### plot/ — 情节写作辅助管线

| PoC | 保留理由 | 目录 |
|-----|---------|------|
| p14 片段内部情节建议 | 场景内行为因果链的诊断与三类建议 | [`plot/p14-intra-scene-plot/`](plot/p14-intra-scene-plot/) |
| p15 提纲生成 | 从 YAML+JSON 自动生成写作提纲 | [`plot/p15-outline-generation/`](plot/p15-outline-generation/) |

### reader/ — 模拟读者系统

| PoC | 保留理由 | 目录 |
|-----|---------|------|
| p16 模拟读者 | 多画像读者模拟系统（Phase I 完成） | [`reader/p16-reader/`](reader/p16-reader/) |
