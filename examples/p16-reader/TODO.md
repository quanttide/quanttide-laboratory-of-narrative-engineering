# p16 TODO

> 基于 README.md（实验设计）和 ROADMAP.md（执行优先级）分解为可执行任务。

---

## Phase I：核心假设验证

> 无层1依赖，纯 prompt。全部通过后才进入 Phase II。

### □ E4-0 — Prompt 操控性检验

**前置条件**：无（这是第一个实验）

- [ ] **0.1 创建目录结构**
  - `mkdir -p phase1 results`
- [ ] **0.2 定义画像配置文件**
  - 创建 `phase1/profiles.json`：P0–P5 六个画像的参数定义（openness/empathy/NFC/expertise/familiarity/time_pressure/purpose）
  - 包含 P0 无画像标记（参数全为 null）
- [ ] **0.3 实现 prompt 模板系统**
  - 创建 `phase1/prompt_templates.py`
  - 实现 `build_reader_self_description_prompt(profile) → str`（读者自述 prompt）
  - 实现 `build_evaluation_prompt(profile, text) → str`（评价 prompt，E4-1 复用）
  - 实现 `build_behavioral_anchor_prompt(profile_tag, text) → str`（行为锚定 fallback 版）
- [ ] **0.4 实现 E4-0 主流程**
  - 创建 `phase1/e4-0_manipulation.py`
  - 加载 `profiles.json`
  - 对 P0–P5 各调用 3 次读者自述 prompt（temperature=0.7），共 18 次 LLM 调用 → 保存原始输出到 `results/e4-0_raw.json`
  - embedding 化所有自述文本
  - 计算轮廓系数、P0 vs P1 余弦距离、P2 vs P4 余弦距离
  - 输出通过/不通过判定到 `results/e4-0_result.json`
- [ ] **0.5 结果分析**
  - 轮廓系数 ≥ 0.25？
  - P1 vs P0 余弦距离 ≥ 0.1？
  - P2 vs P4 距离 > P1 vs P0？
  - 如不通过 → 换行为锚定 prompt 重跑 0.4
- [ ] **0.6 门控判定**
  - 通过 → 进入 E4-1
  - 不通过（行为锚定后仍不通过）→ 项目终止，写入结论

---

### □ E4-1 — 读者画像分化验证

**前置条件**：E4-0 通过 ✅

**E4-1 Pilot（调用次数校准）**

- [ ] **1.1 编写 E4-1 pilot 脚本**
  - 创建 `phase1/e4-1_pilot.py`
  - 选取 P1（普通读者）和 P3（情感沉浸型），在单篇文本（4.1）上各跑 10 次（temperature=0.7）
  - 计算 ICC 和情感冲击评分的 Cohen's d
  - 输出 `results/e4-1_pilot.json`
- [ ] **1.2 确定正式实验调用次数**
  - 根据 pilot 的 ICC 和效应量，确定所需调用次数 `n_calls`
  - 如 ICC ≥ 0.50 且 d ≥ 0.5，n_calls=5 足够；否则上调

**E4-1 正式实验**

- [ ] **1.3 准备植入错误**
  - 对 6 篇测试文本（4.1、7.2、9.1、2.3、10.3、1.2）各植入 2 个语法错误 + 1 个事实矛盾
  - 创建 `phase1/planted_errors.json`：记录每篇文本的错误类型、位置和预期检出
- [ ] **1.4 实现 E4-1 主流程**
  - 创建 `phase1/e4-1_differentiation.py`
  - 5 画像（P1–P5）× 6 篇文本 × n_calls 次调用（temperature=0.7）
  - 每个调用的输出格式：
    ```json
    {
      "text_id": "4.1",
      "profile": "P2",
      "call_index": 0,
      "responses": {
        "logic_break": {"detected": true, "positions": ["第3段"]},
        "grammar_error": {"detected": false},
        "emotional_impact": 5,
        "reading_difficulty": 3,
        "structure_label": "有意留白",
        "aesthetic_grade": "A"
      }
    }
    ```
  - 保存到 `results/e4-1_raw.json`
