---
id: implementation-plan-v1-md
type: doc
relative_path: implementation-plan-v1.md
language: mixed
section: root
---

# Lume Sentinel 2026 技术实施方案 V1

## Source
- Path: `implementation-plan-v1.md`
- Language: `mixed`
- Section: `root`
- Original file: [implementation-plan-v1.md](C:/Users/yh-PC-003/Desktop/codex/lume/docs/implementation-plan-v1.md)

## Body

# Lume Sentinel 2026 技术实施方案 V1

## 1. 文档目标

本文档是 `Lume Sentinel 2026 白皮书 V1` 的工程化落地版本，用于将“Token 资产化”方案拆解为可执行的系统模块、目录结构、数据流和开发阶段。

`V1` 的目标不是一次性实现全部愿景，而是优先建立最关键的闭环：

- 记录高价值云端交互
- 沉淀结构化记忆
- 整理蒸馏训练样本
- 微调本地电池模型
- 在相似任务上进行本地优先复用

## 2. V1 建设原则

### 2.1 先闭环，后扩展

优先验证一次云端任务能否稳定转化为未来的本地可复用能力，而不是同时追求过多高级能力。

### 2.2 先资产化，后智能化

先保证日志、知识、训练语料、LoRA 权重和用户偏好能够沉淀为可长期保存的资产，再追求更复杂的自动推演能力。

### 2.3 先可验证，后宏大化

每一个模块都应具备清晰输入输出和可验证结果，避免陷入概念堆叠。

### 2.4 本地主权优先

训练语料、蒸馏产物、结构化记忆和执行日志默认保存在本地目录中，确保用户对核心数字资产拥有控制权。

## 3. V1 范围定义

`V1` 包含以下六个核心模块：

1. `Shadow Logging`
2. `LLM Wiki Memory`
3. `Dataset Builder`
4. `Distill Pipeline`
5. `Local Router`
6. `Codex Execution Loop`

`V1` 暂不强制包含以下内容：

- 复杂多模态感知
- 完整动态因果图训练
- 高级世界事件预测引擎
- 电影感前端 UI
- 全自动无人值守自主规划系统

这些能力可以在 `V2+` 逐步接入，但不应影响 `V1` 的闭环验证。

## 4. 核心系统流程

`V1` 的主流程如下：

1. 用户发起任务，或系统接收到高价值任务信号
2. `Local Router` 判断任务应走云端、本地或混合模式
3. 若走云端，系统记录完整的输入、输出、执行轨迹和结果
4. `Codex` 执行代码修改、脚本调用、文件更新等动作
5. `Shadow Logging` 将关键行为写入任务日志
6. `LLM Wiki Memory` 提炼其中可长期保留的知识与偏好
7. `Dataset Builder` 将高质量任务转换为蒸馏样本
8. `Distill Pipeline` 定期训练 `Gemma 4 + LoRA`
9. 后续相似任务优先尝试由本地模型接管或辅助完成

## 5. 目录结构建议

建议在 `lume` 目录下使用以下结构：

```text
lume/
  docs/
    whitepaper-v1.md
    implementation-plan-v1.md
  configs/
    models.yaml
    routing.yaml
    retention.yaml
  data/
    raw_logs/
    task_runs/
    wiki/
    datasets/
    distilled/
    checkpoints/
  scripts/
    collect_shadow_logs.py
    build_wiki_entries.py
    build_distill_dataset.py
    train_lora.py
    evaluate_local_model.py
    route_task.py
  src/
    lume/
      __init__.py
      logging/
      memory/
      routing/
      distill/
      execution/
      evaluation/
  prompts/
    wiki/
    distill/
    routing/
  examples/
    task_samples/
    dataset_samples/
  tests/
    test_logging.py
    test_routing.py
    test_dataset_builder.py
    test_wiki_memory.py
```

## 6. 模块设计

### 6.1 Shadow Logging

`Shadow Logging` 是整个资产化流程的入口模块。

职责：

- 记录任务元信息
- 记录用户输入与模型输出
- 记录 `Codex` 的执行轨迹
- 记录关键文件变更摘要
- 记录任务结果、失败原因和后续修正

建议输出格式：

- 每次任务一个目录
- 每个任务目录包含结构化 `json` 日志和摘要 `md`

建议目录示例：

```text
data/task_runs/2026-04-09-task-0001/
  task.json
  prompt_response.json
  tool_trace.json
  file_diff_summary.md
  outcome.json
  notes.md
```

