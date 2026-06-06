# p15 — 提纲生成实验

验证从 YAML（style/story/motif）+ JSON（p14 suggestions）能否自动生成可用的 md 提纲，覆盖原有人工提纲的核心信息。

## 背景

当前提纲有两种来源：
- assets/fiction/2_提纲/*.md（人工撰写，含母题分析、全貌轨迹、隐喻分析）
- p14 pipeline 输出的 chain/diagnosis/suggestion JSON（自动化，含行为链标注、薄弱点诊断、修改建议）

两者功能不同（面向人 vs 面向机器），但内容有重叠。p15 验证能否从 YAML+JSON 自动生成 md 提纲，取代人工撰写的工作量。

## 输入

| 来源 | 内容 | 格式 |
|------|------|------|
| `style.yaml` | boundaries（规则+判断标准） | YAML |
| `motif.yaml` | motif 权重+description | YAML |
| `story.yaml` | tensions（场次+结构难点） | YAML |
| `suggestions_S1.json` | p14 输出的 3 策略建议 | JSON |
| `suggestions_S2.json` | p14 输出的 3 策略建议 | JSON |
| `chain_S1/S2.json` | 行为链标注 | JSON |

## 输出

每个目标场景（1_1、8_2）生成一份 md 提纲，包含：

| 模块 | 来源 | 说明 |
|------|------|------|
| 行为序列 | chain JSON → seq 列表 | 从行为链标注中提取 actor+action |
| 边界提醒 | style.yaml boundaries | 聚合该场景适用的边界规则，每条标注引用维度 |
| 母题信号 | motif.yaml weight | 高 weight 母题（≥8）在该场景中的表现形态 |
| 薄弱点 | diagnosis JSON | 直接嵌入 p14 的诊断结果 |
| 修改建议 | suggestions JSON | 3 策略可选，标注来源 |
| 结构难点 | story.yaml tensions | 从 tensions 中提取结构层面（非情感层面）的条目 |

## 实验步骤

```
步骤 1: 数据加载
  └─ 读取 style.yaml → 提取所有 boundaries
  └─ 读取 motif.yaml → 提取 title + weight + description
  └─ 读取 story.yaml → 提取目标场景的 description + tensions
  └─ 读取 chain_S1.json → 提取行为序列
  └─ 读取 diagnosis_S1.json → 提取薄弱点
  └─ 读取 suggestions_S1.json → 提取 3 策略方案

步骤 2: 提纲生成
  └─ 对每个目标场景，由 LLM 聚合上述输入，输出 md 提纲
  └─ 约束：提纲面向写作者，语言为执行式（"注意""不要""建议"）
        而非分析式（"这个母题进化路径为……"）
  └─ 模板：

    # {id} {title} — 写作备忘

    ## 行为序列

    [从 chain 中提取，每个行为用→连接]

    ## 结构难点

    [从 story.tensions 中提取结构层面条目]
    - 每条标注来源（哪条 tension）
    - 说明该难点在当前场景中的具体表现

    ## 边界提醒

    [从 style.boundaries 中聚合适用的部分]
    - 每条标注适用维度名
    - 语言为执行式： "注意：……""不要……"

    ## 薄弱点与建议

    [从 p14 diagnosis + suggestions 中合并]
    每条展开：位置 → 问题（issue_type+severity） → 策略A / 策略B / 策略C

    注意：策略C（替代行为）不应降级情感信号。如果原行为承载了关键情感，替代方案应保留同等的情感重量，而非退到最安全选项。

步骤 3: 质量评估
  └─ 对比自动生成的提纲 vs 原有人工提纲（assets/fiction/2_提纲/*.md）
  └─ 评估维度：
      ├─ 覆盖度：自动提纲是否覆盖了人工提纲的核心易错点？
      ├─ 精确性：自动提纲中的每一条是否可追溯到具体的 YAML/JSON 源？
      └─ 可用性：写作者是否愿意用自动提纲替代人工提纲？
```

## 验收标准

| 指标 | 合格线 | 良好线 | 优秀线 |
|------|--------|--------|--------|
| 行为序列与人工提纲一致 | 80% | 90% | 100% |
| 边界提醒覆盖人工提纲中所有易错点 | 60% | 80% | 100% |
| 薄弱点直接来自 p14 diagnosis | 100% | 100% | 100% |
| 每一条输出可追溯到 YAML/JSON 源 | 80% | 90% | 100% |

## 输出产物

1. `results/outline_1_1.md`（自动生成的 1.1 提纲）
2. `results/outline_8_2.md`（自动生成的 8.2 提纲）
3. `results/evaluation.json`（与人工提纲的对比评估）

## 不依赖

Python 脚本 + LLM API。依赖：
- docs/gallery/fiction/urban-romance/ 下的 style.yaml / motif.yaml / story.yaml
- examples/p14-intra-scene-plot/results/ 下的 chain/diagnosis/suggestions JSON

## 结果预期

- **最强信号**：行为序列和薄弱点部分应高度可靠（直接从结构化数据提取，无需 LLM 判断）
- **最不确定**：边界提醒的聚合——LLM 需要判断 style.yaml 的 11 个 dimensions 中哪些与当前场景相关，这个筛选可能有遗漏或误报
- **最大的增量价值**：如果自动提纲覆盖了人工提纲中 80%+ 的易错点，说明 p14 pipeline + YAML 的数据足以支撑提纲生成，后续可以按需批量生成所有场景的提纲
- **失败条件**：如果自动提纲遗漏人工提纲中标记为"关键"的易错点（如 1.1 的"毛巾不能是预谋的"），说明 YAML 中未编码该约束，需要补回 style.yaml 的 boundaries
