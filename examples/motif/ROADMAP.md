# Motif 领域模型 — 改进路线图

## 当前质量评估

```
类型安全     ████████░░  8/10  ✅ 强项
术语一致性   █████████░  9/10  ✅ 强项
行为完整性   ██░░░░░░░░  3/10  ❌ 贫血模型
封装性       ████░░░░░░  4/10  ❌ 序列化暴露内部
聚合边界     ████░░░░░░  4/10  ⚠️ 定义了未执行
统一序列化   ██░░░░░░░░  2/10  ❌ 3 种方式共存
━━━━━━━━━━━━━━━━━━━━━━━━━━━
综合          █████░░░░░  5/10
```

---

## 改进计划

### 第 1 批：注入行为 — 从贫血模型到富模型

给实体添加领域行为方法，将散落在 services/ 和 examples/ 中的逻辑收归模型本身。

| 实体 | 新增行为 | 消除的散落代码 |
|------|---------|-------------|
| **Motif** | `is_strong()`, `is_weak()`, `matches_title()`, `merge()` | `t in et.title or et.title in t`（p08/p05 共 3 处） |
| **GapItem** | `is_missing()`, `is_weak()`, `to_suggestion_target()` | 类型判断散落在 `main()` 中 |
| **GapReport** | `fixable_gaps()`, `coverage_rate()`, `summary()` | `gap_report.missing + gap_report.weak`（p08 多处） |
| **Suggestion** | `is_safe()`, `is_risky()` | `reverse_risk` 的比较逻辑 |
| **Article** | `read_text()`, `extract_motifs()` | `read_article_text(path)` 游离函数 |
| **Gallery** | `motifs_for()`, `dimensions_for()` | `gt_dict` 桥接层（p05） |
| **Variant** | `series_name()` | `"都市言情" if s == "urban" else "校园言情"`（p06 3 处） |

**工作量**：~2h | **影响**：消除 ~15 处散落逻辑，模型可自述

---

### 第 2 批：统一序列化

消除 `vars()` / `motifs_to_dicts()` / 手写 dict 三种并存的序列化方式。

```
当前状态：
  vars(m)                    — 5 处（p05/p06/p07/p08/p10）
  motifs_to_dicts(m)         — 2 处（p10）
  [vars(p) for p in pairs]  — 2 处（p06）
  手写 dict 构造            — 8+ 处（所有 example 文件）

目标状态：
  dataclasses.asdict(obj)   — 统一替换所有 vars() 调用
  converter.to_*()          — 保留幂等反向转换
  json.dumps(..., cls=DataclassEncoder) — 自动序列化
```

具体步骤：

1. 新增 `DataclassJSONEncoder(json.JSONEncoder)` — `default` 中调用 `dataclasses.asdict`
2. 修改 `cache_or_compute` 内部使用该 encoder
3. 全局替换 `vars(m)` → `dataclasses.asdict(m)`
4. 删除 `motifs_to_dicts()` / `pairs_to_dicts()` / `dims_to_dicts()` 等重复函数

**工作量**：~1h | **影响**：消除 ~20 处序列化代码，统一出入口

---

### 第 3 批：封装修复 — 消除外部 dict 访问

| 位置 | 当前 | 修复后 |
|------|------|--------|
| `p05/compare_with_ground_truth` | `gt: dict` → `gt.get("urban", {})` | `gt: MotifProfile` → `gt.urban` |
| `p05/gt_dict` 桥接 | 构造中间 dict | 直接传 `MotifProfile` |
| `p08/gap_attribution` | `missing_motif: dict` → `["title"]` | `missing_motif: GapItem` → `.title` |
| `p08/evaluate_suggestions` | `suggestions: list[dict]` | `suggestions: list[Suggestion]` |
| `p10/evaluate_pairwise` | 返回裸 `dict` | 返回 `PairwiseResult` dataclass |
| `SCENE_TEMPLATES` 中母题列表 | `list[dict]` 手写 | `list[Motif]` 构造 |

