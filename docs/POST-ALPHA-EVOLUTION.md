# Post-Alpha Evolution

Status: **FUTURE / AFTER STABLE OPERATIONAL ALPHA**, not active model training or performance optimization. Owner priority 2026-10-18: [Cloud–Desktop–Phone first](DELIVERY-PLAN.md), then dedicated home-server laptop, then physical Edge. The dedicated laptop may be connected in Group 7 after an operational alpha; ongoing post-alpha learning/optimization still requires measured stability.

This document records the owner-approved direction for what OSCAR becomes after
Slice 20 Unified Alpha is genuinely stable in everyday use. It is not a claim
that these systems exist today, and it does not weaken any current Gate/acceptance
requirement.

## 1. Cross-platform Voice Core is a current architectural invariant

OSCAR Voice must remain surface-independent.

The same Voice Core contracts for wake/VAD, STT, Voice Identity, TTS, barge-in,
self-voice suppression, Voice Match, Voice Map, Persona, policy and arbitration
must be reusable across:

- Windows desktop/reference runtime;
- OSCAR Mobile on Android;
- Linux and macOS desktop nodes;
- future Home Node/server surfaces;
- future physical/embedded surfaces where the hardware class is appropriate.

Platform-specific code belongs behind adapters for capture/playback, audio-session
control, echo cancellation, permissions, Bluetooth/headset routing, lifecycle and
hardware acceleration.

**Windows is the current reference implementation, not the architecture.**
Android/OSCAR Mobile is a first-class target and must not require redesigning Voice Core.
A platform is VERIFIED only after real acceptance on that platform.

## 2. Stable alpha usage produces operating telemetry

After Unified Alpha is stable enough for normal owner use, OSCAR should gain an
owner-controlled **Operating Log** / telemetry layer.

Operating telemetry is different from conversation recording, Context Capture,
Daily Journal and Memory.

It records how OSCAR operated, for example:

- model/provider selected and why;
- local vs cloud route;
- tool, Skill, plugin, MCP, connector or capability invoked;
- Worker/sub-agent used;
- start/end time and latency;
- retries, fallbacks, cancellation and recovery;
- token/compute/resource usage where measurable;
- permission/policy decisions;
- task/result verification state;
- failures, quality flags and owner corrections;
- capability gaps where OSCAR could not complete useful work;
- orchestration decisions and escalation paths.

By default, Operating Logs should prefer structured metadata, hashes/IDs and
quality/outcome signals rather than raw conversation or private document content.
Secrets, credentials, raw audio and unrelated personal content must not be logged.

Conversation/capture retention and operating telemetry remain separate permissions
and separate retention controls.

Operating Logs do **not** silently become training data. Promotion of any owner
data into a training/evaluation dataset requires explicit owner authorization,
redaction/minimization, provenance and a defined removal path.

## 3. Improvement loop driven by real use

The long-term loop is:

```text
stable alpha used normally
        ↓
owner-controlled Operating Logs
        ↓
find repeated latency / quality / capability gaps
        ↓
cluster recurring task families
        ↓
benchmark current local + cloud paths
        ↓
propose better workflow / Skill / model
        ↓
owner approval
        ↓
train / fine-tune / distill / optimize where justified
        ↓
evaluate against held-out real task shapes
        ↓
register behind OSCAR contracts
        ↓
canary → verify → promote or roll back
```

Optimization follows observed use instead of guessing what deserves its own model.

## 4. Voice Evolution track — informed by Elocution

The separate Elocution research project is a source of findings for OSCAR's future
Voice Identity work. It is not a mandatory OSCAR runtime dependency.

The target is a natural, expressive, recognizably OSCAR voice across all surfaces:

- natural timing and pauses;
- controllable prosody and modulation;
- emotional range without theatrical overacting;
- stable identity across devices/providers;
- low first-audio latency;
- streaming and prompt cancellation;
- strong barge-in and self-voice suppression;
- graceful quality/compute modes;
- local execution where practical.

The goal is to learn from expressive-voice experiments, not to make OSCAR an exact
celebrity impersonation. Voice Identity remains an original, provider-independent
OSCAR asset.

Any future expressive-voice stack must be benchmarked on desktop, Android/OSCAR Mobile
and the Home Node target rather than optimized only for Windows.

## 5. Specialist Model Fabric — small models before one giant local model

OSCAR should not assume that one large general-purpose model is the best local
answer for every recurring task.

After enough real usage evidence exists, OSCAR may develop smaller models optimized
for specific task families where general models repeatedly underperform, cost too
much, respond too slowly or require unnecessary cloud escalation.

Candidate families may include, only when logs/evals justify them:

