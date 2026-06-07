# story/ — 叙事写作辅助管线

诊断场景内部行为因果链 → 生成写作提纲。

| 模块 | 来源 | 功能 |
|------|------|------|
| `p14_scene_diagnosis.py` | p14 | 行为链标注 → 薄弱点诊断 → 三类修改建议 |
| `p15_outline_generation.py` | p15 | YAML + p14 JSON → 场景写作备忘 |

## 用法

```bash
uv run python src/p14_scene_diagnosis.py
uv run python src/p15_outline_generation.py
```
