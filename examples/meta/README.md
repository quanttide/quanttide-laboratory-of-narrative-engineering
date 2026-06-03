# 从范畴模型到工作流引擎

## 架构

```
Lean 模型 (WriteCategory.lean)
    │  LLM 可读、可校验的范畴论形式化
    │  保证阶段和态射的完备性
    ▼
contract.yaml
    ├── stages/     平台定义（结构固定，源自 Lean 模型）
    └── expand/     用户配置（有界展开参数，自由定义）
    │
    ▼ 平台有界展开引擎
    展开规则：自环 → 带 max 计数器的有限转移
             done → 带 min_cycle 守卫的终态转移
    ▼
可执行的 FSM
```

## 两层分离

| 层 | 谁定义 | 内容 | 校验手段 |
|----|--------|------|---------|
| `stages` | 平台 | 写作阶段、合法态射 | Lean 模型 + LLM 形式化校验 |
| `expand` | 用户 | max 值、守卫条件 | 用户自由设定，LLM 可验证是否与 Lean 模型一致 |

## Lean 模型的定位

Lean 代码**不**参与运行时。它的角色：

- **给 LLM 一个可推理的范畴论模型** — LLM 读取 `WriteCategory.lean` 后，能理解写作过程的变换结构，从而校验用户配置的 `expand` 参数是否在范畴论上合法（例如 `min_cycle: 1` 的前提是 `cycle` 变量存在且有 `max >= 1`）
- **形式化的沟通语言** — 人与 LLM 之间、LLM 与校验工具之间，用同一份 Lean 代码作为语义锚点

## 有界展开

平台提供展开机制：给定 `expand` 参数，将自由范畴中的自环路径和 done 转移替换为带计数器的有限路径。

```
expand 前（自由范畴）                expand 后（FSM）
firstDraft ──rewrite──→ firstDraft    firstDraft ──rewrite──→ firstDraft
        （无限循环）                    ↓ cycle < max
                                       firstDraft (cycle++)
                                       ...
                                       cycle ≥ min_cycle → finalDraft
```
