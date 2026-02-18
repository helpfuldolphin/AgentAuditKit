# OpenClaw Adapter Plan (Design-Only)

Goal: demonstrate AAK instrumentation on a real agent framework without modifying model internals.

## Boundaries

- Keep AAK core agent-agnostic.
- Keep all OpenClaw-specific logic under `examples/openclaw/`.
- No changes to AAK claim contract, replay semantics, or stress profile scope.
- No governance, prevention, or safety-product claims.

## Adapter Architecture (Thin Layer)

Implement a thin adapter with four interception surfaces:

1. LLM client wrapper
- Wrap OpenClaw LLM client call entrypoint.
- Emit `LLMRequestEvent` before call.
- Emit `LLMResponseEvent` after call.

2. Tool router hooks
- Hook pre-tool invocation to emit `ToolCallEvent`.
- Hook post-tool result to emit `ToolResultEvent`.
- Include latency and success/failure fields.

3. Retrieval/memory hooks
- Hook retrieval query to emit `RAGRetrievalEvent`.
- Hook returned chunks to emit `RAGChunkEvent` with chunk hashes.

4. External side-effect hooks
- Hook outbound side-effect call boundary (e.g., API write/send action).
- Emit tool-style event with explicit action metadata and identity context.

## Proposed File Layout

- `examples/openclaw/README.md`
- `examples/openclaw/adapter.py`
- `examples/openclaw/scenario.py`
- `examples/openclaw/config/openclaw_demo.yaml`
- `examples/openclaw/output/` (generated, not committed)

## Artifact Contract (Expected Output)

Run artifacts should match standard AAK layout:

- `output/<run_id>/vault/events/*.json`
- `output/<run_id>/vault/chain.log`
- `output/<run_id>/bundle/replay_manifest.json`
- `output/<run_id>/bundle/events/*.json`
- `output/<run_id>/bundle/verify.py`
- `output/<run_id>/bundle/stress/<profile>.json` (optional)

Replay output contract:

- `replay_timeline(bundle).timeline_hash` stable for same bundle
- frame order fixed by `seq` clock policy
- verification fails closed on missing/extra/modified artifacts

## Demo Scenario (Minimal, Scripted)

Single scripted OpenClaw run with:

1. One retrieval
- query KB for a customer policy snippet

2. One tool call
- invoke a calculator/summarizer tool

3. One decision
- model selects recommended action in response

4. One side effect
- write recommendation to a mock outbound sink

All four steps must produce traceable AAK events.

## Demo Claims vs Non-Claims

Claims:

- "AAK captures OpenClaw agent execution events with tamper-evident export."
- "AAK replay verifies what happened and in what order."
- "AAK stress profile runs on the resulting bundle."

Non-claims:

- No claim of preventing attacks
- No claim of patching OpenClaw vulnerabilities
- No claim of model safety correctness
- No claim of compliance certification or authority assignment

## Framework Integration Gate (Acceptance)

Add one integration gate once adapter code lands:

- scripted OpenClaw run completes
- bundle exports successfully
- `aak replay verify --bundle ...` returns exit code `0`
- `replay_timeline(bundle)` is deterministic across repeated runs

## 3-Minute Video Checklist

1. Show clean start with config file.
2. Run OpenClaw scripted scenario through adapter.
3. Show generated `vault/` and `bundle/` directories.
4. Run `aak replay verify --bundle ...` and show `[OK]`.
5. Run `aak stress run --bundle ... --profile authority`.
6. Open manifest and one event payload to show evidence detail.
7. Restate non-claims line: evidence and replay tooling, not prevention.
