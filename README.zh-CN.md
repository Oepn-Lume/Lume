# Lume

> `Lume` 不是替代 agent 的新 agent，而是装在现有 agent 外层的一层增强，让它们少犯重复错误、少空转、少浪费，并且在撞墙后更快改道。

## 当前对外结果

目前这套 `baseline` vs `baseline + Lume` 的 before/after 结果，已经在三条线上稳定成立：

| 结果线 | 当前等级 | 当前读法 |
| --- | --- | --- |
| `Codex baseline` vs `Codex + Lume` | `B` | 最强的一条线，已经是强可用结果 |
| `OpenClaw baseline` vs `OpenClaw + Lume` | `stable B-` | 已经稳定，不再只是“看起来有用” |
| `Claude Code baseline` vs `Claude Code + Lume` | `stable B-` | 第三个 family 落地后，已经进入稳定可讲状态 |

这意味着项目已经不再是“1 条强线 + 2 条快成型的线”，而是：

- `1` 条 `B`
- `2` 条 `stable B-`

## Lume 到底是什么

`Lume` 是：

- 失效感知层
- 改道控制层
- anti-stall / anti-loop 增强层
- `baseline` vs `baseline + Lume` 的 paired 评测框架

`Lume` 不是：

- `Codex / OpenClaw / Claude Code` 的替代品
- 已经拿到最终级别证明的新模型
- 三条线完全一样强的结果

## 当前最安全的对外讲法

现在可以稳定对外讲的是：

> `Lume` 不是替代现有 agent，而是加在现有 agent 外层的一层控制与增强。当前跨三条线的正式结果是：`Codex + Lume = B`，`OpenClaw + Lume = stable B-`，`Claude Code + Lume = stable B-`。

## 对外引用入口

正式对外时，优先引用这几页：

- 阶段收口页：
  [wiki/analysis/agent-augmentation-phase-close-note-2026-04-21.md](./wiki/analysis/agent-augmentation-phase-close-note-2026-04-21.md)
- 最终总清单：
  [wiki/analysis/agent-augmentation-final-inventory-2026-04-21.md](./wiki/analysis/agent-augmentation-final-inventory-2026-04-21.md)
- 最终等级总表：
  [wiki/analysis/agent-augmentation-paired-scoring-final-gradeboard-2026-04-21.md](./wiki/analysis/agent-augmentation-paired-scoring-final-gradeboard-2026-04-21.md)
- 对外发布摘要：
  [wiki/analysis/agent-augmentation-public-release-summary-2026-04-21.md](./wiki/analysis/agent-augmentation-public-release-summary-2026-04-21.md)
- 首页摘要条：
  [wiki/analysis/lume-public-summary-strip-final-2026-04-21.md](./wiki/analysis/lume-public-summary-strip-final-2026-04-21.md)

## Wiki

- Wiki 索引：
  [wiki/index.md](./wiki/index.md)
- 当前对外发布入口：
  [wiki/analysis/agent-augmentation-public-release-summary-2026-04-21.md](./wiki/analysis/agent-augmentation-public-release-summary-2026-04-21.md)

## 现在能说什么，不能说什么

现在能说：

- `Lume` 的增强效果已经不是只在一条线上成立
- 三条线都已经有正式 before/after scoring 页
- 当前项目的主叙事已经稳定成型

现在还不该说：

- “已经 publication-clean”
- “`Codex` 已经到 `A`”
- “三条线已经一样强”
- “`stable B-` 就等于最终证明”

## 后续更高等级目标

下一阶段的更高等级目标已经明确：

- `Codex: B -> A`
- `OpenClaw: stable B- -> B`
- `Claude Code: stable B- -> B`

路线图：
[wiki/analysis/agent-augmentation-higher-grade-roadmap-2026-04-21.md](./wiki/analysis/agent-augmentation-higher-grade-roadmap-2026-04-21.md)

## 联系方式

- GitHub: [Oepn-Lume/Lume](https://github.com/Oepn-Lume/Lume)
- Email: `dspwatch@gmail.com`
