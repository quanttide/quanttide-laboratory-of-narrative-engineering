# qtcloud-3r

3R 写作工具链。AI for AI。

## 安装

```bash
pip install -e /path/to/apps/cli
export DEEPSEEK_API_KEY="sk-..."
```

## 命令

### 3r review — 理解文本意图

```bash
cat draft.md | 3r review
3r review draft.md --format text
```

输出 JSON：
```json
{
  "genre": "重逢场景",
  "intent": "推进暗恋十年的重逢关系",
  "stage": "成稿，细节丰富、心理描写细腻",
  "summary": "暗恋十年的林远亭在咖啡店偶遇陆知微"
}
```

### 3r reflect — 检测空隙 + 归因

```bash
cat draft.md | 3r reflect
cat draft.md | 3r reflect --format text
```

输出 JSON 数组，每个空隙包含 4 视角分析：

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

### 3r rewrite — 带归因改写

```bash
cat draft.md | 3r rewrite > final.md
cat draft.md | 3r rewrite --format text
```

输入原文，输出改写后的完整文本。

### 3r 3r — 完整一轮

```bash
cat draft.md | 3r 3r > result.json
cat draft.md | 3r 3r --format text
```

等价于依次执行 review → reflect → rewrite。

## 参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--model` | `deepseek-chat` | LLM 模型 |
| `--temp` | `0.3` | 温度 |
| `--format` | `json` | 输出格式：`json` 或 `text` |

## 管道用法

```bash
cat draft.md | 3r review | 3r reflect | 3r rewrite > final.md
```

每个命令的输出都可直接作为下一个命令的上下文。组合灵活，不限于内置的 `3r 3r`。

## 退出码

| 码 | 含义 |
|----|------|
| 0 | 成功 |
| 2 | API 错误 |
| 3 | 解析错误 |
| 4 | 输入为空 |
