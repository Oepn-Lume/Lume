---
id: gemma-vs-cloud-process-events
type: analysis
section: gemma-vs-cloud
---

# Process Event Coverage

## Summary
The comparison preserved non-chat process events so the wiki retains the codex/cloud working chain, not just final replies.

## Details
- Top supplemental events: {'codex_event:task_started': 208, 'codex_event:user_message': 226, 'codex_event:token_count': 1943, 'codex_response_item:reasoning': 741, 'codex_event:agent_message': 783, 'codex_event:task_complete': 204, 'codex_response_item:function_call': 1414, 'codex_response_item:function_call_output': 1413, 'codex_event:exec_command_end': 1117, 'codex_event:web_search_end': 33, 'codex_response_item:web_search_call': 33, 'codex_event:turn_aborted': 3, 'codex_response_item:custom_tool_call': 170, 'codex_event:patch_apply_end': 147, 'codex_response_item:custom_tool_call_output': 170, 'codex_event:context_compacted': 7, 'codex_event:collab_agent_spawn_end': 79, 'codex_event:collab_waiting_end': 16, 'codex_event:collab_close_end': 54, 'codex_event:error': 4, 'codex_event:thread_rolled_back': 1}
- Function calls, function-call outputs, reasoning traces, command completion events, and patch events are all retained.
- These events are essential if the local model is meant to learn how cloud collaboration actually progresses through work.

