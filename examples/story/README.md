# story/ — 叙事写作辅助管线

p18 统一入口，已取代 p14/p15。

| 子命令 | 取代 | 功能 |
|--------|------|------|
| `infer` | — | 情节推理 + 叙事节奏分析 |
| `check` | p14 | 角色一致性检查（行为链标注 → 诊断 → 建议） |
| `outline` | p15 | 推理 + YAML → 格式化写作备忘 |
| `rhythm` | — | 全量相邻对叙事节奏曲线 |

## 用法

```bash
uv run python src/p18_character_plot.py infer
uv run python src/p18_character_plot.py check <场景名>
uv run python src/p18_character_plot.py outline --scene-id <ID>
uv run python src/p18_character_plot.py rhythm
```

## 扩展

角色实验直接在此组内新增，共享 `config.py` 和 `assets/fiction/`。