- [ ] **1.5 分析：判别效度**
  - 计算 4 组对比的方向和效应量：
    - P2 vs P1：结构异常标注比例差（预期 ≥ 20%）
    - P3 vs P1：情感冲击 Cohen's d（预期 ≥ 0.5）
    - P4 vs P1：逻辑断裂召回率差（预期 ≥ 15%）
    - P5 vs P1：逻辑异常占比差（预期 ≥ 10%）
  - 输出 `results/e4-1_discriminant.json`
- [ ] **1.6 分析：定向效度**
  - 检查所有成立对比的方向是否与文献一致
  - 输出 `results/e4-1_directional.json`
- [ ] **1.7 分析：稳定效度**
  - 计算同一画像 × 文本组合的 ICC（≥ 0.50）
  - 输出 `results/e4-1_reliability.json`
- [ ] **1.8 分析：客观基线**
  - 检查各画像对植入错误的检出率（≥ 75%）
  - 输出 `results/e4-1_objective_baseline.json`
- [ ] **1.9 汇总 E4-1 结果**
  - 创建 `results/e4-1_summary.json`：4 项验证的通过/不通过
- [ ] **1.10 门控判定**
  - 全部 4 项通过 → 进入 E4-2
  - 任一未通过 → 项目终止或转为探索性研究

---

### □ E4-2 — 跨文本泛化与外部锚定

**前置条件**：E4-1 全部通过 ✅

- [ ] **2.1 实现泛化检验**
  - 创建 `phase1/e4-2_generalization.py`
  - 将 E4-1 的 6 篇文本分为 3 组（各 2 篇）
  - 3-fold CV：用 2 组训练简单分类器（如逻辑回归），在剩余 1 组上预测画像标签
  - 输出预测准确率到 `results/e4-2_generalization.json`
- [ ] **2.2 实现外部锚定**
  - 加载 E3 历史输出数据（路径：`../p09-aesthetic-review/results/`）
  - 计算 P1 评分 vs E3 评分的 Spearman ρ（审美判断）
  - 计算 P1 评分 vs E3 评分的 Kendall τ（情感冲击）
  - 输出到 `results/e4-2_anchoring.json`
- [ ] **2.3 汇总 E4-2 结果**
  - 创建 `results/e4-2_summary.json`
- [ ] **2.4 门控判定**
  - 全部通过 → **Phase I 通过**，进入 Phase II
  - 任一未通过 → 项目降级为"纯 prompt 模拟读者"，写入结论文档

---

## Phase II：系统集成与校准

> 仅在 Phase I 全部通过后启动。

### □ E4-3 — 层1自动化验证

**前置条件**：E1、E2 数据可用；认知负荷公式已定义

- [ ] **3.1 实现推理需求引擎**
  - 创建 `src/layer1/inference_demand.py`
  - 输入：文本段落 → 输出：每百字隐含信息密度
  - 方法：E2 阶段 I 产出 → 逻辑回归映射
- [ ] **3.2 实现工作记忆负载模块**
  - 创建 `src/layer1/working_memory.py`
  - 输入：句法树 + 名词链 → 输出：工作记忆过载概率
  - 公式：名词密度 × 嵌套从句深度
- [ ] **3.3 实现回溯重读预测模块**
  - 创建 `src/layer1/backtracking.py`
  - 输入：指代链 → 输出：高概率回溯位置
  - 公式：指代距离 × 歧义指数
- [ ] **3.4 实现情境模型构建模块**
  - 创建 `src/layer1/situation_model.py`
  - 输入：全文 RST 树 + 实体网络 → 输出：五维度连贯性评分（时间/空间/人物/因果/意图）
- [ ] **3.5 对齐验证**
  - 创建 `src/layer1/validation.py`
  - 逐项对比 E2 手动标注：
    - 推理需求密度：Spearman ρ ≥ 0.70
    - 工作记忆过载：AUC ≥ 0.75
    - 回溯重读：命中率 ≥ 60%
    - 情境模型五维度：ICC ≥ 0.65
  - 输出 `results/e4-3_validation.json`
- [ ] **3.6 门控判定**
  - 全部 4 项通过 → 进入 E4-4
  - 未通过 → 修复公式或实现

---

### □ E4-4 — 权重映射标定

**前置条件**：E4-3 通过 ✅

- [ ] **4.1 实现 pairwise 权重比推断**
  - 创建 `src/layer2/weight_ratios.py`
  - 对每个画像 Px，以层1 认知负荷指标为自变量、E4-1 模拟评价为因变量，做标准化线性回归
  - 计算权重比 w₁:w₂:w₃:w₄
  - bootstrapping（1000 次）估计 95% CI
  - 输出 `results/e4-4_weight_ratios.json`
