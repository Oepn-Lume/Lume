# Lume Sentinel 的 LLM Wiki 适配说明

## 1. 文档目的

本文档说明如何将 Karpathy 的 `llm-wiki` 思路适配到 `Lume Sentinel` 中，并与现有的 `Shadow Logging`、本地蒸馏和任务执行闭环结合。

参考来源：

- [Karpathy llm-wiki gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)

## 2. llm-wiki 的核心思想

`llm-wiki` 的重点不是把原始资料直接塞进提示词，而是让系统维护一套持续生长、结构化、可更新的 wiki。

它强调三个层次：

1. `Raw Sources`
   保存原始资料，不直接手工混入最终答案

2. `Wiki`
   由 LLM 维护的结构化知识页面，作为长期记忆层

3. `Schema / Rules`
   规定如何写入、更新、链接、查询和检查 wiki

这个思路的价值在于：

- 降低上下文反复重复注入的成本
- 让知识变成可编辑、可审查、可增量演化的资产
- 让模型不只是“回答”，而是“维护一个知识系统”

## 3. 对 Lume 的直接映射

在 `Lume Sentinel` 中，这三个层次可以直接映射为：

- `Raw Sources`
  对应 `data/task_runs/`、未来的 `data/raw_logs/`、外部资料目录

- `Wiki`
  对应 `data/wiki/`

- `Schema / Rules`
  对应未来的 wiki 维护规范、脚本策略和 prompt 模板

换句话说：

- `Shadow Logging` 负责捕获原始任务资产
- `LLM Wiki Memory` 负责把原始资产沉淀为结构化知识
- `Distill Pipeline` 再把高价值知识和行为模式转成训练资产

## 4. Lume 里的 wiki 不只是知识库

在 `Lume` 里，wiki 不只是“记录事实”，还应该记录三类资产：

1. `用户资产`
   偏好、目标、风格、常见约束

2. `任务资产`
   成功样例、失败原因、工作流、常用脚本、操作模板

3. `行为资产`
   Codex 执行惯性、云端规划模式、可复用的任务拆解方式

因此，Lume 的 wiki 比一般的知识库更像一个“结构化数字海马体”。

## 5. V1 的最小适配方案

为了避免一开始做得过重，`V1` 先实现最小三件套：

1. `index.md`
   作为 wiki 内容目录

2. `log.md`
   作为按时间追加的变更日志

3. `tasks/<task_id>.md`
   作为每个高价值任务的结构化页面

这意味着 `V1` 不追求一开始就实现复杂主题图谱，而是先把每个已完成任务沉淀为可查、可读、可扩写的页面。

## 6. 为什么这一步很关键

只有 `Shadow Logging`，系统得到的是“轨迹”。

只有本地蒸馏，系统得到的是“参数”。

而 `LLM Wiki Memory` 提供的是第三种资产：

- 既不是原始日志
- 也不是不可读参数
- 而是介于两者之间、可被人和模型共同维护的结构化记忆层

这正是 `Token as Asset` 里“知识可持有”的关键部分。

## 7. 推荐的页面结构

每个任务页建议包含：

- 基本信息
- 用户目标
- 过程摘要
- 可复用模式
- 工具动作
- 文件结果
- 后续可蒸馏价值

这样做的好处是，后面无论是人工审阅、检索问答，还是样本构建，都会更容易。

## 8. 与 Karpathy 思路最一致的地方

`Lume` 采用这套思路时，最一致的部分有三点：

- 用 markdown 页面而不是只存向量
- 维护 `index.md` 和 `log.md`
- 让系统持续更新 wiki，而不是一次性生成完就不再维护

## 9. Lume 的扩展点

相较于原始 `llm-wiki` 思路，`Lume` 会增加两个扩展层：

1. `Execution-aware Memory`
   把工具调用和文件变更也写入 wiki

2. `Distill-aware Memory`
   在页面中标记哪些任务更适合进入训练数据集

因此，Lume 的 wiki 会天然比普通笔记系统更靠近“Agent memory operating system”。

## 10. V1 结论

`Karpathy llm-wiki` 为 `Lume Sentinel` 提供了记忆层最清晰的工程范式：

- 原始日志负责完整性
- wiki 页面负责结构化
- 后续蒸馏负责参数化

三者结合后，`Token` 支出才真正能转化为本地长期资产。