关键字段建议：

- `task_id`
- `timestamp`
- `user_goal`
- `route_mode`
- `model_used`
- `prompts`
- `responses`
- `tool_calls`
- `files_changed`
- `result_status`
- `postmortem`
- `value_score`

其中 `value_score` 用于后续筛选哪些任务值得进入蒸馏流程。

### 6.2 LLM Wiki Memory

`LLM Wiki Memory` 负责把一次性任务结果转化为长期知识资产。

职责：

- 记录用户偏好
- 记录项目背景和上下文
- 记录常见问题及其解决套路
- 记录高频工作流模板
- 记录重要世界知识或外部依赖决策

建议采用 Markdown + YAML Frontmatter 的格式，便于人读和程序处理。

建议目录结构：

```text
data/wiki/
  user/
  projects/
  workflows/
  decisions/
  world/
```

单篇 Wiki 示例：

```md
---
id: workflow-codex-shadow-distill
type: workflow
updated_at: 2026-04-09
tags: [codex, distill, lora]
source_tasks:
  - 2026-04-09-task-0001
---

# Codex Shadow Distill Workflow

## Summary
...

## Stable Pattern
...

## Reuse Conditions
...
```

### 6.3 Dataset Builder

`Dataset Builder` 负责从任务日志和 Wiki 中提取高质量训练样本。

职责：

- 清洗低质量日志
- 去除敏感信息
- 结构化生成训练样本
- 合并文本推理样本与执行样本
- 为不同训练目标生成不同数据集

建议支持三类数据：

- `sft_reasoning.jsonl`
- `sft_execution.jsonl`
- `memory_update.jsonl`

样本格式建议：

```json
{
  "task_id": "2026-04-09-task-0001",
  "input": "用户要构建 Lume 文档目录并保存白皮书。",
  "target": "创建 lume/docs 并写入 whitepaper-v1.md。",
  "metadata": {
    "route_mode": "cloud",
    "value_score": 0.92,
    "source": "shadow_log"
  }
}
```

### 6.4 Distill Pipeline

`Distill Pipeline` 负责将高价值样本蒸馏到本地模型。

职责：

- 读取训练数据集
- 执行 LoRA/PEFT 微调
- 产出可版本化的 Adapter 权重
- 记录训练配置与评估结果

建议输出目录：

```text
data/distilled/
  gemma4-lora-v1/
    adapter_config.json
    training_args.json
    metrics.json
    checkpoints/
```

建议训练记录项：

- 基础模型版本
- 训练数据版本
- 训练时间
- 超参数
- 评估指标
- 样本数量
- 数据来源任务范围

### 6.5 Local Router

`Local Router` 负责决定任务应由云端、本地或混合模式处理。

建议初版采用规则路由，而不是一开始就使用复杂学习路由器。

初版判断维度：

- 任务复杂度
- 是否涉及代码执行
- 是否需要联网信息
- 是否涉及敏感数据
- 是否存在高相似历史任务
- 当前网络状态
- 当前成本预算

建议路由结果：

- `cloud`
- `hybrid`
- `local`

建议规则示例：

- 新领域复杂任务默认 `cloud`
- 高相似、低风险、高频任务默认 `local`
- 敏感执行任务优先 `hybrid`
- 云端不可达时强制 `local`

### 6.6 Codex Execution Loop

`Codex Execution Loop` 是系统的行动引擎。

职责：

- 接收任务目标
- 结合路由结果选择执行模式
- 进行代码、文件、脚本、终端操作
- 输出结果与修改记录
- 将执行过程反馈给日志和记忆模块

这一层需要保持清晰的输入输出边界：

- 输入：任务描述、上下文、路由模式、历史记忆
- 输出：执行结果、文件变更、工具调用轨迹、结果摘要

## 7. 脚本职责建议

### 7.1 `collect_shadow_logs.py`

负责把单次任务的上下文、输入输出、工具轨迹和结果整理成标准任务目录。

输入：

- 原始交互记录
- 工具执行信息
- 文件变更摘要

输出：

- `data/task_runs/<task_id>/...`

### 7.2 `build_wiki_entries.py`

负责从高价值任务日志中生成或更新 Wiki 条目。

输入：

- 任务日志目录
- 已有 Wiki 目录

输出：

- 新增或更新后的 `data/wiki/*.md`

### 7.3 `build_distill_dataset.py`

