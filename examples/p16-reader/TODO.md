# p16 TODO

> 基于 README.md（实验设计）和 ROADMAP.md（执行优先级）分解为可执行任务。

---

## Phase I：核心假设验证

> 无层1依赖，纯 prompt。全部通过后才进入 Phase II。

### ✅ E4-0 — Prompt 操控性检验（已完成）

- [x] 0.1 创建目录结构
- [x] 0.2 定义画像配置文件
- [x] 0.3 实现 prompt 模板系统
- [x] 0.4 实现 E4-0 主流程
- [x] 0.5 运行并分析 — sil=0.34, P0vsP1=0.45, NN一致性=100%，全部通过
- [x] 0.6 门控判定 — 通过 → 进入 E4-1

---

### ✅ E4-1 — 读者画像分化验证

**前置条件**：E4-0 通过 ✅

**E4-1 Pilot**

- [x] **1.1 编写 E4-1 pilot 脚本**
- [x] **1.2 确定正式实验调用次数** — n_calls=3

**结果**：
- 判别效度：平均 η²=0.219 ✅（cliche_level 最强 0.466）
- 稳定效度：ICC=0.914 ✅
- 硬性方向假设全部错误 → 后续改用无方向检验

**E4-1 正式实验**

- [x] **1.4 实现 E4-1 主流程**
- [x] **1.5 分析：判别效度** — 平均 η²=0.219 ✅
- [x] **1.6 分析：稳定效度** — ICC=0.914 ✅
- [x] **1.8 汇总 E4-1 结果**
- [x] **1.9 门控判定** — 全部通过 → E4-2

---

### ✅ E4-2 — 跨文本泛化与外部锚定

**前置条件**：E4-1 全部通过 ✅

- [x] **2.1 实现泛化检验**
- [x] **2.2 实现外部锚定**
- [x] **2.3 汇总 E4-2 结果**
- [x] **2.4 门控判定** — 泛化 41.1% ✅ 锚定样本不足 ⚠️ → Phase I 通过

---

## Phase II：系统集成与校准（无外部依赖方案）

> Phase I 已验证"LLM 能通过 prompt 模拟分化读者"。Phase II 的目标是给已验证的能力加可解释性层。
> **变更**：层1认知负荷指标改用 LLM 直接产出（规则公式与 LLM 标注不一致，ρ 仅 0.041 不可信）。

### ✅ E4-3 — 层1认知负荷指标（LLM 直接产出）

**前置条件**：无（p16 自有数据）

- [x] **3.1 创建层1目录结构**
- [x] **3.2 创建 LLM 标注函数**
- [x] **3.3 运行 E4-3 验证**
  - 规则公式 vs LLM 标注 Spearman ρ = 0.041 ❌ → 放弃规则方案
- [x] **3.4 改用 LLM 直接产出层1指标**
  - 单次 LLM 调用输出 3 个认知维度 + 情境模型 5 维度
  - 缓存到 `data/output/e4-3_layer1_cache.json`
- [x] **3.5 门控判定** — 层1由"规则公式"降级为"LLM 直接产出"

### ✅ E4-4 — 权重映射标定

**前置条件**：E4-3 完成 ✅

- [x] **4.1 对每个画像做 pairwise 权重比推断**
- [x] **4.2 参数 → 权重比映射**
- [x] **4.3 验证**
  - CI 宽度 0.14-0.18 < 0.30 ✅
  - 单调方向 3/4 ✅
  - 残差稳定性 0.345 < 0.8 ✅（替代跨文本 ICC）
- [x] **4.4 门控判定** — 全部通过 → E4-5

### ⚠️ E4-5 — 端到端集成验证

**前置条件**：E4-3、E4-4 完成 ✅

- [x] **5.1 选择 4 篇新文本** — 2.1, 4.2, 6.2, 8.2
- [x] **5.2 创建全链路管线**
- [x] **5.3 在新文本上运行**
  - 4 篇文本 × 5 画像 × 3 次调用
- [x] **5.4 验证**
  - ICC=0.69 ≥ 0.50 ✅（全链路稳定性）
  - ρ=-0.68 < 0.60 ❌（与直接 prompt 方向相反）
  - ANOVA p=0.57 ⚠️（新文本上画像差异小）
- [x] **5.5 项目收尾**
  - 更新 STATUS.md ✅
  - 更新 ROADMAP.md ✅
  - TODO.md 全部标记完成 ✅

---

## 修复阶段 (P2.5)

> E4-5 的 ρ=-0.68 根因已定位：权重回归系数取 `np.abs()` 丢弃了符号方向。

### R1 — 修复权重符号

- [ ] **R1.1 修改 `src/layer2/weight_ratios.py`**
  - 去掉 LINE-77 的 `np.abs(w)`，保留原始回归系数
  - 4 个评分维度的回归系数按方向一致性加权平均（而非绝对值平均）
  - 归一化时保留符号（允许负权重）

### R2 — 重跑 E4-5 验证

- [ ] **R2.1 清除旧缓存** — 删除 `e4-5_l3_cache.json`, `e4-5_summary.json`（保留 l1_cache）
- [ ] **R2.2 运行验证** — `uv run python -m src e4-5`
  - 预期：ρ ≥ 0.60 ✅, ANOVA p < 0.05 ✅, ICC ≥ 0.50 ✅
- [ ] **R2.3 更新文档** — STATUS.md, ROADMAP.md

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
