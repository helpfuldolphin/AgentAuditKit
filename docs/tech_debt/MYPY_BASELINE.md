# Mypy Baseline (Deferred)

Status: Deferred by scope rule  
Decision: Week-2 and Week-4 gates prioritize deterministic replay contract over full typing cleanup.

## Current Baseline (`mypy src`)

Count: 5 errors across 3 files

1. `src/aak/vault/store.py:334`  
   `Missing type parameters for generic type "dict" [type-arg]`
2. `src/aak/vault/store.py:337`  
   `Returning Any from function declared to return "dict[Any, Any]" [no-any-return]`
3. `src/aak/vault/export.py:252`  
   `Unused "type: ignore" comment [unused-ignore]`
4. `src/aak/intercept/openai_client.py:24`  
   `Cannot find implementation or library stub for module named "openai" [import-not-found]`
5. `src/aak/intercept/openai_client.py:25`  
   `Cannot find implementation or library stub for module named "openai.types.chat" [import-not-found]`

## Scope Rationale

- These errors pre-date replay-core implementation.
- They do not block deterministic replay correctness in `src/aak/replay`.
- They are tracked here to avoid silent debt while preserving v0.1 execution velocity.

## Remediation Window

- Target window: post week-4 replay gate, before pilot hardening.
- Priority order:
  1. `src/aak/vault/store.py` typing fixes
  2. `src/aak/vault/export.py` ignore cleanup
  3. `openai` typing strategy (`types` dependency or guarded protocol stubs)
