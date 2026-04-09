# Lume Sentinel 2026

`Lume` is a local-first prototype for turning high-value AI usage into reusable assets.

## Battery Model

The working project definition is:

`Battery Model = Gemma4 31B + LoRA`

That means:

- `Gemma4 31B` is the local base model served by `Ollama`
- `LoRA` adapters are distilled from real cloud-returned sessions, bootstrap guidance, execution traces, and code outputs
- the `Battery Model` is the local continuation layer for offline, low-latency, and high-frequency tasks

Cloud models still provide first-pass premium reasoning. `Shadow Logging`, dataset building, and LoRA training convert that paid capability into reusable local assets.

## Starfire Protocol

`Lume Starfire Protocol` is the release-and-distribution layer that turns repository changes into collaborative signal.

Current implementation scope:

- repository messaging for the `Battery Model` narrative
- a GitHub Actions workflow skeleton for contribution intake and validation
- a safe `X` marketing executor that defaults to `dry-run`
- local watchman reporting so launch operations stay observable and low-anxiety

The protocol is designed to keep execution grounded:

- if the workspace is not a Git repository, release actions stop before branch/push steps
- if X credentials are not configured, the marketing executor renders plans and reports without posting
- if contributed artifacts fail validation, the workflow fails closed

## Contact

- Release contact: `dspwatch@gmail.com`

## Layout

- `docs/`: whitepaper, implementation plan, architecture appendix
- `configs/`: model, routing, retention configs
- `data/`: logs, wiki memory, datasets, distilled adapters
- `scripts/`: import, build, train, evaluate, generate entrypoints
- `src/lume/`: core Python modules
- `examples/`: example outputs and sample payloads
- `tests/`: test drafts and smoke checks

## Core Pipeline

The current minimum working loop is:

`Codex sessions / task runs -> raw logs -> datasets -> LoRA training -> Gemma4 Battery Model generation/evaluation`

Main steps:

1. Import or sync session logs
   - `python scripts/import_codex_sessions.py`
   - `python scripts/sync_codex_training_data.py --skip-train`
2. Build datasets
   - `python scripts/build_distill_dataset.py`
3. Train a local adapter
   - `python scripts/train_lora.py`
4. Generate or evaluate
   - `python scripts/generate_local_response.py --prompt "写一篇爱国散文诗"`
   - `python scripts/evaluate_local_model.py`

Recommended Battery Model stack:

- Base model: `gemma4:31b` via `Ollama`
- Adapter: `data/distilled/transformers-lora-v2-realcloud/adapter`
- Primary purpose: bootstrap guidance, full-fidelity runtime behavior, and execution-style continuation

## Shadow Logging

Available logging paths:

- Batch import from JSON or CLI arguments:
  - `python scripts/collect_shadow_logs.py`
- Runtime incremental recording:
  - `src/lume/logging/recorder.py`
  - `src/lume/execution/session.py`
  - `src/lume/execution/runtime.py`
- Codex desktop session import:
  - `python scripts/import_codex_sessions.py`
- Continuous Codex sync:
  - `python scripts/watch_codex_training_data.py --interval-seconds 30`

Structured task logs are written to `data/task_runs/<task_id>/`.

## Wiki Memory

Wiki memory is built from task logs:

- Build task pages:
  - `python scripts/build_wiki_entries.py`
- Output:
  - `data/wiki/index.md`
  - `data/wiki/log.md`
  - `data/wiki/tasks/*.md`

## Training

The default trainer is now a real `transformers + PEFT/LoRA` flow.

Recommended GPU command:

```powershell
C:\Users\yh-PC-003\Desktop\codex\wan22\venv\Scripts\python.exe scripts\train_lora.py --device cuda --model-name-or-path uer/gpt2-chinese-cluecorpussmall
```

Current Battery Model workflow:

1. Run `Gemma4 31B` locally through `Ollama`
2. Distill real Codex/cloud traces into LoRA adapters
3. Evaluate whether the adapter improves bootstrap and execution-style generations
4. Route suitable tasks to the local Battery Model

Useful options:

- `--training-mode transformers_peft_lora`
- `--model-name-or-path uer/gpt2-chinese-cluecorpussmall`
- `--model-name-or-path sshleifer/tiny-gpt2`
- `--max-samples 256`
- `--epochs 2`

