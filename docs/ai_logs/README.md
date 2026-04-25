# AI Logs README

This folder should contain exported full AI responses and conversation logs used during the TraceFix project.

The course AI usage policy requires submitted work to include exact prompts and the AI tool's full responses in an appendix. `docs/ai_prompt_appendix.md` records the prompt inventory and points to this folder when full responses are too large to include directly in the appendix.

## Recommended Files

Use clear filenames such as:

- `chatgpt_phase_planning_export.md`
- `codex_repository_tasks_export.md`
- `claude_code_task_log.md`
- `gemini_review_notes.md`
- `minimax_drafting_notes.md`
- `grok_brainstorming_notes.md`

## What To Include

Each exported log should include:

- tool name and model/version shown in the UI
- prompt text
- full AI response
- date or session identifier if available
- short note explaining which TraceFix task the log supports

## Why These Logs Matter

The logs support course compliance by showing:

- what was asked of each AI tool
- what content or code suggestions the AI returned
- which parts were later reviewed, edited, tested, or rejected by the team
- that the final repository did not depend on unverified AI claims

## How To Reference Logs

After adding exported logs, update `docs/ai_prompt_appendix.md` so each prompt record points to the exact file and section containing the response.

Example:

```md
Full response location: `docs/ai_logs/codex_repository_tasks_export.md#p009-phase-3-feedback-repair`
```

If a response log is unavailable, do not recreate it from memory. Leave a compliance warning in the appendix explaining that the exported AI conversation log was not found in the repository.
