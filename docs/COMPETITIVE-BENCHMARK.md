# Competitive Benchmark — 2026-09-29

This document records the final architecture comparison used to freeze OSCAR's pre-implementation design. It compares OSCAR against current public capability patterns in VoiceOS, MCU JARVIS, ChatGPT, Claude, Gemini, Grok Bot, OpenClaw, Hermes Agent and Pi.

This is a benchmark, not a claim that OSCAR currently implements these capabilities. OSCAR is still at Slice 00.

## Benchmark systems

### VoiceOS

Strengths to match:

- system-wide dictation/editing;
- selected-text editing;
- cursor/screen context;
- point-and-talk interaction;
- agentic actions with confirmations;
- many first-party integrations;
- very low-friction voice interaction.

Primary lesson: **interaction quality and latency are the baseline.** OSCAR's broader architecture is not useful if Dictate/Edit/Ask/Act feels slower or more cumbersome.

References:

- https://www.voiceos.com/
- https://www.voiceos.com/blog/how-voiceos-is-building-the-voice-operating-system
- https://www.voiceos.com/changelog

### MCU JARVIS

Useful capability pattern:

- conversational interaction;
- home/lab/business infrastructure control;
- engineering/design/simulation support;
- environmental/suit diagnostics;
- sensor fusion and scene analysis;
- health/vital monitoring;
- autonomous coordination of many systems;
- persistent proactive presence.

Primary lesson: JARVIS is defined less by chat intelligence than by **shared state, perception, executive control and tool/device reach**.

Reference note: the film/research benchmark is captured in OSCAR planning; no external fan-wiki URL is embedded here because that site blocks automated link validation.

### ChatGPT

Strengths to learn from:

- long-running Work-style execution;
- finished artifacts rather than only chat replies;
- plugins/connectors/skills;
- memory across conversation and connected sources;
- cloud browser/computer-use workflows;
- scheduled and event-triggered automations.

Primary lesson: objectives should end in verified outcomes/artifacts, and background work should survive beyond a single foreground turn.

Reference note: current OpenAI product/help documentation was reviewed on 2026-09-29; direct OpenAI URLs are omitted here because the repository's automated link checker receives HTTP 403 from those documentation hosts.

### Claude

Strengths to learn from:

- automatic movement between conversation and agentic work;
- connectors-first execution with browser/computer-use fallback;
- cloud background work;
- plugins combining skills/connectors/sub-agents;
- scheduled tasks;
- increasingly deep Google Workspace operations.

Primary lesson: users should state the objective; OSCAR/Jev should choose the execution depth and best available capability rather than forcing mode selection.

References:

- https://support.claude.com/en/articles/15520349-use-claude-cowork-on-web-desktop-and-mobile
- https://support.claude.com/en/articles/10166901-use-google-workspace-connectors

### Gemini

Strengths to learn from:

- deep Google ecosystem context;
- cross-source Personal Intelligence across Gmail/Photos/Search/YouTube/Workspace/Contacts and related services;
- Android-native phone/device actions;
- always-running agent/schedule patterns;
- strong native access to calendar, mail, contacts and other personal systems.

Primary lesson: the competitive advantage is not merely individual connectors but **cross-source personal understanding tied to canonical entities and live context**.

References:

- https://blog.google/intl/en-in/products/personal-intelligence-launches-in-the-gemini-app-in-india/
- https://support.google.com/gemini/answer/16836988

### Grok Bot

Strengths to learn from:

- persistent named Bots/teammates;
- long-running execution;
- parallel coordination and handoffs;
- skills learned from completed work/demonstration;
- routines/schedules;
- approvals;
- voice and persistent context.

Primary lesson: persistent delegated Workers are valuable, but OSCAR should keep them under one identity and use the user's real device/service mesh rather than requiring a cloud computer per Worker.

Reference:

- https://docs.x.ai/grok-bot/overview

### OpenClaw

Strengths to learn from:

- self-hosted gateway architecture;
- broad communication-channel coverage;
- native/mobile nodes;
- voice/camera/screen/device actions;
- multiple model providers;
- skills/plugins;
- browser/exec;
- cron/webhooks;
- multi-agent routing;
- scalable tool/capability discovery.

Primary lesson: communication needs a **Universal Channel Gateway**, and capability discovery needs to scale beyond loading every tool into context.

Reference:

- https://github.com/openclaw/openclaw

### Hermes Agent

Strengths to learn from:

- persistent memory;
- self-created/improved skills;
- Agent Skills compatibility;
- scheduled automation;
- messaging surfaces;
- parallel delegates;
- durable multi-agent task state;
- heartbeats/reclaim/zombie detection/retries/session recovery.

Primary lesson: persistent Workers/Protocols need a serious **Durable Execution Runtime**, and learned automation needs an evaluation/promotion pipeline rather than trusting one successful run.

References:

- https://hermes-agent.nousresearch.com/docs/
- https://github.com/NousResearch/hermes-agent-self-evolution

### Pi

Strengths to learn from:

- intentionally small core;
- clear agent loop;
- multi-provider model layer;
- extensions/Skills/packages;
- embedding through SDK/RPC-style interfaces;
- refusal to bake every competitor feature into the core.

Primary lesson: OSCAR should gain breadth through stable primitives and specialist capabilities, **not by turning the core into a giant framework**.

Reference:

- https://github.com/earendil-works/pi

## Final missing primitives identified

The review produced five cross-cutting additions:

1. **Universal Channel Gateway** — normalized inbound/outbound communication transport with capability-aware adapters.
2. **Durable Execution Runtime** — checkpoints, leases, heartbeats, reclaim, crash resume, bounded retry and durable task state.
3. **Capability Catalog + Dynamic Tool Search** — searchable lightweight manifests and progressive contract loading.
4. **Learned Automation Evaluation Pipeline** — candidate → replay/evaluate → compare → safety/permission review → promote/rollback.
5. **Artifact / Result Model** — typed durable outputs with provenance, version and verification state.

See [RUNTIME-FOUNDATIONS.md](RUNTIME-FOUNDATIONS.md).

## Epistemic integrity correction

The benchmark also exposed a behavioral requirement more fundamental than feature breadth: OSCAR must never claim that work is complete merely because it intended to do it, delegated it, or received a success response.

OSCAR must distinguish:

```text
planned
executing
reported success
observed result
verified result
partially verified
failed / blocked / unknown
```

A Worker/tool result is evidence, not automatically truth. User-facing claims cannot exceed available evidence.

See [EPISTEMIC-INTEGRITY.md](EPISTEMIC-INTEGRITY.md).

## Final architecture position

OSCAR's frozen pre-implementation architecture should therefore include:

```text
Perception Fabric
→ World Model
→ Jev + Epistemic Integrity
→ Memory / Live Context / Intelligence
→ Executive Planner
→ Durable Execution Runtime
→ Workers / Protocols / Skills
→ Capability Catalog + Dynamic Tool Search
→ Actions / Channel Gateway / Device Mesh / Specialists
→ Action Ledger + Artifact/Result Model
→ Verify
→ update World Model / Memory
→ report only what evidence supports
```

Cross-cutting layers:

- Personal Policy;
- permissions;
- canonical entity graph;
- audit/provenance;
- learning/evaluation;
- safety.

## What OSCAR deliberately does differently

OSCAR remains **device-mesh first** rather than assuming every agent owns a cloud VM.

```text
OSCAR
├── Sunday / phone
├── Windows/macOS machine nodes
├── ESP32/Pico Edge
├── APIs/plugins/channels
└── optional future cloud Worker nodes
```

If a device is offline, its capabilities disappear; OSCAR remains alive and reroutes only through equivalent authorized capabilities.

An optional cloud Worker can be added later as another capability, not as the foundation of the product.

## Architecture freeze rule

After these additions, stop expanding the architecture because another assistant product ships a feature.

The next objective is implementation quality:

> **Slice 01 remains next. Prove the fundamental loop before adding more conceptual breadth.**
