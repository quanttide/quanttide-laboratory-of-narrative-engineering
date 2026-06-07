# story/ — 叙事写作辅助管线

情节 + 角色：诊断场景因果链 → 生成写作备忘 → 分析角色档案/弧线/关系。

| 模块 | 来源 | 功能 |
|------|------|------|
| `p14_scene_diagnosis.py` | p14 | 行为链标注 → 薄弱点诊断 → 三类修改建议 |
| `p15_outline_generation.py` | p15 | YAML + p14 JSON → 场景写作备忘 |

## 用法

```bash
uv run python src/p14_scene_diagnosis.py
uv run python src/p15_outline_generation.py
```

## 扩展

角色实验（角色档案提取、弧线检测、关系图谱）直接在此组内新增，与情节模块共享 `config.py` 和 `assets/fiction/story.yaml`。
