# 叙事工程 CLI 应用组

基于 p05-p10 实验验证的能力，设计一组 Rust CLI 工具。

## 架构

```
narrative-cli                  # 单一二进制，子命令分发
├── extract                    # p05 母题提取
├── review                     # p09 风格评审
├── gap                        # p08 母题缝隙分析
├── diagnose                   # p10 风格-母题交叉诊断
└── suggest                    # p10/p08 多向改进建议生成
```

每个子命令接受 YAML 配置文件（类似现有 `contract.yaml` 模式）和输入文本，通过 HTTP 调用 LLM API，输出结构化 JSON。

---

## 子命令设计

### `narrative-cli extract` — 母题提取

| 项 | 内容 |
|----|------|
| **来源** | p05 |
| **输入** | `--scene <path>` + `--motif-profile <path>`（可选，用于对照） |
| **输出** | `motifs.json`：母题列表（title, description, weight, evidence） |
| **选项** | `--series urban\|campus` 指定目标母题集 |

```
$ narrative-cli extract --scene assets/fiction/都市言情/3_初稿/1_1_咖啡厅重逢.md \
    --series urban --output results/motifs.json
{
  "motifs": [
    {"title": "十年", "description": "核心时间母题，贯穿全文", "weight": 8, "evidence": [...]},
    {"title": "手势", "description": "情感通过动作表达", "weight": 7, "evidence": [...]}
  ],
  "coverage": {"matched": 3, "total": 5, "rate": 0.60}
}
```

### `narrative-cli review` — 风格评审

| 项 | 内容 |
|----|------|
| **来源** | p09 |
| **输入** | `--scene <path>` + `--style <path>`（style.yaml） |
| **输出** | `review.json`：11 维度评分 + evidence + tension |
| **选项** | `--samples <dir>` 参考样本目录 |

```
$ narrative-cli review --scene scene.md --style urban-romance/style.yaml \
    --samples urban-romance/samples/ --output review.json
{
  "dimension_scores": [
    {"dimension": "情感表达", "score": 6, "evidence": [...], "tension": null, "note": "..."},
    {"dimension": "叙事视角", "score": 8, "evidence": [...], "tension": null, "note": "..."}
  ],
  "average": 7.7,
  "weak_dimensions": ["情感表达", "时代质感"]
}
```

### `narrative-cli gap` — 母题缝隙分析

| 项 | 内容 |
|----|------|
| **来源** | p08 |
| **输入** | `--scene <path>` + `--motif-profile <path>` |
| **输出** | `gap.json`：缺失/弱化母题 + 归因 + 6 方向建议 |
| **选项** | `--directions amplify,introduce,borrow` 选择建议方向 |

```
$ narrative-cli gap --scene draft.md --motif-profile urban-romance/motif.yaml \
    --directions amplify,restrain --output gap.json
{
  "gaps": [
    {
      "motif": "歌声", "status": "missing", "target_weight": 5,
      "attribution": {"gap_types": ["scene_incompatible"], "reasoning": "..."},
      "suggestions": [
        {"direction": "amplify", "text": "...", "feasibility": 4},
        {"direction": "restrain", "text": "十年母题已够重，不加歌声更好", "feasibility": 5}
      ]
    }
  ]
}
```

### `narrative-cli diagnose` — 风格-母题交叉诊断

| 项 | 内容 |
|----|------|
| **来源** | p10 |
| **输入** | `--scene <path>` + `--style <path>` + `--motif-profile <path>` |
| **输出** | `diagnosis.json`：弱维度↔缺失母题映射 + 组合改法 |
| **选项** | `--mode free\|guided` 诊断模式 |

```
$ narrative-cli diagnose --scene draft.md \
    --style urban-romance/style.yaml \
    --motif-profile urban-romance/motif.yaml --output diagnosis.json
{
  "links": [
    {
      "weak_dimension": "情感表达", "score": 5,
      "related_motif": "手势", "confidence": "high",
      "hypothesis": "场景缺乏非言语的情感动作",
      "combined_fix": "在第3段'她看着他'之后加入她抬起手想碰他肩膀又放下的动作",
      "fix_quality": {"specific": 5, "natural": 4, "motif_fit": 4}
    }
  ],
  "style_motif_mapping": {"情感表达": ["手势", "十年"], "时间结构": ["十年"]}
}
```

### `narrative-cli suggest` — 多向改进建议

