# Lume Sentinel 2026 Implementation Plan V1

## English

### Goal

This document turns the whitepaper into an executable engineering plan.  
`V1` is focused on proving a closed loop:

1. capture valuable cloud-returned interactions
2. preserve them as local datasets and memory
3. distill them into adapters
4. improve local reuse through the Battery Model

### V1 Modules

- `Shadow Logging`
- `LLM Wiki Memory`
- `Dataset Builder`
- `Distill Pipeline`
- `Local Router`
- `Codex Execution Loop`

### Recommended Directory Structure

```text
lume/
  configs/
  data/
    raw_logs/
    task_runs/
    wiki/
    datasets/
    distilled/
  docs/
  scripts/
  src/lume/
  tests/
```

### Delivery Order

1. make logging reliable
2. make memory and dataset extraction reproducible
3. make LoRA training repeatable
4. connect routing and local inference
5. evaluate Battery Model quality against cloud baselines

### Success Criteria

- real cloud traces are captured locally
- datasets can be rebuilt deterministically
- adapters can be retrained on demand
- the local model improves on repeatable task classes
- the user sees lower marginal cloud dependence over time

## 中文

### 目标

本文档将白皮书拆解为可执行的工程计划。  
`V1` 的重点是验证一个完整闭环：

1. 捕捉高价值的云端返回交互
2. 将其沉淀为本地数据集与记忆
3. 蒸馏为适配器权重
4. 通过 Battery Model 提升本地复用能力

### V1 模块

- `Shadow Logging`
- `LLM Wiki Memory`
- `Dataset Builder`
- `Distill Pipeline`
- `Local Router`
- `Codex Execution Loop`

### 建议目录结构

```text
lume/
  configs/
  data/
    raw_logs/
    task_runs/
    wiki/
    datasets/
    distilled/
  docs/
  scripts/
  src/lume/
  tests/
```

### 交付顺序

1. 先把日志记录做稳定
2. 再让记忆和数据集提取可重复
3. 再让 LoRA 训练可重复执行
4. 接入路由和本地推理
5. 用真实云端基线评估 Battery Model 质量

### 成功标准

- 真实云端轨迹能稳定落到本地
- 数据集可以确定性重建
- 适配器可以按需重训
- 本地模型在可重复任务上确实提升
- 用户能感知到边际云端依赖下降
