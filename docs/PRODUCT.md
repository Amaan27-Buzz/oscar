# Product Vision

## North star

OSCAR is a persistent personal intelligence designed to do justice to the idea of JARVIS: one intelligence that understands natural language, perceives context, reasons, communicates, operates software, controls hardware, delegates to specialist systems, keeps working autonomously, learns successful procedures and appears through whichever trusted device is available.

It is explicitly **not** a conventional chatbot, a laptop-only agent, a wrapper around one model provider or a decorative animated orb.

A non-negotiable rule:

> **OSCAR must prefer uncertainty, incompleteness, disagreement or failure over presenting an unverified statement as fact.**

Where verification is technically possible, OSCAR verifies before making an unqualified completion claim.

## What OSCAR should feel like

- **Immediate** — reflexes and simple interactions happen locally and quickly.
- **Present** — OSCAR exists continuously rather than only while a chat window is open.
- **Continuous** — one relationship and interaction point; the user does not manage memory by finding old chats.
- **Contextual** — it understands active work, devices, communications, schedule and environment.
- **Capable** — it acts through tools, apps, cloud services, Workers and physical devices.
- **Selective** — it uses the strongest suitable capability rather than invoking a frontier model for everything.
- **Personal** — voice, Persona, Personal Policy, permissions, memory and interaction style belong to the user.
- **Recognizably itself** — one voice/visual/character identity persists across surfaces.
- **Learning** — verified procedures can become evaluated reusable Skills/routines/Protocols.
- **Delegating** — Workers can own temporary or persistent responsibilities underneath OSCAR.
- **Quietly proactive** — important events surface; routine noise stays quiet.
- **Truthful about state** — reported/verifying/partial/blocked/failed/unknown remain real outcomes.
- **Hard to kill** — ordinary loss of a phone, desktop, cloud node or Edge node degrades capability instead of erasing the system.

## One continuous relationship

The product-facing primitive is:

```text
You ↔ OSCAR
```

There is no requirement for the user to create a new chat to gain a new context window or find an old thread to recover history. Internal segmentation into turns, episodes, projects, objectives, entities and memories is an implementation detail.

Active context is reconstructed from recent conversation, current objectives/projects/entities/commitments, relevant retrieved history and current World Model state.

See `docs/MEMORY.md`.

## OSCAR-owned Memory Fabric

OSCAR owns its history rather than outsourcing identity/continuity to a managed memory vendor.

Canonical architecture:

```text
OSCAR Event Archive
SQLite + WAL + FTS5
      │
      ├─ Qdrant OSS semantic/hybrid index
      └─ Graphiti OSS + Neo4j Community temporal/entity index
                │
        Retrieval Fusion + reranker
                │
        Jev Memory Preflight
                │
          Context Assembly
```

Qdrant and Graphiti/Neo4j are derived/rebuildable indexes. The Event Archive remains canonical source history and provenance.

Product memory guarantees we design toward:

- OSCAR does not say `I remember X` unless X was actually retrieved or remains in active context with provenance;
- personal/historical claims bind to source events/memories;
- an empty first retrieval is not treated as proof of absent memory;
- Jev broadens retrieval before returning UNKNOWN when memory is expected;
- live authoritative state beats stale recall for current-state questions;
- corrections supersede old current facts without destroying history;
- model-derived inference never silently becomes fact;
- memory never grants permission or silently creates Personal Policy.

The previous planned Supermemory dependency is retired.

## Ambient Chief of Staff

OSCAR should behave like a continuously available personal Chief of Staff, not an app the user repeatedly opens to coordinate each part of life manually.

Authorized current context may include time/date/timezone, weather, calendar, tasks/deadlines, location/mobility, notifications, calls/messages/email, current media/activity state, device/Connection Grid state, Workers/Protocols and Sentry/Edge observations.

OSCAR should combine these into one freshness-qualified picture of the user's day and, within Personal Policy and real capability, help with:

- schedule conflict detection and replanning;
- task/deadline prioritization;
- focus/study/build blocks;
- preparation/travel/weather buffers;
- commitments extracted from communication;
- morning/day briefs and `what did I miss?` summaries;
- proactive warnings when plans become unrealistic;
- bounded automatic calendar/task changes when explicitly authorized;
- communication follow-up and schedule updates after verified changes.

Proactivity is graduated:

```text
observe silently
→ inform
→ suggest
→ act within policy
→ interrupt only when justified
```

A core permission rule is:

```text
CAN PERCEIVE ≠ CAN RETAIN ≠ CAN ACT
```

See `docs/CHIEF-OF-STAFF.md`.

## One intelligence, many embodiments

### Sunday

Sunday is OSCAR on the phone. It is the preferred everyday owner-control surface because the phone usually remains with the user while laptops/desktops come and go.

Subject to platform support and permissions, Sunday provides voice/text, notifications, communication context/actions, camera/sensors, biometric approval, remote task supervision, Connection Grid controls and everyday Chief-of-Staff presence.

On Android, use legitimate platform capabilities where supported: assistant/voice-interaction role, optional application overlay for the OSCAR Orb, home-screen widgets, notification-listener context and legitimate notification replies when a real reply action exists.

The Orb is persistent presence, not permanent obstruction. It may retreat during video, reading, presentations or focus and reappear when invoked.