| 项 | 内容 |
|----|------|
| **来源** | p08 + p10 |
| **输入** | `--scene <path>` + `--gap <path>`（gap 诊断 JSON）+ `--style <path>`（可选，组合模式） |
| **输出** | `suggestions.json`：6 方向建议 + pairwise 质量排名 |
| **选项** | `--compare` 启用 pairwise 对比评估 |

```
$ narrative-cli suggest --scene draft.md --gap gap.json \
    --style urban-romance/style.yaml --compare --output suggestions.json
{
  "suggestions": [
    {"direction": "introduce", "text": "...", "pairwise_wins": 3},
    {"direction": "amplify", "text": "...", "pairwise_wins": 2},
    {"direction": "restrain", "text": "...", "pairwise_wins": 1}
  ],
  "recommended": "introduce"
}
```

---

## 配置文件

### motif-profile.yaml（替代 motif.yaml 的扁平格式）

```yaml
series: urban-romance
title: 连接障碍
motifs:
  - title: 十年
    description: 核心时间母题
    weight: 10
  - title: 手势
    description: 全书最高级的情感表达在手里
    weight: 9
  - title: 雨
    description: 天气作为命运干涉的隐喻
    weight: 7
  - title: 孤独
    description: 独自扛了十年的创始人
    weight: 7
  - title: 歌声
    description: 特定歌曲标记情感浓度
    weight: 5
```

---

## 数据流

```
                    ┌──────────┐
                    │  scene   │
                    └────┬─────┘
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
     ┌─────────┐   ┌──────────┐   ┌──────────┐
     │ extract │   │  review  │   │   gap    │
     │  (p05)  │   │  (p09)   │   │  (p08)   │
     └────┬────┘   └────┬─────┘   └────┬─────┘
          │              │              │
          │         ┌────┘              │
          ▼         ▼                   │
     ┌──────────────────────┐           │
     │      diagnose        │◄──────────┘
     │       (p10)          │
     └──────────┬───────────┘
                │
                ▼
     ┌──────────────────────┐
     │      suggest         │
     │   (p08 + p10)        │
     └──────────────────────┘
```

---

## Cargo 项目结构

```
apps/cli/
├── Cargo.toml
├── src/
│   ├── main.rs              # CLI 入口，clap 子命令分发
│   ├── lib.rs               # 库入口
│   ├── contract.rs          # 配置文件模型（YAML deserialize）
│   ├── llm.rs               # LLM API 调用封装（DeepSeek HTTP）
│   ├── commands/
│   │   ├── mod.rs
│   │   ├── extract.rs       # extract 子命令
│   │   ├── review.rs        # review 子命令
│   │   ├── gap.rs           # gap 子命令
│   │   ├── diagnose.rs      # diagnose 子命令
│   │   └── suggest.rs       # suggest 子命令
│   └── prompts/
│       ├── mod.rs
│       ├── motif_extract.rs # p05 母题提取 prompt 模板
│       ├── style_review.rs  # p09 风格评审 prompt 模板
│       ├── gap_analysis.rs  # p08 缝隙分析 prompt 模板
│       └── diagnose.rs      # p10 交叉诊断 prompt 模板
├── tests/
│   └── integration.rs
└── contracts/               # 示例配置文件
    ├── urban-motif.yaml
    ├── campus-motif.yaml
    └── urban-style.yaml
```

---

## 与现有代码的关系

| 现有 | 本设计 |
|------|--------|
| `src/cli/src/main.rs`（单参数 demo） | `main.rs`（clap 子命令） |
| `src/cli/src/contract.rs`（状态机 contract） | `contract.rs`（保留 + 新增 motif/style YAML 模型） |
| `src/cli/src/workflow.rs`（pr4xis 引擎） | 保留（3R workflow 仍使用状态机） |
| 无 LLM 调用层 | 新增 `llm.rs`（HTTP client） |
| 无 prompt 管理 | 新增 `prompts/`（模板目录） |

---

## 优先实现顺序

| 优先级 | 子命令 | 原因 |
|:---:|------|------|
| 🔴 | `extract` | 所有下游功能的前置依赖 |
| 🔴 | `review` | 风格评审是 Reflect 环节的输入 |
| 🟡 | `gap` | 基于 extract 输出，独立性强 |
| 🟡 | `diagnose` | 依赖 extract + review 输出 |
| 🟢 | `suggest` | 依赖 diagnose/gap 输出，收束功能 |