负责从任务日志和 Wiki 提炼训练样本。

输入：

- `data/task_runs/`
- `data/wiki/`

输出：

- `data/datasets/*.jsonl`

### 7.4 `train_lora.py`

负责读取数据集并训练 LoRA。

输入：

- 基础模型
- 数据集路径
- 训练配置

输出：

- `data/distilled/<run_name>/`

### 7.5 `evaluate_local_model.py`

负责比较蒸馏前后模型在代表性任务集上的表现。

建议评估维度：

- 指令遵循
- 结构化输出质量
- 本地高频任务命中率
- 执行步骤合理性
- 与历史偏好一致性

### 7.6 `route_task.py`

负责基于规则和上下文输出任务路由决策。

输入：

- 任务描述
- 预算和网络状态
- 历史相似度结果

输出：

- `cloud` / `hybrid` / `local`

## 8. 数据流设计

建议的主数据流如下：

```text
User Task
  -> Local Router
  -> Cloud/Hybrid/Local Decision
  -> Codex Execution Loop
  -> Shadow Logging
  -> LLM Wiki Memory Update
  -> Dataset Builder
  -> Distill Pipeline
  -> Local Model Evaluation
  -> Router Feedback
```

这条链路的关键是闭环。没有闭环，日志只是日志，模型只是模型，无法形成真正的 Token 资产化。

## 9. 配置文件建议

### 9.1 `configs/models.yaml`

用于定义：

- 云端模型别名
- 本地基础模型路径
- LoRA 权重路径
- 推理参数

### 9.2 `configs/routing.yaml`

用于定义：

- 路由优先级规则
- 成本阈值
- 相似度阈值
- 网络异常降级策略

### 9.3 `configs/retention.yaml`

用于定义：

- 日志保留策略
- 数据脱敏规则
- 高价值任务筛选阈值
- Wiki 更新频率

## 10. V1 评估方案

`V1` 需要至少定义一套最小可验证指标。

建议指标分为四类。

### 10.1 记录质量

- 任务日志是否完整
- 工具轨迹是否可重放
- 文件变更是否可追踪

### 10.2 知识沉淀质量

- Wiki 条目是否结构化
- 用户偏好是否可复用
- 历史任务是否可检索

### 10.3 蒸馏效果

- LoRA 微调后是否提升相似任务表现
- 是否减少对云端的重复依赖
- 是否提升本地任务完成率

### 10.4 经济效果

- 相似任务云端调用比例是否下降
- 平均 Token 消耗是否下降
- 用户对“能力资产积累感”的主观反馈是否提升

## 11. 开发阶段建议

### Phase 1：目录与数据标准

完成以下事项：

- 建立目录结构
- 定义任务日志格式
- 定义 Wiki 格式
- 定义数据集格式

### Phase 2：日志与记忆

完成以下事项：

- 实现 `Shadow Logging`
- 实现 Wiki 自动更新
- 建立高价值任务筛选逻辑

### Phase 3：数据集与训练

完成以下事项：

- 实现数据集生成脚本
- 实现 LoRA 训练脚本
- 建立最小评估集

### Phase 4：本地接管

完成以下事项：

- 实现初版 `Local Router`
- 接入本地模型推理
- 在高相似任务上启用本地优先

### Phase 5：迭代优化

完成以下事项：

- 优化样本筛选
- 优化路由效果
- 优化本地模型评估
- 优化日志和记忆质量

## 12. 风险控制

`V1` 最容易失败的点主要有四类：

- 日志采集不完整，导致后续无法蒸馏
- Wiki 结构过松，导致知识沉淀不可复用
- 数据集质量差，导致 LoRA 学到噪声
- 路由策略过早复杂化，导致系统行为不可预测

因此建议在 `V1` 坚持以下原则：

- 结构先于规模
- 规则先于学习
- 质量先于数量
- 可追踪先于自动化

## 13. V1 交付物清单

建议 `V1` 至少交付以下产物：

- 一套目录结构
- 一套任务日志标准
- 一套 Wiki 标准
- 一套数据集构建脚本
- 一套 LoRA 训练脚本
- 一套路由规则配置
- 一套最小评估方案
- 一份运行示例

## 14. 一句话定义

`Lume Sentinel 技术实施方案 V1` 的目标，是把“Token 即资产”从概念变成工程闭环：让一次高价值云端任务，能够被记录、沉淀、蒸馏，并最终转化为可由本地模型复用的长期能力。