### Desktop

Native/lightweight Windows/macOS surfaces provide interaction, dictation, approvals, context and presence. Desktop machines are optional high-capability nodes exposing coding agents, terminal, filesystem, browser/computer use, installed apps, GPU/local models and other capabilities.

A desktop is never the permanent OSCAR host.

### Edge

ESP32/Pico-class hardware provides persistent local presence, sensors, wake/VAD, GPIO/actuators and deterministic safety/reflex behavior. Edge does not run OSCAR's primary language intelligence.

### Cloud

A replaceable cloud coordinator may provide rendezvous, durable coordination, remote command routing and notification fan-out. OSCAR should support free-tier, paid and BYOC paths rather than one required vendor.

## Connection Grid

Sunday, cloud coordination, Desktop nodes and Edge form the OSCAR Connection Grid. Nodes advertise capabilities dynamically and communicate through OSCAR-owned transport.

The user should be able to start useful work on one machine, leave, inspect/approve/cancel remotely, receive a verified result and optionally permit power actions when a real capability exists.

Remote wake/power exists only where a real mechanism exists.

## Native infrastructure

OSCAR does not depend on separate Latch/SwitchRoute runtimes.

- Latch-derived ideas → OSCAR Transport + Capability Fabric.
- SwitchRoute-derived ideas → OSCAR Model Router.

Jev decides action/evidence class; capability selection chooses executor; Model Router chooses a model/provider only after reasoning is required.

## Persona

OSCAR may be dry, witty, solemn, warm, formal, playful, blunt or custom. Persona changes expression, not truth or authority.

Epistemic Integrity, hard safety, permissions and Personal Policy outrank Persona.

## Voice identity

Voice has four distinct layers:

- Voice Input — wake/VAD/STT/barge-in/dictation.
- OSCAR Voice Identity — stable provider-independent voice/prosody contract.
- Voice Match — authorization-oriented owner/authorized-speaker evidence.
- Voice Map — perception-oriented confidence-qualified speaker recognition.

Recognizing someone never grants authority by itself.

## Sentry and continuity capture

Sentry means persistent local awareness when enabled, not permanent cloud transcription.

Possible low-cost signals include wake/reflex commands, VAD/speech presence, Voice Map events, configured sound classes, device/environment events and barge-in.

Optional Context Capture / Daily Journal may retain selected communication or in-person context only where technically, legally and policy permitted.

Raw audio, transcripts, summaries and derived memory are separate retention decisions.

## Core product principles

1. **Delegate objectives, not button presses.** OSCAR chooses the strongest legitimate execution path and verifies results where practical.
2. **Language is a control surface.** Short contextual phrases resolve against active state, memory and policy.
3. **Memory is not authority.** Historical continuity never silently replaces current live truth.
4. **Personal Policy is first-class.** Explicit desired behavior is distinct from memory, Persona and permissions.
5. **Communication belongs to OSCAR.** Calls/messages/email/meetings/dictation/follow-up share one identity/context architecture.
6. **Reflexes bypass intelligence.** Emergency stop/mute/cancel and deterministic controls do not wait on cloud reasoning.
7. **Use models only where useful.** Jev decides whether reasoning is needed.
8. **Know when context is missing.** Jev retrieves/expands/asks rather than guessing personal/current facts.
9. **Never claim more than evidence supports.** External success testimony is not objective verification.
10. **Get faster with experience.** Verified procedures may become evaluated reusable automation.
11. **Workers recover before escalating.** Repair/reroute is bounded and never expands authority.
12. **Capabilities are discovered progressively.** The core searches manifests rather than loading every tool into every prompt.
13. **Artifacts/results are first-class.** Finished outputs carry provenance and verification state.
14. **Proactivity requires restraint.** OSCAR distinguishes silent update, inform, suggest, act and interrupt.
15. **Hardware safety is local.** Cloud intelligence never replaces deterministic interlocks/emergency behavior.
16. **Perception, retention and action are separate.** Observing context does not imply storing or mutating it.
17. **Availability is distributed.** Losing one ordinary node degrades capability instead of erasing OSCAR.
18. **Finish gates end-to-end.** Planned mandatory work is completed and verified before moving to the next Club unless scope is explicitly changed.

## Current build direction

Gate A is accepted. Gate B is the current work and must be completed before Club C.

Gate B completion includes real machine/browser/computer-use/installed-app/remote-control paths plus the full OSCAR Memory Fabric, open-ended Personal Policy, real private OAuth/connector acceptance, secure credential storage and live-authority-vs-memory federation.

See `docs/ROADMAP.md` and `docs/BUILD-GATES.md`.

## Non-goals

- conventional chat-thread management as the memory model;
- mandatory managed memory vendor;
- decorative AI-orb software;
- laptop-only availability;
- reimplementing specialist software OSCAR can invoke;
- required external Latch/SwitchRoute runtimes;
- unsupported phone/app/control claims;
- treating notification visibility as unrestricted app access;
- conflating perception permission with retention/action authority;
- treating external success reports as verified facts;
- yes-man behavior;
- covert/silently enabled recording;
- letting Persona reduce truthfulness/safety;
- putting an LLM in a hardware emergency-control loop.
