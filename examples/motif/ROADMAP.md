# Motif 领域模型 — 完善路线图

## 一、领域模型（当前版本 v0.5）

```
┌──────────────────────────────────────────────────────────────┐
│  Gallery (知识库 / 人工标注)                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ Shared Motif  │  │ Series Motif │  │ Style Framework  │   │
│  │ [6]           │  │ [5 / 4]      │  │ [11 dimensions]  │   │
│  └──────────────┘  └──────────────┘  └──────────────────┘   │
└──────────────────────────────────────────────────────────────┘
                           │ 对照/约束
                           ▼
┌──────────────────────────────────────────────────────────────┐
│  Article / Scene (被分析文本)                                │
│                                                              │
│  1. Motif Extraction ──→ ExtractedMotif [3-6]                │
│       │                  ├─ title / description / weight     │
│       │                  └─ evidence[] (原文引用)             │
│       │                                                      │
│  2. Gap Analysis ──→ GapReport                               │
│       │               ├─ Covered[] (满足的母题)               │
│       │               ├─ Missing[] (缺失的母题)               │
│       │               └─ Weak[] (弱化的母题)                  │
│       │                                                      │
│  3. Improvement ──→ Suggestion[6 directions]                 │
│       │              amplify / introduce / borrow             │
│       │              transform / restrain / reverse           │
│       │                                                      │
│  4. Style Diagnosis ──→ StyleReview + Diagnosis[]             │
│                         (弱维度 → 缺失母题的关联)              │
└──────────────────────────────────────────────────────────────┘
                           │ 跨作品
                           ▼
┌──────────────────────────────────────────────────────────────┐
│  Variant (跨作品变体)                                        │
│  ├─ motif: 所属母题                                          │
│  ├─ series: 所属系列                                         │
│  ├─ scene: 场景标识                                          │
│  └─ description: 变体表现                                     │
│                                                              │
│  MotifSimilarityPair                                         │
│  ├─ pair_a / pair_b: 两个变体                                 │
│  ├─ same_motif: LLM 判定                                     │
│  └─ similarity: 0-1 相似度                                   │
└──────────────────────────────────────────────────────────────┘
```

### 实体定义

| 实体 | 属性 | 不变约束 | 状态 |
|------|------|---------|------|
| **Motif** | title, description, weight(1-10), evidence[] | title 唯一; weight ≥ 1 | ✅ 稳定 |
| **SubMotif** | parent_motif, name, variants[] | 子类互斥; 各子类 variant ≥ 1 | 🟡 待确认（p11 发现"手势"有 2 子类） |
| **Variant** | motif, series, scene, desc | 每个 motif 在每个 series 中至多 1 variant | ✅ 稳定 |
| **Article** | id, series, name, path, text | — | ✅ 稳定 |
| **ExtractedMotif** | title, description, weight, evidence | 每篇文章 3-6 个 | 🟡 提取阈值未定（窗口/场景依赖） |
| **Gap** | type(covered/missing/weak), target_weight, extracted_weight | missing: extracted=0; weak: extracted < target×0.5 | ✅ 稳定 |
| **GapAttribution** | gap_types[], alternative_motif, reasoning | 支持多归因 | 🟡 gap_types 枚举待收敛 |
| **Suggestion** | direction(6种), text, paragraph_ref, reverse_risk | 反向方向需标注风险 | 🟡 "克制""反向"方向价值待验证 |
| **StyleDimension** | title, description, score(1-10), evidence | 11 个固定维度 | 🟡 跨场景可比较性存疑 |
| **StyleMotifLink** | weak_dimension, related_motif, confidence | 每个 motif 至多关联 2 个弱维度 | 🟡 仅 urban 系列验证 |

### 值对象

| 值对象 | 字段 |
|--------|------|
| CoverageReport | extracted_count, matched_count, coverage(0-1), matches[] |
| MotifChain | clusters[{motif_name, members[], reason}] |
| PairwiseEval | winners{specific, root_cause, motif_fit, natural, style_cover} |
| EvaluationScore | feasibility(1-5), motif_fit(1-5), naturalness(1-5), actionable(1-5) |