Outputs are saved under `data/distilled/<run-name>/` and include:

- `adapter/`
- `tokenizer/`
- `training_config.json`
- `metrics.json`
- `sample_generation.txt`

Current best real-cloud LoRA checkpoint:

- `data/distilled/transformers-lora-v2-realcloud/`

This checkpoint is the current adapter candidate for the `Gemma4 31B` Battery Model path, even though the rapid-iteration trainer still uses a smaller transformer base during some experiments.

If a constrained environment cannot use `transformers/peft`, you can still force the old fallback:

```powershell
python scripts/train_lora.py --training-mode tiny_lm_fallback
```

## Synthetic Data Factory

Generate synthetic SFT samples:

```powershell
python scripts/generate_100k_dataset.py --task-count 1000 --provider mock
```

If a cloud key is available later:

```powershell
python scripts/generate_100k_dataset.py --task-count 1000 --provider openai
```

Synthetic outputs land in:

- `data/generated_corpus/generated_raw/`
- `data/generated_corpus/generated_scored/`
- `data/generated_corpus/generated_final/`

For a real-cloud-only campaign that must not fall back to mock data:

```powershell
C:\Users\yh-PC-003\Desktop\codex\wan22\venv\Scripts\python.exe scripts\generate_real_cloud_dataset.py --target-count 1000 --batch-size 50
```

This campaign stops immediately if a real provider is unavailable and only writes records that are marked `real_cloud=true`.

## Continuous Training Refresh

Incremental Codex sync plus retraining:

```powershell
python scripts/sync_codex_training_data.py --device cuda --model-name-or-path uer/gpt2-chinese-cluecorpussmall
```

Continuous watch mode:

```powershell
python scripts/watch_codex_training_data.py --interval-seconds 30
```

---

# Lume Sentinel 2026 中文版

`Lume` 是一个以本地优先为核心的原型系统，目标是把高价值 AI 使用过程转化为可复用、可积累、可沉淀的长期资产。

## Battery Model

当前项目的正式定义是：

`Battery Model = Gemma4 31B + LoRA`

这意味着：

- `Gemma4 31B` 是通过 `Ollama` 提供服务的本地基础模型
- `LoRA` 适配器来自真实云端返回会话、启动指导、执行轨迹与代码产物的蒸馏
- `Battery Model` 是系统在离线、低延迟和高频场景下的本地续航层

云端模型仍然负责首发高质量推理，而 `Shadow Logging`、数据集构建和 LoRA 训练负责把这些付费能力转化为本地可复用资产。

## 星火协议

`Lume Starfire Protocol` 是面向发布、协作和传播的外层协议，用来把仓库变更转化为可扩散的协作信号。

当前已经落地的范围包括：

- 围绕 `Battery Model` 的仓库叙事与发布口径
- 用于贡献接入与验证的 `GitHub Actions` 工作流骨架
- 默认 `dry-run` 的安全型 `X` 平台营销执行器
- 用于降低运营焦虑的本地守望者报告

这套协议遵循几个约束：

- 如果工作区还不是 Git 仓库，发布动作会在分支与推送前停止
- 如果没有配置 X 平台凭据，营销执行器只生成预览和报告，不会真实发帖
- 如果贡献产物未通过验证，工作流会直接失败并拒绝放行

## 联系方式

- 发布联系邮箱：`dspwatch@gmail.com`

## 目录结构

- `docs/`：白皮书、实施方案、架构附录
- `configs/`：模型、路由、保留策略配置
- `data/`：日志、Wiki 记忆、训练数据、蒸馏产物
- `scripts/`：导入、构建、训练、评估、生成脚本入口
- `src/lume/`：核心 Python 模块
- `examples/`：示例输出和样本数据
- `tests/`：测试草稿与 smoke check

## 核心流水线

当前最小可运行闭环是：

`Codex sessions / task runs -> raw logs -> datasets -> LoRA training -> Gemma4 Battery Model generation/evaluation`

主要步骤：

1. 导入或同步会话日志
   - `python scripts/import_codex_sessions.py`
   - `python scripts/sync_codex_training_data.py --skip-train`
