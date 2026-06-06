# 可复用组件

从 10 个叙事工程实验中提取的可复用 Python 组件，按功能分类。

## 母题提取

| 组件 | 来源 | 功能 | 成熟度 |
|------|------|------|:---:|
| `motif_extractor` | p05 run.py | 从文本中提取叙事母题（3-6 个），每个附 weight + evidence | 🟡 |
| `motif_ground_truth_loader` | p05 run.py | 加载 gallery 三层 motif.yaml（跨系列/系列专属）作为基准 | 🟢 |
| `motif_coverage_evaluator` | p05 run.py | 提取结果 vs 人工标注的覆盖率计算 | 🟡 |
| `motif_blind_clusterer` | p05 run.py | Blinded 母题聚类归因（3 轮取平均） | 🟡 |

## 母题跨作品识别

| 组件 | 来源 | 功能 | 成熟度 |
|------|------|------|:---:|
| `cross_work_similarity` | p06 run.py | 跨作品场景对的母题相似度判定（pairwise F1=100%） | 🟢 |
| `motif_chain_reconstructor` | p06 run.py | 无监督母题链重构（14 场景自由聚类） | 🟡 |
| `blind_pairing_tester` | p06 run.py | 配对盲测——匿名场景两两配对母题 | 🟢 |
| `cross_work_mirror_pool` | p06 run.py | 跨作品母题变体素材库（7 母题 × 2 系列） | 🟢 |

## 母题一致性

| 组件 | 来源 | 功能 | 成熟度 |
|------|------|------|:---:|
| `motif_constrained_generator` | p07 run.py | 以 motif.yaml 为约束生成多场景文本 | 🟢 |
| `motif_alignment_detector` | p07 run.py | 检测生成文本中的目标母题覆盖 | 🟡 |
| `motif_constraint_analyzer` | p07 run.py | 单母题约束力分析（覆盖率梯队） | 🟢 |

## 母题缝隙分析

| 组件 | 来源 | 功能 | 成熟度 |
|------|------|------|:---:|
| `gap_reporter` | p08 run.py | 初稿母题覆盖 vs 目标母题的缺口报告 | 🟢 |
| `gap_attributor` | p08 run.py | 缝隙归因（场景不兼容/替代母题/真正遗漏） | 🟡 |
| `six_direction_suggester` | p08 run.py | 6 方向改进建议生成（增强/引入/借用/转化/克制/反向） | 🟢 |
| `suggestion_evaluator` | p08 run.py | 建议质量 4 维度自动评估 | 🟢 |

## 风格与审美

| 组件 | 来源 | 功能 | 成熟度 |
|------|------|------|:---:|
| `style_yaml_loader` | p09 run.py | 加载 style.yaml（11 维度 + clues + tensions + excerpts） | 🟢 |
| `style_prompt_builder` | p09 run.py | 构建风格评审 prompt（维度定义 + 样本场景） | 🟢 |
| `style_reviewer` | p09 run.py | 逐维度 1-10 评分 + 原文证据 + tension 检测 | 🟢 |
| `style_alignment_evaluator` | p09 run.py | 方向匹配率 + Spearman's ρ + tension 发现统计 | 🟢 |
| `cross_series_tester` | p09 run.py | 跨系列审美转移测试（含 genre_fit 标注） | 🟡 |

## 母题+风格合成

| 组件 | 来源 | 功能 | 成熟度 |
|------|------|------|:---:|
| `two_step_diagnoser` | p10 run.py | 两步风格-母题关联诊断（自由推断→匹配母题库） | 🟢 |
| `style_motif_link_learner` | p10 run.py | 学习风格维度↔母题的映射矩阵 | 🟢 |
| `pairwise_blind_evaluator` | p10 run.py | Blind pairwise 改法质量对比 | 🟢 |

## 通用工具

| 组件 | 来源 | 功能 | 成熟度 |
|------|------|------|:---:|
| `call_llm` / `call_llm_text` | p05-p10 | LLM API 调用封装（DeepSeek, 含 retry + JSON 验证） | 🟢 |
| `clean_json` | p05-p10 | LLM 输出清理（markdown 代码块剥离） | 🟢 |
| `load_yaml` / `load_motif_yaml` | p05-p10 | YAML 加载（含格式修复） | 🟢 |
| `read_article_text` | p05-p10 | 去除 front matter 的文本读取 | 🟢 |

---

**成熟度说明**：🟢 稳定可复用 / 🟡 需解耦抽象 / 🔴 实验专用