---

## 二、通用语言词典（Ubiquitous Language）

### 已确认术语（✅ 有实验支撑）

| 术语 | 英文 | 定义 | 验证实验 |
|------|------|------|---------|
| **母题** | Motif | 叙事中反复出现的主题元素。与主题不同：主题是"说什么"，母题是"怎么说" | p05 提取成功（覆盖 56-58%） |
| **变体** | Variant | 同一母题在不同作品/场景中的不同表现。如"手势先于语言"在都市表现为"擦头发"，校园为"擦眼泪" | p06 相似度矩阵 F1=100% |
| **母题吻合度** | Alignment | 约束生成后检测到的母题与目标的匹配程度（0-1） | p07 约束组 > 对照组 +20-45% |
| **母题覆盖率** | Coverage | 提取/生成的母题占目标母题的比例 | p05 去重后覆盖 56-75% |
| **缝隙** | Gap | 文章实际母题与目标母题库的偏差，含 covered/missing/weak | p08 缝隙检测与预期一致 |
| **缝隙归因** | Gap Attribution | 分析母题缺失的根本原因（场景不兼容/替代/遗漏） | p08 归因框架可用 |
| **风格-母题关联** | Style-Motif Link | 弱风格维度与缺失母题之间的因果关联 | p10 LLM 发现 2-3 个关联 |

### 待确认术语（🟡 有初步证据，需更多验证）

| 术语 | 英文 | 当前理解 | 需什么验证 |
|------|------|---------|-----------|
| **子母题** | SubMotif | "手势先于语言"可拆为"无意识触碰"和"保护性包裹"两个子类 | p06 层次聚类已确认；需验证子类在其他系列是否成立 |
| **母题约束力** | Motif Constraint Power | 具象母题（雨/论坛）约束力强，抽象母题（孤独/旁观者）约束力弱 | p07 约束力梯队已确认；可执行约束翻译后需重测 |
| **生成性 vs 分析性母题** | Generative vs Analytic Motif | 某些母题是分析性概念（读者推断），不适合直接作为生成约束 | p07 "孤独"覆盖率 0%；翻译为行为指令后待验证 |
| **改进方向价值** | Direction Value | 6 方向中 增强/转化 自然度高，借用有趣，克制有智慧，反向有风险 | p08 待人工评审方向间多样性 |
| **跨维度可比性** | Cross-Scene Comparability | 风格评分跨场景是否可比？T1 vs T3 的评分差异 | p10 发现跨场景评分可比性存疑 |
| **母题提取窗口** | Extraction Window | 前 3000 字是否足够？C3(KTV) 仅 25% 覆盖率 | 待做 1k/2k/3k/全文对比实验 |

### 已弃用术语（❌ 有实验证伪）

| 术语 | 弃用原因 | 替代 |
|------|---------|------|
| **keyword-map 匹配** | false positive/negative 严重 | embedding 余弦相似度 / LLM 语义判断 |
| **无监督母题聚类** | LLM 在盲测中无法自主重建 gallery 分类（ARI≈0.25） | 改为"有参照的 pair-wise 判定"模式 |
| **单句摘要母题匹配** | 粒度太粗，配对盲测 0% | 完整段落（300-500 字） |

### 关系定义

| 关系 | 源 → 目标 | 多重性 | 说明 |
|------|----------|--------|------|
| 提取 | Article → ExtractedMotif | 1 : 3-6 | 每篇文章提取 3-6 个母题 |
| 对照 | ExtractedMotif → Motif(GT) | N : M | 用语义相似度匹配 |
| 归属 | Variant → Motif | N : 1 | 多个变体属于同一母题 |
| 诊断 | StyleDimension → Motif | 1 : 0-1 | 一个弱维度对应至多一个缺失母题 |
| 改进 | Gap → Suggestion | 1 : 6 | 每个缝隙生成 6 方向建议 |
| 分层 | Motif → SubMotif | 1 : 1-2 | 一个母题含 1-2 个子类（p11 发现） |

---

## 三、模型验证状态

### ✅ 已验证的模型要素

