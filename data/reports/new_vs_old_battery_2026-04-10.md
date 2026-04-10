# New vs Old Battery Strategy Benchmark

- Expert Report: `C:\Users\yh-PC-003\Desktop\codex\lume\data\reports\expert_adapter_pipeline_report.json`
- Total Matched Examples: `12`

## Headline

- New avg char match: `0.0338` vs old `0.0507`
- New avg similarity: `0.0216` vs old `0.1602`
- New prefix match rate: `0.0` vs old `0.0833`
- New wins: `3` / Old wins: `9` / Ties: `0`

## Per Dataset

| Dataset | Examples | New Char Match | Old Char Match | New Similarity | Old Similarity | New Wins | Old Wins |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `continue` | 4 | 0.0796 | 0.0558 | 0.0018 | 0.0215 | 3 | 1 |
| `patch` | 4 | 0.0107 | 0.0423 | 0.0315 | 0.2708 | 0 | 4 |
| `log` | 4 | 0.0112 | 0.054 | 0.0316 | 0.1883 | 0 | 4 |

## New Strategy Win Samples

### `continue` · `continue-pipeline-demo-continue-augment`
- Action Label: `continue_task`
- Old Expert: `base-expert`
- New Expert: `base-expert`
- New Cascade: `base-expert -> code-expert -> logic-expert`
- Target: `Continue from the current task state, acknowledge the latest status and artifacts, prioritize the pending work for 'write a system architecture summary with ...`
- Old: `**Task Status:** Completed **Artifact:** `examples/task_samples/write-a-system-architecture-summary-with-python-code-pipeline-demo.md` **Logical Verification...`
- New: `: _ : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : :`

### `continue` · `debug-this-python-code-patch-pipeline-demo-continue-augment`
- Action Label: `continue_task`
- Old Expert: `code-expert`
- New Expert: `code-expert`
- New Cascade: `code-expert -> base-expert`
- Target: `Continue from the current task state, acknowledge the latest status and artifacts, prioritize the pending work for 'debug this python code patch', and take t...`
- Old: `Since the previous goal of debugging the Python code patch is marked as **completed**, the objective now shifts from implementation to final validation and c...`
- New: `: are the code - expert '.. : are the code - expert '.. : are the code - expert '.. : are the code - expert '.. : are the code - expert '.. : are the code - ...`

### `continue` · `demo-inline-continue-augment`
- Action Label: `continue_task`
- Old Expert: `base-expert`
- New Expert: `base-expert`
- New Cascade: `base-expert`
- Target: `Continue from the current task state, acknowledge the latest status and artifacts, prioritize the pending work for 'Verify shadow logging inline.', and take ...`
- Old: `The verification of shadow logging inline has been completed successfully. As there are currently no pending tasks in the queue, I am ready for the next obje...`
- New: `address _ : address _ : address _ : address _ : address _ : address _ : address _ : address _ : address _ : address _ : address _ : address _ : address _ : a...`
