# Built for the Worksite: From "Library Researcher" to "Always-On Teammate"
## How Local AI Engineering Needs to Change

Over the past two years, the AI industry has become increasingly comfortable with a simple assumption: bigger parameter counts mean better models, longer context windows mean better reasoning, and more complex architectures mean better intelligence. But if we shift our attention away from benchmark charts and into real engineering practice, a different reality appears.

The biggest weakness of local models is often not a lack of knowledge. It is a lack of situational awareness and state continuity.

That is the most important lesson from the latest full-history comparison inside `Lume Treasury`. We replayed the full retained session history and asked local `Gemma 4` to respond where the cloud model had already responded in real work. What emerged was not a simple “local is weaker than cloud” story. The deeper problem was much more specific: Gemma often behaved like a model outside the worksite, while the cloud behaved like a teammate inside it.

If the cloud model is like a seasoned foreman on a live construction site, able to react to the current project state, command history, file changes, and task flow, then the current Gemma often resembles a well-informed intern working in a library. It knows things. It explains things. But it does not always convert that knowledge into the next on-site action.

That is why this effort is not really about making Gemma “smarter” in the generic sense. It is about making it more site-aware.

## 1. Why Parameters Are Not the Answer

Many local-model improvement efforts still follow an old instinct: add more data, add more parameters, widen the scope, and hope the system becomes generally stronger. That approach is not useless, but in engineering environments it often misses the point.

Engineering work does not primarily reward a model for generating long, complete answers. It rewards a model for choosing the correct next action under a specific state.

A model may be articulate, structured, and knowledgeable, but if it repeatedly asks for context that is already present, restarts the task from scratch, or turns operational instructions into general tutorials, then it is not acting like a teammate. It is acting like a consultant with no awareness of the room it is standing in.

This is why the weaknesses we observed in Gemma cannot be fixed by parameter growth alone. The issue is not that it lacks encyclopedic knowledge. The issue is that it does not yet maintain project state the way a real worksite agent must.

## 2. The First Necessary Shift: Training Data Must Become Stateful

Traditional SFT datasets flatten the world. They reduce behavior into decontextualized `User -> Assistant` pairs. That is exactly the kind of data that teaches a model to respond in a generic, broadly helpful tone while failing to pick up a live thread.

In a real engineering session, the input to a short command like “continue” should never be just the word “continue.” It should be paired with the surrounding environment:

- the previous few turns
- the most recent successful patch event
- current file state
- recent command outcomes
- the immediate working objective

This is the reason we built new `on-site alignment` datasets inside `Lume Treasury`. We now generate:

- `onsite_alignment_sft.jsonl`
- `developer_chain_sft.jsonl`
- `onsite_alignment_dpo.jsonl`

These records are not plain Q&A. They include:

- `Session_History`
- `Internal_Events`
- `Current_State`
- the current short instruction

This changes what the model is being asked to learn. It is no longer being trained only to produce a plausible answer. It is being trained to continue a live stateful process.

## 3. The Most Valuable Signal Is the Negative Contrast

One of the most useful assets in the system now is not just the cloud output itself, but the gap between the cloud response and Gemma’s local response.

From `gemma_vs_cloud_all_sessions.json`, we now have a large pool of examples where:

- the cloud continued the active task
- Gemma produced a generic explanation
- the cloud stayed short and execution-aware
- Gemma drifted into tutorial mode or asked for already-available information

That is exactly the kind of contrast a local model needs.

The point is not just to show the model “a better answer.” The point is to show the model that its original instinct was the wrong mode of behavior. This is why negative contrast matters so much. It does not only train correctness. It trains correction.

In practical terms, one of the most important penalty rules is this: if the context already contains the necessary material, the model should be penalized for asking the user to restate it.

In a chat assistant, “please provide the article” may seem polite. In an engineering loop, it is a sign that the model has already lost the thread.

## 4. Architecture Has to Explicitly Inject Worksite State

Even if a local model technically receives long context, that does not mean it uses it well. In local inference, context utility often decays quickly. The model sees information without truly binding that information into a working state.

That is why prompt engineering alone is not enough. The system itself needs to inject state explicitly.