**工作量**：~1h | **影响**：消除所有 `["key"]` 外部 dict 访问

---

### 第 4 批：补齐缺失领域概念

| 概念 | 形态 | 解决什么 |
|------|------|---------|
| **Series** | `class Series(Enum): URBAN = "urban"; CAMPUS = "campus"` | Literal 只在类型检查时生效，Enum 运行时也防错 |
| **SimilarityThreshold** | `SIMILARITY_CUTOFF: float = 0.7` 常量 | 消除 ~5 处 `0.7` 魔术数字 |
| **ExperimentContext** | `@dataclass ExperimentContext: gallery_version, llm_params, timestamp` | 实验结果可复现 |
| **PromptTemplate** | `@dataclass PromptTemplate: name, params, rendered` | prompt 加载纳入领域模型 |
| **PairwiseWinners** | `@dataclass PairwiseWinners: specific, root_cause, ...` | 替代 `evaluate_pairwise` 的裸 dict 返回 |
| **WeakDimension** | `@dataclass WeakDimension: title, score, note` | 替代 `{"dimension":"...", "score": 5}` 散装 dict |

**工作量**：~1.5h | **影响**：消除 ~10 处魔术值 + 裸 dict

---

### 第 5 批：聚合边界执行

`ArticleAnalysis` 已定义但未使用。改造管线使其成为真正的聚合根：

```python
# 目标使用方式：
analysis = ArticleAnalysis(article=article)
analysis = extract_motifs_into(analysis)    # 返回 analysis，内部追加 motifs
analysis = compute_gaps_for(analysis)       # 返回 analysis，内部赋值 gap_report
analysis = generate_fixes_for(analysis)     # 返回 analysis，内部赋值 suggestions

# analysis 可直接 JSON 序列化（全部在聚合中）
save_analysis(analysis)
```

当前散落的关联：

```python
# p05: 3 个游离 dict
single_results[aid] = {...}
joint_results[series] = {...}
comparison[level_name] = {...}

# p08: 3 个游离 dict
all_gaps[art["id"]] = gap_report
all_suggestions[art["id"]] = art_suggestions
all_evaluations[art["id"]] = art_evaluations

# p10: 3 个游离 dict
all_diagnoses[aid] = diagnoses
all_fixes[aid] = art_fixes
all_evaluations[aid] = art_evals
```

全部统一为 `analyses: dict[str, ArticleAnalysis]`。

**工作量**：~2h | **影响**：聚合边界从文档走向代码强制执行

---

## 执行顺序

```
第 1 批（行为注入） ──→ 第 2 批（序列化统一） ──→ 第 3 批（封装修复）
                                                        │
                                                        ▼
                                              第 4 批（缺失概念）
                                                        │
                                                        ▼
                                              第 5 批（聚合执行）
```

依赖关系：1→2→3 是线性依赖，4 和 5 可并行（依赖 3 完成）。

---

## 验收标准

| 批次 | 验收条件 |
|------|---------|
| 1 | `Motif("x", "d", 9).is_strong()` → True；`compute_gap_report` 中无 `t in et.title` |
| 2 | `json.dumps(obj, cls=DataclassEncoder)` 可序列化任意模型对象；`vars(m)` 在代码中 0 处 |
| 3 | `grep '\["key"\]' examples/` 无命中（除 ARTICLES 等纯数据） |
| 4 | `Series.URBAN.value == "urban"`；`SIMILARITY_CUTOFF == 0.7` |
| 5 | `all_gaps` / `all_suggestions` / `all_evaluations` 合并为 `analyses: dict[str, ArticleAnalysis]` |

---

## 已知不改

| 方向 | 理由 |
|------|------|
| ❌ ORM 持久化 | 实验数据以 JSON 文件存储，无数据库需求 |
| ❌ 事件溯源 | 无跨实体的长事务 |
| ❌ 领域服务与模型解耦测试 | 当前无测试框架，引入后追加 |
| ❌ 全文检索 | 母题分析面向结构化元数据，非全文搜索 |
