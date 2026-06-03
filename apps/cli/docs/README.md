# qtcloud-3r

**位置**：`apps/cli/` · 属于 [quanttide-laboratory-of-narrative-engineering](https://github.com/quanttide/quanttide-laboratory-of-narrative-engineering)

3R 写作工具链。AI for AI。

## 安装

```bash
git clone https://github.com/quanttide/quanttide-laboratory-of-narrative-engineering.git
cd quanttide-laboratory-of-narrative-engineering/apps/cli
pip install -e .
```

获取 API key 并配置：

```bash
# https://platform.deepseek.com/api_keys
export DEEPSEEK_API_KEY="sk-..."
```

验证安装：

```bash
3r --help
```

依赖：Python ≥ 3.12、DeepSeek API key（export 到环境变量）。

## 先试试

```bash
echo '他推开门，看到她坐在窗边。想说话，但喉咙发紧。' | 3r review --format text
```

10 秒内能看到输出，确认工具正常。

## 输入格式

- 纯文本（推荐）或 Markdown
- 中文/英文均可
- 上限 **8000 字**（超过会报错退出，不会静默截断）
- 每段用空行分隔

## 命令

统一用法：`3r <command> [file]`。省略 file 时从 stdin 读取。

### `3r review` — 理解文本意图

```bash
3r review draft.md
```

```json
{
  "genre": "重逢场景",
  "intent": "推进暗恋十年的重逢关系",
  "stage": "成稿，细节丰富、心理描写细腻",
  "summary": "暗恋十年的林远亭在咖啡店偶遇陆知微"
}
```

`--format text`：

```text
体裁: 重逢场景
意图: 推进暗恋十年的重逢关系
阶段: 成稿，细节丰富、心理描写细腻
总结: 暗恋十年的林远亭在咖啡店偶遇陆知微
```

### `3r reflect` — 检测空隙 + 归因

```bash
3r reflect draft.md
```

```json
[
  {
    "gap_type": "transition",
    "location": "从林远亭视角切换到陆知微",
    "detail": "缺少过渡性的环境或心理衔接",
    "structure": "必然省略，但缺少过渡锚点",
    "psychology": "未写林远亭的观察过程",
    "reader": "读者需要一个共享感官细节桥接",
    "craft": "无意识忽略",
    "root_cause": "视角切换缺少共享感官细节"
  }
]
```

`--format text`：

```text
--- 空隙 1 ---
类型: transition
位置: 从林远亭视角切换到陆知微
说明: 缺少过渡性的环境或心理衔接
叙事结构: 必然省略，但缺少过渡锚点
人物心理: 未写林远亭的观察过程
读者期待: 读者需要一个共享感官细节桥接
写作技法: 无意识忽略
根本原因: 视角切换缺少共享感官细节
```

### `3r rewrite` — 带归因改写

```bash
3r rewrite draft.md --format text > final.md
```

`--format text` 输出纯文本，**没有 JSON 包裹**，适合 `> final.md`。

```json
{
  "text": "修改后的完整文章……",
  "length": 1234
}
```

### `3r cycle` — 完整一轮

等价于依次执行 review → reflect → rewrite。

```bash
3r cycle draft.md > result.json
```

```json
{
  "review": {
    "genre": "重逢场景",
    "intent": "推进暗恋十年的重逢关系",
    "stage": "成稿",
    "summary": "十年暗恋在咖啡店重逢"
  },
  "reflect": [
    {
      "gap_type": "transition",
      "location": "从林远亭视角切换到陆知微",
      "detail": "缺少过渡性衔接",
      "structure": "必然省略，但缺少过渡锚点",
      "psychology": "未写林远亭的观察过程",
      "reader": "读者需要一个共享感官细节桥接",
      "craft": "无意识忽略",
      "root_cause": "视角切换缺少共享感官细节"
    }
  ],
  "rewrite": {
    "text": "修改后的完整文章……",
    "length": 1234
  }
}
```

## 参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--model` | `deepseek-chat` | LLM 模型 |
| `--temp` | `0.3` | 温度 |
| `--format` | `json` | 输出格式：`json` 或 `text` |

## 输出结构

| 命令 | json 格式 | text 格式 |
|------|----------|----------|
| `review` | `{genre, intent, stage, summary}` | 4 行键值 |
| `reflect` | `[{gap_type, structure, psychology, reader, craft, root_cause}]` | 每条空隙 8 行 |
| `rewrite` | `{text, length}` | 纯文本，无包裹 |
| `cycle` | `{review, reflect, rewrite}` | 三段式文本 |

## 退出码

| 码 | 含义 |
|----|------|
| 0 | 成功 |
| 2 | API 错误（网络/认证） |
| 3 | 解析错误（LLM 输出格式异常） |
| 4 | 输入为空 |
| 5 | 输入过长（上限 8000 字） |