Inside `Lume Treasury`, we now add a `<field_report>` before local planning. This report can include:

- inferred working directory
- latest command result
- pending task
- current focus
- latest reasoning snapshot
- latest patch snapshot
- recent file path

This is not cosmetic prompt decoration. It is an attempt to force the local model to recognize that it is not sitting in a generic chatroom. It is operating inside a live, stateful, partially unfinished environment.

We also added short-command expansion. When the user gives a very short instruction such as “continue,” “ship it,” or “next,” the system automatically expands that prompt with recent task state, file changes, and command results before local inference.

The goal is simple: transform a short instruction from an ambiguous token into a stateful continuation trigger.

## 5. Internal Collaboration Chains Need Their Own Alignment Layer

Another important discovery is that `developer/codex -> cloud` messages should not be treated as ordinary dialogue. They behave more like protocol traffic or action-level control messages.

When the model sees inputs like:

- approved
- continue
- commit this
- only push these files

the ideal response is not a full explanation. It is brief, stateful, and action-oriented.

That is why we split these records into a separate dataset, `developer_chain_sft.jsonl`. This allows the local model to learn a crucial distinction: sometimes it is talking to a user, and sometimes it is participating in an internal execution chain.

Those are not the same task, and they should not be optimized as if they were.

## 6. Evaluation Must Move from Similarity to Closure

An average similarity score of `0.0768` is already enough to show that ordinary text similarity metrics are not telling us what matters in engineering scenarios.

What matters is not whether the local model says approximately the same thing. What matters is whether it closes the same intent.

A more useful evaluation framework should ask:

- did it trigger the correct function call?
- did it preserve the right parameter structure?
- did it keep the response close to the cloud’s closure length?
- did it reference the current session’s actual files, symbols, and state?
- when asked to “continue,” did it continue the right thing?

This is a shift from language matching to action alignment.

That shift is essential if local models are going to become reliable engineering partners rather than impressive demo systems.

## 7. The Real Paradigm Shift: From Temporary Consultant to Always-On Teammate

The most important conceptual change here is that we should stop optimizing local models to be better chat consultants and start optimizing them to be better at “reading the save file.”

That metaphor is the right one.

The model does not just need to understand the latest user utterance. It needs to understand the state archive of the ongoing work:

- what commands were run
- which files changed
- what is currently active
- what has already succeeded
- what the user is ultimately trying to accomplish

This is the difference between a model that can answer and a model that can stay in character as a teammate.

`Lume Treasury` is already moving in the right direction here. The goal is not to train a Gemma that chats more beautifully. The goal is to train a Gemma that keeps the thread.

## 8. The Most Concrete Next Step

If there is one high-leverage next step, it is this: turn the **8,766 process events** into state-chain supervision.

Those events are not noise. They are the hidden basis from which the cloud model’s concise answers emerge. The user may only say “continue,” but the cloud can continue intelligently because it is implicitly standing on:

- branch creation history
- file edits
- test outcomes
- patch application events
- command outputs
- recent reasoning traces

If we convert those state chains into trainable samples, the local model stops learning the dictionary meaning of “continue” and starts learning what “continue” means *here*.

That is the real asset.

## 9. Conclusion: The True Value of Local AI

When we overemphasize the breadth of a model’s knowledge, we often overlook the capability that matters most in engineering work: the ability to choose the correct next action inside a specific context.

This improvement plan is ultimately about turning AI from an encyclopedic consultant into a teammate that knows how to read the state of the work.

It is not about making the model know more facts. It is about making it forget less of the session.

Only then can the local Battery Model evolve from a one-shot answer engine into an always-on collaborator that can remain inside a development flow, understand project status, and make coherent next-step decisions.

This is why the future of local AI is not just “smarter models.” It is more site-aware partners.

And in real engineering practice, that is what value looks like: when a developer says “continue,” the model should know where to continue, what to continue, and how to continue.

## Project Information

`GitHub`: [https://github.com/Oepn-Lume/Lume](https://github.com/Oepn-Lume/Lume)  
`Email`: `dspwatch@gmail.com`
