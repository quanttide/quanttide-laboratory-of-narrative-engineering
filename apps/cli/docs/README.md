# qtcloud-3r

3R 写作工具链。AI for AI。

## 安装

```bash
git clone https://github.com/quanttide/quanttide-laboratory-of-narrative-engineering.git
cd quanttide-laboratory-of-narrative-engineering/apps/cli
pip install -e .
export DEEPSEEK_API_KEY="sk-..."
```

验证安装成功：

```bash
3r --help
```

依赖：Python ≥ 3.12、DeepSeek API key。

## 先试试

```bash
echo '他推开门，看到她坐在窗边。想说话，但喉咙发紧。' | 3r review --format text
```

10 秒内能看到输出，确认工具正常。

## 输入格式

- 纯文本（推荐）或 Markdown
- 中文/英文均可
- 不限长度（长文本会自动截断到前 2000 字）
- 每段用空行分隔

## 命令

### `3r review` — 理解文本意图

```bash
3r review draft.md
cat draft.md | 3r review
3r review draft.md --format text
```

输出：
```json
{
  "genre": "重逢场景",
  "intent": "推进暗恋十年的重逢关系",
  "stage": "成稿，细节丰富、心理描写细腻",
  "summary": "暗恋十年的林远亭在咖啡店偶遇陆知微"
}
```

### `3r reflect` — 检测空隙 + 归因

```bash
cat draft.md | 3r reflect
cat draft.md | 3r reflect --format text
```

输出 JSON 数组：
```json
[
  {
    "gap_type": "transition",
    "location": "从林远亭视角切换到陆知微",
    "structure": "必然省略，但缺少过渡锚点",
    "psychology": "未写林远亭的观察过程",
    "reader": "读者需要一个共享感官细节桥接",
    "craft": "无意识忽略",
    "root_cause": "视角切换缺少共享感官细节"
  }
]
```

### `3r rewrite` — 带归因改写

```bash
cat draft.md | 3r rewrite > final.md
```

输出：
```json
{
  "text": "修改后的完整文章……",
  "length": 1234
}
```

`--format text` 时直接输出纯文本，适合重定向到文件。

### `3r cycle` — 完整一轮

```bash
cat draft.md | 3r cycle > result.json
```

等价于依次执行 review → reflect → rewrite。输出包含全部三个阶段的结果。

`3r 3r` 也支持（与 `3r cycle` 等价），但推荐用 `cycle`。

## 参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--model` | `deepseek-chat` | LLM 模型 |
| `--temp` | `0.3` | 温度 |
| `--format` | `json` | 输出格式：`json` 或 `text` |

## 输出结构

| 命令 | json 格式 | text 格式 |
|------|----------|----------|
| `review` | `{genre, intent, stage, summary}` | 五行文本 |
| `reflect` | `[{gap_type, ...}]` | 每条空隙一屏 |
| `rewrite` | `{text, length}` | 纯文本 |
| `cycle` | `{review, reflect, rewrite}` | 三段式文本 |

## 管道用法

```bash
cat draft.md | 3r review | 3r reflect | 3r rewrite > final.md
```

每条命令的输出可作为下一条的输入。不限于内置的 `3r cycle`。

## 退出码

| 码 | 含义 |
|----|------|
| 0 | 成功 |
| 2 | API 错误（网络/认证） |
| 3 | 解析错误（LLM 输出格式异常） |
| 4 | 输入为空 |
