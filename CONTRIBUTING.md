# 贡献指南

## 工作流程

实验室的实验是探索性的。出发前不需要完整的实验设计——需要的是一个方向、一个最小可运行的版本、和记录结果的习惯。

### 做实验

1. 在 `examples/` 下创建 `p##-name/` 目录
2. 写 `README.md`，三两句话说明方向即可
3. 写代码、跑一次、看发生了什么
4. 把发现写在 `STATUS.md` 里
5. 决定下一步：改方向、继续深入、或终止

### 模板

```
examples/p##-name/
├── README.md          # 出发方向（草稿级别，不需要完整设计）
├── STATUS.md          # 跑完后记下的结果和反思（核心产出）
├── TODO.md            # 待办（可选）
├── src/               # 代码
├── data/              # 输入输出数据
│   ├── input/
│   └── output/
└── docs/              # 设计记录（可选）
```

### README.md 写什么

出发前的草稿，不是蓝图。写清楚即可：

- 想探索什么（一句话）
- 需要什么数据
- 怎么跑
- 预期（如果预期错了，记在 STATUS.md 里）

### STATUS.md 写什么

这是实验的真正产出。跑完后记：

- 发生了什么
- 和出发时的预期有哪些一致和偏差
- 发现了什么新问题
- 如果终止，原因是什么

## 技术栈

- **语言**：Python 3.11+
- **包管理**：`uv`（每个实验在各自目录下 `uv sync`）
- **公共工具**：`packages/` 在仓库根目录，包含 LLM 调用（`packages/llm.py`）、JSON 读写（`packages/io.py`）、统计函数（`packages/stats.py`）
- **LLM 模型**：默认 DeepSeek Chat，与 p09/p10 一致
- **不做**：不引入 pandas、matplotlib、PyTorch

### 路径约定

所有 `src/` 中的脚本通过 `GIT_ROOT = Path(__file__).resolve().parents[n]` 定位仓库根，然后 `sys.path.insert(0, str(GIT_ROOT))` 导入 `packages/`。

## 数据资产

实验共用的文本和元数据在 `assets/fiction/`：

| 文件 | 内容 |
|------|------|
| `4_成稿/*.md` | 职场言情系列成稿 14 篇 |
| `3_初稿/*.md` | 对应初稿 |
| `style.yaml` | 克制浪漫风格配置（11 维度 + boundaries） |
| `motif.yaml` | 母题模型（5 母题 + 权重） |
| `story.yaml` | 故事结构（角色 + 情节线 + tensions） |

## 已有的实验

见 `examples/README.md`。每个实验的 STATUS.md 记录了它的实际发现——比 README.md 更值得读。

## 提交

实验代码和数据提交到本仓库（`quanttide-laboratory-of-narrative-engineering`）。实验报告提交到 `docs/report/laboratory/experiments/`（`quanttide-report-of-narrative-engineering`）。
