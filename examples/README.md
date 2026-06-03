# 叙事工程实验室 — 概念验证清单

面向叙事工程的逐项验证序列，补全"范畴模型 → 分析引擎 → 编辑器闭环"的缺失链路。

## 当前格局与缺口

```
元模型层：meta/（Lean 范畴模型 + contract.yaml）
              │
              ▼ 缺少：模型如何驱动实际写作行为？
    分析层：src/provider（FastAPI + LLM 叙事分析）
              │
              ▼ 缺少：分析结果如何回写到编辑器？
    编辑层：src/studio / write-agent-studio（Flutter 编辑器）
```

三个 PoC 依次填补这三层缺口。

---

## PoC 清单

### p03 — 评审标注嵌入编辑器

**验证目标**：把 provider 的分析结果（起承转合标签、空隙位置、风格对比、修改建议）嵌入到 Markdown 编辑器中，形成"写作 → 评审 → 修改 → 再评审"的闭环。

**验收标准**：
- 编辑器行号旁显示空隙标记圆点（复用 p02 的 gap-markers 设计）
- 每段尾部显示"起承转合"标签（颜色编码同 studio）
- 侧面板展示当前段落的 LLM 分析与风格对比
- 点击修改建议自动跳转到编辑器对应位置
- 修改后可一键重新提交评审

**依赖**：p02（复用 UI 模式）、provider API（分析数据源）

**技术栈建议**：单 HTML 文件（在 p02 index.html 基础上集成 provider 调用），或 Flutter 原型（扩展 studio）

---

### p04 — 范畴模型驱动的写作工作台

**验证目标**：把 cli 的范畴论 FSM 引擎引入实际写作工具，验证 contract.yaml 定义的阶段转换能约束和引导作者的写作行为。

**验收标准**：
- 工作台显示当前写作阶段（material / outline / firstDraft / finalDraft）
- 只有合法态射对应的操作按钮可用（如 material 阶段不显示 review 按钮）
- 自环操作带计数器（rewrite 3/5、review 2/3）
- 尝试非法操作时显示违反的守卫条件和当前状态
- 阶段转换记录可追溯（类似 p01 的 3R 会话记录）

**依赖**：meta/（contract.yaml 和 Lean 模型）、p01（3R 会话模式）

**技术栈建议**：Python CLI（在 p01 基础上扩展），或 Web 界面（前端展示状态机 + 后端运行 Rust FSM）

---

### p05 — 多文档风格对比与写作模式发现

**验证目标**：利用 provider StyleStore 积累的好文章语料库，可视化对比多篇文章的叙事结构分布，帮助作者发现自己的写作模式。

**验收标准**：
- 展示语料库中所有文章的"起承转合"段落分布热力图
- 选定一篇待评审文章，可视化其叙事结构与"好文章平均分布"的偏差
- 展示风格对比的具体段落对（坏段落 vs 好范例）
- 支持按作者、标签、时间范围筛选对比
- 随着语料积累，趋势图自然浮现

**依赖**：provider（StyleStore 和分析能力）

**技术栈建议**：单 HTML 文件（Chart.js 或 ECharts 可视化 + 调用 provider API），或扩展 studio 新增对比面板

---

## 推荐实施顺序

| 优先级 | PoC | 预估工作量 | 填补缺口 | 依赖 |
|--------|-----|-----------|---------|------|
| 1 | p03 评审标注嵌入编辑器 | 中 | 分析 → 编辑闭环 | p02、provider |
| 2 | p04 范畴模型驱动的写作工作台 | 中 | 模型 → 行为驱动 | meta/、p01 |
| 3 | p05 多文档风格对比与写作模式发现 | 小 | 积累 → 洞察 | provider |

## 来源

- 缺口分析：`apps/qtcloud-write/STATUS.md`
- 范畴模型：`examples/default/examples/meta/`
- 分析引擎：`apps/qtcloud-write/src/provider/`
- 编辑前端：`apps/qtcloud-write/src/studio/`