| 模型要素 | 置信度 | 证据 |
|---------|--------|------|
| Motif 作为可提取的实体 | 高 | p05 单篇覆盖 56-58%，盲品聚类 79% |
| Motif 跨作品身份（pairwise 判定） | 高 | p06 F1=100%，同 0.839 vs 异 0.133 |
| Motif 作为生成约束 | 中 | p07 约束组 > 对照组 +20-45% |
| Gap 的三种分类 | 中 | p08 缝隙检测与 p05 已知覆盖一致 |
| 6 方向建议框架 | 中 | p08 各方向建议可区分 |
| 风格-母题关联存在性 | 中 | p10 LLM 发现部分人工标注关联 |

### 🟡 待验证的模型要素（按优先级排序）

| # | 模糊点 | 当前假设 | 验证方法 | 影响 |
|---|--------|---------|---------|------|
| **M1** | 母题是否有子类层级？ | "手势先于语言"可拆为"无意识触碰"和"保护性包裹" | p11 层次聚类 ✅ 已确认；需在其他 series/motif 上验证 | 模型需引入 SubMotif 实体 |
| **M2** | 母题提取的最小可靠窗口是多少？ | 前 2000 字可能不足，场景类型影响大 | p05 窗口敏感性实验：1k/2k/3k/全文对比 | 决定 API 的最小输入长度 |
| **M3** | 多篇联合提取的 ROI 何时饱和？ | 2 篇可能已接近峰值 | p05 联合提取 ROI：1/2/3/5 篇覆盖率增长曲线 | 决定"作者风格画像"需要多少篇文章 |
| **M4** | 抽象母题翻译为可执行约束后是否有效？ | 翻译后覆盖率从 0% 提升至 40-60% | p07 翻译后重测约束组吻合度 | 决定 motif.yaml 是否需要增加"生成性指令"字段 |
| **M5** | motif + style 联合约束是否 1+1 > 2？ | 可能更强，也可能相互稀释 | p07 4 组对比实验：无约束/仅 motif/仅 style/联合 | 决定产品中约束策略 |
| **M6** | 场景模板设计是否决定了母题覆盖率上限？ | 是——某些母题只在特定场景中出现 | p07 新增 4 个场景模板后重测覆盖率 | 决定场景模板库的设计原则 |
| **M7** | 改进建议的"克制""反向"方向是否有创作价值？ | 克制是最有智慧的"不建议"，反向是最有风险的 | p08 人工评审 18 条建议的方向间多样性 | 决定 6 方向框架是否作为产品功能保留 |
| **M8** | 组合改法是否优于单层改法？ | 组合 > 风格单层 or 母题单层 | p10 三组 pairwise 对比分析 | 决定产品的改法策略 |
| **M9** | 风格评分跨场景是否可比？ | 可能不可比——T3(成稿)评分低于 T1(初稿) | p10 跨场景评分一致性和相关性分析 | 决定风格评分是否可用于跨文章比较 |
| **M10** | "时间的两种用法"是否应该从 shared motif 中移除？ | 各项指标最差（sim=0.600, 聚类/配对全部失败） | p06 跨作品识别 + p11 层次聚类 | 决定 gallery 的母题粒度是否统一 |

---

## 四、模型完善计划

完善计划按**模型要素**组织，而非按实验模块。每项任务解决一个模型模糊点。

### 第 1 批：模型可信化（解决 M2, M3, M9）

| 模型要素 | 任务 | 涉及实验 | 产出 |
|---------|------|---------|------|
| Extraction Window (M2) | 对 C3(KTV) 等低覆盖率场景做 1k/2k/3k/全文 对比 | p05 窗口敏感性 | 最小可靠窗口参数 |
| Joint Extraction ROI (M3) | 在 1/2/3/5 篇样本量上测试覆盖率饱和点 | p05 联合提取 ROI | 作者风格画像所需最少文章数 |
| Cross-Scene Comparability (M9) | 分析 p10 风格评分的跨场景方差 vs 组内方差 | p10 跨场景一致性 | 风格评分是否可比较的结论 |

