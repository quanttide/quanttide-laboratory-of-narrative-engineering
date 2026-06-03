# qtcloud-3r

**位置**：`apps/provider/` · 属于 [quanttide-laboratory-of-narrative-engineering](https://github.com/quanttide/quanttide-laboratory-of-narrative-engineering)

3R 写作服务。API 端点：

| 端点 | 方法 | 输入 | 输出 |
|------|------|------|------|
| `/review` | POST | `{"text": "..."}` | `{genre, intent, stage, summary}` |
| `/reflect` | POST | `{"text": "..."}` | `[{gap_type, structure, ...}]` |
| `/rewrite` | POST | `{"text": "..."}` | `{text, length}` |
| `/cycle` | POST | `{"text": "..."}` | `{review, reflect, rewrite}` |

## 启动

```bash
git clone https://github.com/quanttide/quanttide-laboratory-of-narrative-engineering.git
cd quanttide-laboratory-of-narrative-engineering/apps/provider
pip install -e .
export DEEPSEEK_API_KEY="sk-..."
python -m app
```

依赖：Python ≥ 3.12、DeepSeek API key。

## 调用

```bash
curl -X POST http://localhost:8000/review \
  -H "Content-Type: application/json" \
  -d '{"text": "他推开门，看到她坐在窗边。"}'
```

上限 **8000 字**（超过返回 422）。
