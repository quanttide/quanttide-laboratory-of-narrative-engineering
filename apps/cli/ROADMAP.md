# ROADMAP — qtcloud-3r CLI

3R 写作工具链。AI for AI。

---

## 设计原则

- **CLI is the API** — stdin/stdout 管道，每步输出 JSON
- **AI 是调用者** — 所有输出都是结构化的（JSON），人类可读是副产品
- **单文件操作** — 每次处理一个文本对象，不管理目录/项目/状态

---

## 命令设计

```
3r review   <file    # 理解意图 → {genre, intent, stage, summary}
3r reflect  <file    # 检测空隙 + 归因 → [{gap_type, causes}]
3r rewrite  <file    # 根据归因改写 → 新版本
3r 3r       <file    # 一轮完整 3R
```

每条命令：
- 输入：文件路径 或 stdin（`-`）
- 输出：JSON 到 stdout，日志到 stderr
- 管道用法：`cat draft.md | 3r reflect | 3r rewrite > final.md`

---

## 阶段

### P0 — 核心管线（当前）

目标：跑通 3R 管线，AI 可调用。

- [ ] 项目骨架：pyproject.toml、cli entry point
- [ ] `3r review` —— 迁移 p04 的 Review prompt（体裁/意图/阶段/总结）
- [ ] `3r reflect` —— 迁移 p02 的 Reflect prompt（空隙检测 + 4 视角归因）
- [ ] `3r rewrite` —— 输入原文 + Reflect JSON，输出改写文本
- [ ] `3r 3r` —— 组合命令，一次调用完成一轮 3R
- [ ] 管道支持：所有命令可接受 stdin，输出 JSON 到 stdout

### P1 — AI 交互优化

目标：让 AI 调用更自然。

- [ ] `--format text` 参数：输出人类可读文本而非 JSON（调试用）
- [ ] `--model` 参数：可选 LLM 模型
- [ ] `--temperature` 参数
- [ ] 非 0 退出码：Review/Reflect 失败时退出码区分问题类型

### P2 — 配置与扩展

- [ ] `.3rconfig` 配置文件（默认模型、写作风格偏好）
- [ ] `--style` 参数：指定风格指南文件，供 Review/Reflect 作为上下文
- [ ] 输出分步缓存：每步结果写入临时文件，支持断点续跑

---

## 与实验室实验的对应

| CLI 命令 | 实验来源 | 状态 |
|----------|---------|------|
| `review` | p04 Review 可靠性 | ✅ prompt 已验证 |
| `reflect` | p02 修正版 Reflect | ✅ prompt 已验证 |
| `rewrite` | p02 修正版 Rewrite | ✅ prompt 已验证 |
| `3r` | p02 全流程 | ✅ 15/15 轮成功 |

已有实验数据可以直接迁移，不需要重新验证 prompt。