### 第 2 批：模型精细化（解决 M1, M4, M6）

| 模型要素 | 任务 | 涉及实验 | 产出 |
|---------|------|---------|------|
| Motif Hierarchy (M1) | 将 p11 层次聚类结果与 gallery 对比，确定 sub-motif 是否需要纳入模型 | p11 + gallery 对齐 | SubMotif 实体定义 |
| Abstract Motif Translation (M4) | 验证 p07 可执行约束翻译后的覆盖率提升 | p07 翻译后重测 | motif.yaml 是否需要"生成性指令"字段的决策 |
| Scene Template Coverage (M6) | 新增 4 场景后重测全母題覆盖率 | p07 场景模板验证 | 场景模板库设计原则 |

### 第 3 批：模型产品化（解决 M5, M7, M8, M10）

| 模型要素 | 任务 | 涉及实验 | 产出 |
|---------|------|---------|------|
| Combined Constraints (M5) | 4 组约束对比实验 | p07 联合约束 | 约束策略选择 |
| Direction Value (M7) | 18 条建议的人工评审（高/中/低分层抽样） | p08 人工评估 | 6 方向框架的保留/裁减决策 |
| Fix Strategy (M8) | p10 pairwise 对比的统计分析 | p10 改法对比 | 组合/风格/母题策略选择 |
| "时间的两种用法" 归队或移除 (M10) | 基于跨作品识别 + 层次聚类数据，决定该母题是否保留 | p06 + p11 综合 | gallery 母题粒度统一 |

### 第 4 批：模型工具化

| 任务 | 说明 | 依赖 |
|------|------|------|
| **CLI 工具** | `motif extract`, `motif suggest`, `motif analyze` | 第 1-3 批完成 |
| **Gallery API** | motif.yaml/style.yaml 的版本化读写接口 | SubMotif 实体确定后 |
| **motif-aware generation API** | 输入场景 + 母题约束 → 输出带一致性的文本 | 约束策略确定后 |

---

## 五、实验 → 模型映射矩阵

| 实验 | 验证的模型要素 | 关键指标 |
|------|-------------|---------|
| **p05 母题提取** | Motif 可提取性、Coverage 概念、Extraction Window | 覆盖率、盲品聚类率 |
| **p06 跨作品识别** | Variant 概念、Motif 跨作品身份、Motif Hierarchy | 相似度矩阵 F1、ARI |
| **p07 一致性检验** | Motif 约束力、Alignment 概念、Generative vs Analytic | 约束组/对照组差距、单母题覆盖率 |
| **p08 缝隙分析** | Gap 实体、GapAttribution、Suggestion 6 方向 | 缝隙识别准确率、方向间 Jaccard 距离 |
| **p10 风格改进** | StyleMotifLink、跨维度可比性、Fix 策略 | Jaccard 相似度、pairwise win counts |
| **p11 层次聚类** | SubMotif 层级、母题间距 | 簇纯度、簇内/簇间距离比 |

---

## 六、方向性决策（模型层面）

### 模型适用边界

| 决策 | 理由 |
|------|------|
| 母题在 **pairwise 判定模式** 下可用 | p06 F1=100% |
| 母题在 **无监督发现模式** 下不可用 | p06 ARI≈0.25 |
| 具象母题可作生成约束，抽象母题需翻译 | p07 "雨"80% vs "孤独"0% |
| 当前 3 层母题库（shared/urban/campus）的结构成立 | p11 7 个簇全部纯度高 |
| "手势先于语言"需引入子类 | p11 发现"无意识触碰"和"保护性包裹"两个子簇 |

### 开放问题

| 问题 | 当前立场 | 待了什么数据 |
|------|---------|------------|
| 模型是否需要 SubMotif 实体？ | 倾向需要，但需验证子类在更多 series 中成立 | p06 在 campus-only/urban-only 子集上重跑层次聚类 |
| 模型是否需要"生成性约束"字段？ | 倾向需要，但需验证翻译后的覆盖率提升 | p07 翻译后重测 |
| 风格评分是否可以跨场景比较？ | 倾向不可比，但需正式检验 | p10 方差分析 |
