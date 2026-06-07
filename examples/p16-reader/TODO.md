# p16 TODO

> 基于 README.md（实验设计）和 ROADMAP.md（执行优先级）分解为可执行任务。

---

## Phase I：核心假设验证

> 无层1依赖，纯 prompt。全部通过后才进入 Phase II。

### ✅ E4-0 — Prompt 操控性检验（已完成）

- [x] 0.1 创建目录结构
- [x] 0.2 定义画像配置文件 — `data/input/profiles.json`（5 个具名用户画像 + P0 基线）
- [x] 0.3 实现 prompt 模板系统 — `src/phase1/prompt_templates.py`
- [x] 0.4 实现 E4-0 主流程 — `src/phase1/e4_0_manipulation.py`
- [x] 0.5 运行并分析 — sil=0.34, P0vsP1=0.45, NN一致性=100%，全部通过
- [x] 0.6 门控判定 — 通过 → 进入 E4-1

---

### □ E4-1 — 读者画像分化验证

**前置条件**：E4-0 通过 ✅

**E4-1 Pilot（调用次数校准）**

- [ ] **1.1 编写 E4-1 pilot 脚本**
  - 创建 `src/phase1/e4_1_pilot.py`
  - 选取 P1（甜宠少女）和 P3（资深老书虫），在单篇文本（4.1）上各跑 10 次（temperature=0.3）
  - 计算 ICC 和文笔评分的 Cohen's d
  - 输出 `data/output/e4-1_pilot.json`
- [ ] **1.2 确定正式实验调用次数**
  - 根据 pilot 的 ICC 和效应量，确定所需调用次数 `n_calls`

**E4-1 正式实验**

- [ ] **1.3 准备植入错误**
  - 对 6 篇测试文本（4.1、7.2、9.1、2.3、10.3、1.2）各植入 2 个语法错误 + 1 个事实矛盾
  - 填写 `data/input/planted_errors.json`
- [ ] **1.4 实现 E4-1 主流程**
  - 创建 `src/phase1/e4_1_differentiation.py`
  - 5 画像（P1–P5）× 6 篇文本 × n_calls 次调用（temperature=0.3）
  - 评价项：文笔评分 1-7、情感冲击 1-7、角色真实感 1-7、套路痕迹 1-5、逻辑断裂检测、语法错误检测、审美等级
- [ ] **1.5 分析：判别效度**
  - P2 > P1 文笔评分（预期 ≥ +1.0）
  - P5 > P1 角色真实感评分（预期 ≥ +1.0）
  - P4 < P1 情感冲击评分（预期 ≤ -0.5）
  - P3 > P2 套路识别率（预期 ≥ +20%）
- [ ] **1.6 分析：稳定效度**
  - 同一画像 × 文本组合的 ICC ≥ 0.50
- [ ] **1.7 分析：客观基线**
  - 各画像对植入错误的检出率 ≥ 75%
- [ ] **1.8 汇总 E4-1 结果**
  - 创建 `data/output/e4-1_summary.json`
- [ ] **1.9 门控判定**
  - 全部通过 → E4-2
  - 任一未通过 → 项目终止或转为探索性研究

---

### □ E4-2 — 跨文本泛化与外部锚定

**前置条件**：E4-1 全部通过 ✅

- [ ] **2.1 实现泛化检验**
  - 创建 `src/phase1/e4_2_generalization.py`
  - 将 E4-1 的 6 篇文本分为 3 组（各 2 篇）
  - 3-fold CV：用 2 组训练简单分类器，在剩余 1 组上预测画像标签
  - 输出预测准确率到 `data/output/e4-2_generalization.json`
- [ ] **2.2 实现外部锚定**
  - 加载 E3 历史输出
  - 计算 P1 评分 vs E3 评分的 Spearman ρ（审美判断）
  - 计算 P1 评分 vs E3 评分的 Kendall τ（情感冲击）
  - 输出到 `data/output/e4-2_anchoring.json`
- [ ] **2.3 汇总 E4-2 结果**
  - 创建 `data/output/e4-2_summary.json`
- [ ] **2.4 门控判定**
  - 全部通过 → **Phase I 通过**，进入 Phase II
  - 任一未通过 → 项目降级为"纯 prompt 模拟读者"

---

## Phase II：系统集成与校准（无外部依赖方案）

> Phase I 已验证"LLM 能通过 prompt 模拟分化读者"。Phase II 的目标是给已验证的能力加可解释性层。
> **关键变更**：层1验证不依赖 E1/E2 手动标注，改用 LLM 自身作为金标准。

### □ E4-3 — 层1认知负荷指标实现与自验证

**前置条件**：无（p16 自有数据）

- [ ] **3.1 创建层1目录结构**
  - 创建 `src/layer1/__init__.py`
  - 创建 `src/layer1/inference_demand.py` — 推理需求密度（规则驱动）
  - 创建 `src/layer1/working_memory.py` — 工作记忆负载（规则驱动）
  - 创建 `src/layer1/backtracking.py` — 回溯重读预测（规则驱动）
  - 创建 `src/layer1/situation_model.py` — 情境模型五维度（规则驱动）