- document creation and structured editing;
- presentation/deck planning and artifact generation;
- research/evidence triage;
- tool selection and capability routing;
- calendar/task/communication operations;
- browser/computer-use planning;
- code/repository operations;
- memory/retrieval/reranking;
- voice turn handling;
- verification/critique;
- orchestration and Worker selection.

A specialist model is promoted because measured task performance is better for its
scope, not merely because it is smaller.

Models must remain replaceable behind OSCAR contracts. Each specialist needs:

- explicit task boundary;
- benchmark/evaluation set;
- quality and failure criteria;
- provenance/licensing review;
- resource/latency profile;
- authority/permission boundary;
- fallback/escalation route;
- rollback/versioning.

The owner rationale is reinforced by the recent Ajax/Odysseus direction: a compact
Qwen3.5-9B model is being tuned specifically for an always-on self-hosted agent
workspace. OSCAR treats that as evidence that specialization is worth testing, not
proof that the same recipe will automatically work here.

## 6. Singularity direction

This aligns with the owner's Singularity direction:

> one OSCAR experience composed from a coordinated set of specialized local
> intelligences rather than forcing every problem through one monolithic model.

To the user it remains one continuous OSCAR. Internally, the Controller/Router may
compose task-specific models, deterministic systems, retrieval, tools and Workers.

Over time even orchestration itself should migrate toward measured, optimized local
models where they can match the required quality and truthfulness.

## 7. Home-server end state

The intended long-term primary deployment is an owner-controlled dedicated home
server laptop, **not the current development laptop**.

Where hardware permits, that host should eventually run:

- persistent OSCAR Core/coordinator;
- Memory Fabric and indexes;
- Operating Logs/observability;
- local Model Router;
- specialist model pool;
- local STT/TTS/Voice Identity services;
- durable Workers and queues;
- artifact/document services;
- home/device coordination.

The baseline daily OSCAR experience should progressively stop depending on cloud
models.

Cloud models remain available for:

- genuinely difficult or high-value work;
- frontier capability not yet available locally;
- temporary fallback/recovery;
- benchmarking/teacher/evaluation workflows where terms and policy permit;
- major orchestration while local orchestration is still maturing.

Cloud escalation must stay explicit, policy-aware and replaceable. "Local-first"
does not mean refusing a stronger cloud model when the owner intentionally wants it.

## 8. Privacy and training boundary

Operating telemetry exists to improve OSCAR, but private ownership remains primary.

Rules:

1. telemetry and conversation content are separate data classes;
2. collect the minimum useful operational metadata;
3. no secrets/credentials in logs;
4. no silent training on private logs/conversations;
5. owner can inspect/export/delete telemetry subject to truthful storage limits;
6. training/eval datasets require explicit promotion and provenance;
7. external model outputs may be used for training only when provider terms,
   licensing and policy permit;
8. synthetic/public/licensed data is preferred when it can answer the research
   question without exposing private owner data.

## 9. Post-alpha phases

These phases begin only after Unified Alpha is stable enough for real sustained use.

### P1 — Operating Intelligence
Implement local Operating Logs, dashboards/queries, retention controls and task-gap
analysis.

### P2 — Voice Evolution
Bring measured Elocution findings into OSCAR Voice Identity and benchmark expressive
local voice across Windows, Android/OSCAR Mobile and Home Node hardware.

### P3 — Specialist Model Fabric
Use real task clusters and evals to build/register small optimized models. Start
with the clearest repeated gaps rather than pretraining a large suite speculatively.

### P4 — Home-server independence
Move persistent Core, memory, voice, specialist models and increasing orchestration
onto the dedicated home-server laptop. Reduce cloud use to intentional escalation.

## 10. Success condition

This direction succeeds when OSCAR becomes more capable from measured real use
while remaining one coherent intelligence, locally operable, portable across
surfaces, evidence-backed and owner-controlled.

## Current Slice 08 quality pass boundary — 2026-10-06

The [local voice quality pass](VOICE-QUALITY.md) applies the current portability
invariant and reuses Elocution's identity/delivery separation without importing a
celebrity identity. This does not implement Operating Logs, specialist-model
training or home-server migration. Those remain future after stable Unified Alpha.
Physical voice acceptance is owner-deferred to the
[consolidated Gate C run](GATE-C-CONSOLIDATED-ACCEPTANCE.md); Gate C remains PARTIAL.

## Numbering note — 2026-10-09

The canonical Unified Alpha milestone is now **Slice 20**, previously
Slice 17. This post-alpha roadmap remains unchanged in substance and
starts only after the revised Slice 20 is stable. See
[canonical slice map](SLICE-NUMBERING.md).
