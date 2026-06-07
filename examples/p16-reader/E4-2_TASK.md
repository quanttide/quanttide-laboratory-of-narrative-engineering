# E4-2 任务：跨文本泛化与外部锚定

## 背景

E4-1（读者画像分化验证）已通过（平均 η²=0.219, ICC=0.914），证明 LLM 能通过 prompt 产生分化、稳定的读者画像评价。现在是 Phase I 的最后一个实验。

## 任务目标

实现并运行 E4-2，验证两件事：
1. **跨文本泛化**：分化效应在未见文本上是否依然成立
2. **外部锚定**：模拟读者评分与 E3（美学评审）的既有输出是否具有可解释的关联

## 数据结构参考

### E4-1 原始数据（`data/output/e4-1_raw.json`）
每条记录结构：
```json
{
  "writing_quality": int 1-7,
  "emotional_impact": int 1-7,
  "character_realism": int 1-7,
  "cliche_level": int 1-5,
  "reading_difficulty": int 1-5,
  "logic_break": {"detected": bool, "positions": [...]},
  "structure_label": "正常" / "逻辑断裂" / "有意留白",
  "aesthetic_grade": "A" / "A-" / "B" / "C",
  "profile": "P1" ... "P5",
  "text_id": "4.1" / "7.2" / "9.1" / "2.3" / "10.3" / "1.2",
  "call": 0..2
}
```

### E3 美学评审数据（`examples/p09-aesthetic-review/results/full_report.json`）
```json
{
  "scores": {
    "aesthetic": {
      "T1": {"dimension_scores": [{"dimension": "...", "score": 1-10}, ...]},
      "T2": {...},
      "T3": {...},
      "T4": {...}
    },
    "general": { "T1": {...}, ... },
    ...
  }
}
```

E3 有 4 篇文本（T1-T4），每篇有 10 个维度的评分（1-10）。p16 有 6 篇文本（4.1, 7.2, 9.1, 2.3, 10.3, 1.2）。
注意：E3 的文本 ID（T1-T4）和 p16 的文本 ID（4.1, 7.2, etc）不一样——E3 只评测了 14 篇中的 4 篇，其中 **T2 = "职场言情/1_1_咖啡厅重逢.md" = p16 的 "4.1"**（从 T2 的描述 "咖啡厅重逢" 可以判断）。

### a) 跨文本泛化（`src/phase1/e4_2_generalization.py`）

创建文件 `src/phase1/e4_2_generalization.py`，实现 3-fold cross-validation：

1. **数据准备**：从 `e4-1_raw.json` 读取，取 `writing_quality`, `emotional_impact`, `character_realism`, `cliche_level`, `reading_difficulty` 这 5 个数值评分列作为特征
2. **3-fold CV**：将 6 篇文本随机分成 3 组（各 2 篇）。每轮用 2 组训练一个 RandomForestClassifier（n_estimators=100），在剩余 1 组上预测 5 个画像标签（P1-P5）
3. **输出**：`data/output/e4-2_generalization.json`
   ```json
   {
     "accuracy_per_fold": [0.xx, 0.xx, 0.xx],
     "mean_accuracy": 0.xx,
     "random_baseline": 0.20,
     "pass": true/false (≥ 0.40),
     "confusion_matrix": [[...], ...]  // 可选
   }
   ```

### b) 外部锚定（`src/phase1/e4_2_anchoring.py`）

创建文件 `src/phase1/e4_2_anchoring.py`：

1. **审美判断一致性**：用 p16 中 P1（甜宠少女）的 `aesthetic_grade` 评分（A=4, A-=3, B=2, C=1）与 E3 aesthetic 评审 10 维度均分做 Spearman ρ 相关
   - ⚠️ **注意**：E3（p09-aesthetic-review）有 T1-T4 共 4 篇文本，而 p16 有 6 篇文本（4.1, 7.2, 9.1, 2.3, 10.3, 1.2）
   - E3 的 T2 对应 p16 的 "4.1"（咖啡厅重逢文本）
   - 对于其他 3 篇 E3 文本（T1, T3, T4），它们不在 p16 的 6 篇中
   - **因此，目前 p16 和 E3 只有 1 篇重叠文本（p16 "4.1" = E3 "T2"），不足以为 Spearman ρ 提供统计效力**
   - 作为替代方案：改为对 E3 本身的数据做分析——将 E3 的 aesthetic 评审 4 篇文本 × 10 维度的评分均值与 E3 其他评分类型（general, blind3, blind6）在对应文本上的评分均值做 Spearman ρ 相关分析
   - **设计决策**：如果只有 1 篇重叠文本，输出 `{"error": "p16与E3仅1篇文本重叠(n=1), Spearman ρ 无法计算", "overlap_text": {"p16": "4.1", "e3": "T2"}, "note": "建议运行E3更多文本的评测以获取足够样本"}`

2. **情感冲击**：同上，如果样本不足则输出 error 信息

3. **输出**：`data/output/e4-2_anchoring.json`

## 引用方式

`src/__main__.py` 已预留了命令注册位置，需要添加：
```python
"e4-2-g": "src.phase1.e4_2_generalization",
"e4-2-a": "src.phase1.e4_2_anchoring",
```

也可直接作为 stand-alone 脚本运行，入口函数签名与现有实验一致：
```python
def run(data_dir: Path, results_dir: Path):
    ...
```

## 执行步骤

1. 创建 `src/phase1/e4_2_generalization.py`
2. 创建 `src/phase1/e4_2_anchoring.py`
3. 更新 `src/__main__.py` 注册新命令
4. 运行 E4-2 泛化检验：`cd examples/p16-reader && python -m src e4-2-g`
5. 运行 E4-2 锚定检验：`cd examples/p16-reader && python -m src e4-2-a`
6. 汇总结果到 `data/output/e4-2_summary.json`：
   ```json
   {
     "generalization": {"accuracy": 0.xx, "pass": true/false},
     "anchoring": {"spearman_rho": null, "kendall_tau": null, "pass": "insufficient_data"},
     "overall_pass": false  // 泛化通过即可视为phase I通过的基础条件
   }
   ```
7. 更新 STATUS.md 的 E4-2 部分，填入实际结果

## 代码规范

- 遵循现有实验的文件结构和函数签名模式
- 使用 `packages.io.load_json` / `save_json` 进行文件读写
- 使用 `packages.stats.spearman_rho` / `kendall_tau` 进行统计
- sklearn 依赖已在环境中可用（用于 RandomForestClassifier）
- 每次提交后必须推送到远程仓库
