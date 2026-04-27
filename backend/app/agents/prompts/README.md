# Agent Prompts

Each agent loads its system prompt from a `.system.md` file in this directory
at startup. Keeping prompts as files (not Python string literals) means:

- Designers can iterate on wording without a code review.
- Prompt versions can be checked into git separately and A/B tested.
- A future eval pipeline can hash + cache prompts independently.

Files:

| File | Owner |
|---|---|
| `interpreter.system.md` | ActionInterpreter |
| `validator.system.md` | DomainValidator |
| `npc_director.system.md` | NPCDirector |
| `consequence_engine.system.md` | ConsequenceEngine |

The Mentor Coach reuses prompts from `app/ai/prompt_builder.py` — no separate
file needed (the existing personas already work).

These files are written in Phase 1; this README is a placeholder so the
directory is present in source control.