2. 构建数据集
   - `python scripts/build_distill_dataset.py`
3. 训练本地适配器
   - `python scripts/train_lora.py`
4. 生成或评估
   - `python scripts/generate_local_response.py --prompt "写一篇爱国散文诗"`
   - `python scripts/evaluate_local_model.py`

推荐的 Battery Model 组合：

- 基座模型：通过 `Ollama` 提供的 `gemma4:31b`
- 当前适配器：`data/distilled/transformers-lora-v2-realcloud/adapter`
- 主要用途：承接启动指导、全量运行时行为以及执行风格续写

## Shadow Logging

当前支持的日志路径：

- 通过 JSON 或 CLI 参数进行批量导入
  - `python scripts/collect_shadow_logs.py`
- 运行时增量记录
  - `src/lume/logging/recorder.py`
  - `src/lume/execution/session.py`
  - `src/lume/execution/runtime.py`
- 导入 Codex Desktop 会话
  - `python scripts/import_codex_sessions.py`
- 持续同步 Codex 数据
  - `python scripts/watch_codex_training_data.py --interval-seconds 30`

结构化任务日志会写入 `data/task_runs/<task_id>/`。

## Wiki Memory

Wiki 记忆层从任务日志中构建：

- 构建任务页面
  - `python scripts/build_wiki_entries.py`
- 输出位置
  - `data/wiki/index.md`
  - `data/wiki/log.md`
  - `data/wiki/tasks/*.md`

## 训练

默认训练器已经切换为真实的 `transformers + PEFT/LoRA` 流程。

推荐 GPU 命令：

```powershell
C:\Users\yh-PC-003\Desktop\codex\wan22\venv\Scripts\python.exe scripts\train_lora.py --device cuda --model-name-or-path uer/gpt2-chinese-cluecorpussmall
```

当前 Battery Model 的工作流是：

1. 通过 `Ollama` 本地运行 `Gemma4 31B`
2. 将真实 Codex/云端轨迹蒸馏成 LoRA 适配器
3. 评估适配器是否提升了启动指导和执行风格生成效果
4. 将合适任务路由到本地 Battery Model

常用参数：

- `--training-mode transformers_peft_lora`
- `--model-name-or-path uer/gpt2-chinese-cluecorpussmall`
- `--model-name-or-path sshleifer/tiny-gpt2`
- `--max-samples 256`
- `--epochs 2`

训练输出保存在 `data/distilled/<run-name>/`，包括：

- `adapter/`
- `tokenizer/`
- `training_config.json`
- `metrics.json`
- `sample_generation.txt`

当前最佳的真实云端 LoRA 检查点是：

- `data/distilled/transformers-lora-v2-realcloud/`

这份检查点是当前 `Gemma4 31B` Battery Model 路径上的适配器候选，虽然快速迭代训练时仍会使用更小的 transformer 基座做实验。

如果在受限环境下无法使用 `transformers/peft`，仍然可以手动切回旧的 fallback：

```powershell
python scripts/train_lora.py --training-mode tiny_lm_fallback
```

## Synthetic Data Factory

生成 synthetic SFT 样本：

```powershell
python scripts/generate_100k_dataset.py --task-count 1000 --provider mock
```

如果后续配置了云端 key：

```powershell
python scripts/generate_100k_dataset.py --task-count 1000 --provider openai
```

synthetic 输出会落到：

- `data/generated_corpus/generated_raw/`
- `data/generated_corpus/generated_scored/`
- `data/generated_corpus/generated_final/`

如果要运行一个严格的真实云端数据 campaign，并且绝不回退到 mock：

```powershell
C:\Users\yh-PC-003\Desktop\codex\wan22\venv\Scripts\python.exe scripts\generate_real_cloud_dataset.py --target-count 1000 --batch-size 50
```

当真实 provider 不可用时，这个 campaign 会立即停止，只保留标记为 `real_cloud=true` 的记录。

## 持续训练刷新

增量同步 Codex 数据并重训：

```powershell
python scripts/sync_codex_training_data.py --device cuda --model-name-or-path uer/gpt2-chinese-cluecorpussmall
```

持续监听模式：

```powershell
python scripts/watch_codex_training_data.py --interval-seconds 30
```