- [ ] **3.2 创建 LLM 标注函数**
  - 创建 `src/layer1/llm_labels.py` — LLM 对逐句标注推理需求/阅读难度/回读概率/连贯性
- [ ] **3.3 创建验证入口**
  - 创建 `src/layer1/validate.py` — 对 6 篇 Phase I 文本，公式 vs LLM 标注的 Spearman ρ
  - 成功标准：4 项 ρ 全部 ≥ 0.60
- [ ] **3.4 运行 E4-3**
  - 更新 `src/__main__.py` 注册 `e4-3`
  - 运行 `python -m src e4-3`
  - 输出 `data/output/e4-3_summary.json`
- [ ] **3.5 门控判定**
  - 全部通过 → E4-4
  - 任一未通过 → 调试公式后重试；仍不过则跳过（层1降级为实验性功能）

### □ E4-4 — 权重映射标定

**前置条件**：E4-3 完成 ✅

- [ ] **4.1 对每个画像做 pairwise 权重比推断**
  - 创建 `src/layer2/weight_ratios.py`
  - 自变量：层1 4 个认知负荷指标（E4-3 产出）
  - 因变量：E4-1 的 4 个评分维度
  - 输出各画像的权重比 w₁:w₂:w₃:w₄
- [ ] **4.2 参数 → 权重比映射**
  - 创建 `src/layer2/weight_mapping.py`
  - 5 个画像作观测点，线性拟合单调趋势
- [ ] **4.3 验证**
  - Bootstrapping CI 宽度 < 0.30
  - 单调方向 ≥ 3/4
  - 跨文本 ICC ≥ 0.50
  - 输出 `data/output/e4-4_summary.json`
- [ ] **4.4 门控判定**
  - 全部通过 → E4-5
  - 任一未通过 → 简化权重模型（降为 2-3 个主线维度）

### □ E4-5 — 端到端集成验证

**前置条件**：E4-3、E4-4 完成 ✅

- [ ] **5.1 选择 4 篇新文本**
  - 从 assets/fiction 选非 4.1/7.2/9.1/2.3/10.3/1.2 的文本
- [ ] **5.2 创建全链路管线**
  - 创建 `src/pipeline.py`
  - 层1 → 层2（加权）→ 层3（聚合 P1-P5 评价分布）
- [ ] **5.3 在新文本上运行**
  - 4 篇文本 × 5 画像 × 3 次调用
- [ ] **5.4 验证**
  - ICC ≥ 0.50（全链路稳定性）
  - ρ ≥ 0.60（与直接 prompt 一致）
  - ANOVA p < 0.05（画像主效应）
  - 输出 `data/output/e4-5_summary.json`
- [ ] **5.5 项目收尾**
  - 更新 STATUS.md Phase II 部分
  - 更新 ROADMAP.md
  - 创建 `CONCLUSION.md` 或确认 STATUS.md 已覆盖

---

## 探索性方向 (P3)

### □ 探索 ⑥：抽象母题的读者感知差异

- [ ] 6.1 将 E4-1 的 6 篇文本按"具象母题 / 抽象母题"分类
- [ ] 6.2 比较两类文本上画像间的效应量大小
- [ ] 6.3 输出 `data/output/p3_abstraction_effect.json`

### □ 探索 ⑦：temperature 对分化效度的影响

- [ ] 7.1 P2 vs P5 在 temperature=0.3/0.5/0.7/1.0 各跑 5 次
- [ ] 7.2 比较 ICC 和分化效应量
- [ ] 7.3 输出 `data/output/p3_temperature_analysis.json`

---

## 项目交付物清单

- [x] `data/input/profiles.json` — 画像定义（5 个具名用户画像）
- [x] `data/input/planted_errors.json` — 植入错误记录（待填写）
- [x] `src/phase1/prompt_templates.py` — prompt 模板
- [x] `src/phase1/e4_0_manipulation.py` — E4-0 主流程 ✅
- [x] `data/output/e4-0_result.json` — E4-0 结果
- [ ] `src/phase1/e4_1_pilot.py` — E4-1 pilot
- [ ] `src/phase1/e4_1_differentiation.py` — E4-1 主流程
- [ ] `src/phase1/e4_2_generalization.py` — E4-2 泛化
- [ ] `src/layer1/inference_demand.py` — 推理需求引擎
- [ ] `src/layer1/working_memory.py` — 工作记忆负载
- [ ] `src/layer1/backtracking.py` — 回溯重读预测
- [ ] `src/layer1/situation_model.py` — 情境模型
- [ ] `src/layer1/validation.py` — 层1对齐验证
- [ ] `src/layer2/weight_ratios.py` — 权重比推断
- [ ] `src/layer2/weight_mapping.py` — 参数→权重映射
- [ ] `src/pipeline.py` — 全链路管线
- [ ] `data/output/e4-1_summary.json`
- [ ] `data/output/e4-2_summary.json`
- [ ] `data/output/e4-3_validation.json`
- [ ] `data/output/e4-4_summary.json`
- [ ] `data/output/e4-5_summary.json`
- [ ] `CONCLUSION.md`