- [ ] **4.2 实现参数 → 权重比映射**
  - 创建 `src/layer2/weight_mapping.py`
  - 以 5 个画像（P1–P5）为观测点，拟合每个权重比随画像参数的单调趋势
  - 正则化线性回归（特征数 ≤ 3）
- [ ] **4.3 验证**
  - 权重比 CI 宽度 < 0.30？
  - 预期单调关系成立比例 ≥ 3/4？
  - 跨文本 ICC ≥ 0.50？
  - 输出 `results/e4-4_summary.json`
- [ ] **4.4 门控判定**
  - 全部通过 → 进入 E4-5
  - 未通过 → 简化映射方案（如固定等权）

---

### □ E4-5 — 端到端集成验证

**前置条件**：E4-3、E4-4 通过 ✅

- [ ] **5.1 实现全链路管线**
  - 创建 `src/pipeline.py`
  - 层1 → 层2 → 层3 串联
  - 输入：文本 ID + 画像参数 → 输出：评价分布
- [ ] **5.2 在未见文本上运行**
  - 8 篇未见文本（14 − 6 = 8），每篇 × 3 次全链路调用
- [ ] **5.3 验证**
  - 全链路 ICC ≥ 0.50？
  - 与 E4-1 直接 prompt 的 Spearman ρ ≥ 0.60？
  - ANOVA 画像主效应 p < 0.05？
  - 输出 `results/e4-5_summary.json`
- [ ] **5.4 项目收尾**
  - 撰写实验总报告到 `CONCLUSION.md`
  - 清理中间文件

---

## 探索性方向 (P3)

> 非门控，优先级低于 Phase I/II。

### □ 探索 ⑦：抽象母题的读者感知差异

**前置条件**：E4-1 数据可用

- [ ] 7.1 将 E4-1 的 6 篇文本按"具象母题 / 抽象母题"分类（参考 p07 分类）
- [ ] 7.2 比较两类文本上画像间的效应量大小
- [ ] 7.3 输出 `results/p3_abstraction_effect.json`

### □ 探索 ⑨：temperature 对分化效度的影响

**前置条件**：E4-1 pilot 脚本可用

- [ ] 9.1 用 P2 vs P5，在单篇文本上以 temperature=0.3/0.5/0.7/1.0 各跑 5 次
- [ ] 9.2 比较各 temperature 下的 ICC 和分化效应量
- [ ] 9.3 输出 `results/p3_temperature_analysis.json`

---

## 项目交付物清单

- [ ] `phase1/profiles.json` — 画像参数定义
- [ ] `phase1/prompt_templates.py` — prompt 模板（读者自述 + 评价 + 行为锚定）
- [ ] `phase1/planted_errors.json` — 植入错误记录
- [ ] `phase1/e4-0_manipulation.py` — E4-0 主流程
- [ ] `phase1/e4-1_pilot.py` — E4-1 调用次数校准
- [ ] `phase1/e4-1_differentiation.py` — E4-1 主流程
- [ ] `phase1/e4-2_generalization.py` — E4-2 泛化与锚定
- [ ] `src/layer1/inference_demand.py` — 推理需求引擎
- [ ] `src/layer1/working_memory.py` — 工作记忆负载
- [ ] `src/layer1/backtracking.py` — 回溯重读预测
- [ ] `src/layer1/situation_model.py` — 情境模型
- [ ] `src/layer1/validation.py` — 层1对齐验证
- [ ] `src/layer2/weight_ratios.py` — 权重比推断
- [ ] `src/layer2/weight_mapping.py` — 参数→权重映射
- [ ] `src/pipeline.py` — 全链路管线
- [ ] `results/e4-0_result.json` — E4-0 结果
- [ ] `results/e4-1_summary.json` — E4-1 汇总
- [ ] `results/e4-2_summary.json` — E4-2 汇总
- [ ] `results/e4-3_validation.json` — E4-3 验证
- [ ] `results/e4-4_summary.json` — E4-4 汇总
- [ ] `results/e4-5_summary.json` — E4-5 汇总
- [ ] `CONCLUSION.md` — 实验总报告
