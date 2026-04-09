# Battery Model V1

## English

### Definition

`Battery Model = Gemma4 31B + Sentinel-LoRA`

In `Lume`, the Battery Model is the local continuation layer that absorbs cloud-returned intelligence and keeps working when cloud access is slow, unavailable, or too expensive.

### Components

- `Base Model`: `gemma4:31b` served locally through `Ollama`
- `Adapter Layer`: `Sentinel-LoRA`, distilled from real cloud dialogues, bootstrap guidance, execution traces, code outputs, and patch events
- `Runtime Role`: low-latency inference, offline continuity, and repeat-task reuse
- `SOH`: state-of-health style evaluation against stronger cloud baselines

### Data Sources

- `real_cloud_dialogue_sft.jsonl`
- `real_cloud_bootstrap_sft.jsonl`
- `real_cloud_full_fidelity_sft.jsonl`
- `real_code_execution_sft.jsonl`

### Current Status

The Battery Model definition is fixed at the project level, but the runtime still needs deeper routing integration so that `gemma4:31b` can take over selected real tasks automatically.

## 中文

### 定义

`Battery Model = Gemma4 31B + Sentinel-LoRA`

在 `Lume` 中，电池模型是本地续航层。它负责吸收云端返回的智能内容，并在云端变慢、不可达或成本过高时继续工作。

### 组成

- `基座模型`：通过 `Ollama` 本地运行的 `gemma4:31b`
- `适配层`：`Sentinel-LoRA`，由真实云端对话、启动指导、执行轨迹、代码输出和补丁事件蒸馏而来
- `运行时角色`：低延迟推理、离线续航与重复任务复用
- `SOH`：对比强云端基线的健康度评估机制

### 数据来源

- `real_cloud_dialogue_sft.jsonl`
- `real_cloud_bootstrap_sft.jsonl`
- `real_cloud_full_fidelity_sft.jsonl`
- `real_code_execution_sft.jsonl`

### 当前状态

电池模型的定义已经在项目内固定下来，但运行时仍需要更深入的路由接入，才能让 `gemma4:31b` 自动接管被选中的真实任务。
