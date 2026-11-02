# OSCAR — Cinematic First Run and Progressive Setup

**Status:** Owner-directed product/design mandate, 2026-11-02. This document describes the required software experience; it is **not** an implementation or acceptance receipt.

Read with [First-Time Setup / Commissioning](ONBOARDING.md), [Product Direction](PRODUCT-DIRECTION.md), [Connection Grid](CONNECTION-GRID.md) and [Cloud Core](CLOUD-CORE.md). Their existing authority, privacy, enrollment, persistence and provider constraints continue to apply.

## Intent

OSCAR is an approachable, capable personal intelligence that helps people rather than replaces them. Its first minutes should feel like **meeting a playful, helpful companion**, not installing an agent framework. The owner cites HeyClicky's public cinematic first-run as a reference for pacing, discovery and hands-on demonstration, **not** as authorization to reproduce its character, art, animation, copy or exact sequence.

Preserve the original OSCAR mascot and canonical Orb, the approved Desktop Workspace/Companion and the approved native Android visual language. Favor the established **Quietly Alive + Playful Precision** direction, expressive movement, warm paper/graphite and purposeful blue/yellow accents. Cinematic presentation must lead to real utility.

**Two layers, not a 26-page blocking wizard:**
1. **First encounter:** approximately 1–3 minutes as a design target (skippable), ending in a live conversation and one meaningful real capability.
2. **OSCAR Setup Studio:** reopenable progressive guided setup for identity, integrations, permissions, devices, hosting, automation and advanced configuration. Everything not required for the first useful conversation may be postponed.

A user with one available local or configured model should be able to start using OSCAR without cloud hosting, a phone, an OSCAR-dedicated provider account or all integrations. If no model is available, show a truthful, lightweight model-connection step rather than a fake chat.

## Cinematic narrative — design beats, not rigid screens

| Beat | Experience | Real underlying effect |
| --- | --- | --- |
| **01 · Awakening** | Quiet opening; canonical Orb/mascot comes alive, subtle audio/motion, succinct introduction and an obvious Skip option | Start actual Core or report its readiness. Never animate a false "online" state |
| **02 · Getting acquainted** | Brief conversational choices for how OSCAR should address and assist the user, humor, voice/persona and initiative; allow typing instead of speaking | Persist verified preferences and Persona without changing authorization/safety boundaries |
| **03 · Give OSCAR a mind** | Detect available local models, show optional cloud providers, user keys, automatic/manual routing and free-first/local preferences | Store secrets only through the existing secure Vault/OS path, perform genuine inference preflight and expose real availability, costs/quotas and fallback constraints |
| **04 · First magic** | Invite one small safe real-world request; guide the user in the actual Workspace or phone UI, with playful contextual expression | Perform an actual model reply or permitted capability operation, then verify its result; no hardcoded success or faux computer control |
| **05 · Connect your world** | Offer attractive, optional integration choices with clear benefits instead of a provider configuration wall | Real OAuth/account selection, capabilities and scoped grants, with connected/configured/available distinctions |
| **06 · Everywhere you are** | Introduce the same OSCAR moving between phone, desktop, a spare-laptop server and optional cloud coordination; show the Grid simply | Real device invitations/pairing/health checks, one Core identity and safe ownership of canonical state; unavailable environments remain setup options, not connected devices |
| **07 · Your OSCAR** | Orb settles into its normal companion position; setup visually transitions into the *actual* Conversation/Workspace/Android UI | Live state, persistent conversation, accurate readiness and suggested first actions |

The first encounter should normally stop after beat 04 and offer beats 05–06 as optional Setup Studio journeys, not demand completion before use. On repeat launch, resume normal OSCAR immediately. The intro can be replayed from Preferences without recreating an identity, overwriting settings or re-enrolling credentials.

## Setup Studio — progressive commissioning journeys

Provide small understandable cards or conversational flows, grouped by what the owner wants to accomplish, not by the internal module names.

### Intelligence and providers

- Detect current Ollama/local runtimes and registered models. Do not download enormous models automatically.
- Support user-selected local, manual, auto, privacy-first and **free-first when genuinely available** routing. Free availability, quotas, provider limits and prices must be discovered/clearly described, not invented.
- Securely add/revoke API keys or authorize accounts through existing credential/Vault support. Never display or persist raw credentials in screenshots, logs, chat history, URLs or the repository.
- Verify each provider/model with a real request, allow switching later and show reasoned unavailable/degraded states.

### Accounts, integrations and OSCAR's own identity

- Offer scoped connections to Google, Microsoft, GitHub, communications, productivity, MCP and other actually supported connectors. Allow multiple distinct owner accounts and explicitly label source/destination role.
- Explain **"give OSCAR its own account"** as an optional user-managed dedicated service identity where each provider permits it, with separate credentials/roles, least privilege, revocation and safe delegation. Do **not** silently create provider identities, claim that third-party sign-up can be automated, or conflate it with the canonical OSCAR Core identity.
- Present what OSCAR can read, retain and change; verify an actual harmless capability and honor disconnect/revocation.

### Devices and surfaces

- **Desktop:** connect the approved Workspace/Companion to the genuine Core; advertise actual native capabilities.
- **Phone:** guided Android installation, short-lived QR/deep-link or code-based trusted pairing, review exact Core/device identity and permissions. Support approvals, shared conversation, tasks and Workers; comply with Android/OEM restrictions.
- **Spare laptop as server:** optional guided compatible-host preparation/deployment and later owner commissioning. Provide detected prerequisites and precise commands when OS-level or network changes require user intervention.
- **Oracle Cloud / bring-your-own cloud:** guided, replaceable Core coordinator setup; disclose account, quotas, capacity, networking, billing and public exposure implications. **Never promise guaranteed Always Free capacity**, provision or spend silently. Provide local-only or another supported route if unavailable.
- Preserve **one authoritative Core identity, Memory Event Archive and ongoing Workers**. State migration/hosting changes must be explicit, backed up, verified and single-writer; never accidentally create parallel OSCAR identities or split-brain memories.
- The server provisioning software, setup journeys and protocols are **non-deferred software scope**; procurement and physical commissioning of dedicated home-server and ESP32/Pico hardware remain separately deferred.

### Trust, voice, Persona and autonomy

- Reveal basic permission choices contextually and keep **perceive / retain / act** independent.
- Offer voice, wake and Sentry only when the OS/source supports them and permissions are granted; provide clear mic/capture indications and reduced-privilege defaults.
- Introduce temporary/persistent Workers, Ask/Secure/Full, schedules and proactivity progressively, with scope, transparency and a straightforward stop/revoke path.
- Persona, cinematic sound/motion and Voice Match must never imply stronger authorization than exists.

## Experience and implementation constraints

- Use the existing native apps, Core, Model Router, Vault, commissioning and Grid protocols; no second wizard database, second Core, parallel identity system or stand-alone deceptive web demo.
- Cinematic transitions can be original 2D/3D/native motion as appropriate. Make them lightweight, responsive, interruptible and optional: Skip, Back, Retry, Resume, keyboard/screen-reader access, reduced motion and muted audio.
- Handle offline setup, provider refusal, failed pairing, stalled host provisioning and partial completion without losing choices or pretending success.
- Completion/readiness is **evidence-backed**: configured ≠ connected ≠ recently verified ≠ currently operational. Clearly mark optional unfinished setup.
- Do not require entering real provider secrets, spending, physical phone/mic/camera use or privileged owner activation in automated acceptance.

## Alpha acceptance / manual user testing

Test the **packaged real application**, not only a fixture or reference UI:

1. Clean first launch: original cinematic interaction displays correctly; Skip and reduced-motion both work.
2. Local model detection or secure provider configuration leads to a **genuine** conversation in the approved Workspace.
3. First safe guided task performs a real effect where authorized and reports verification.
4. Restart preserves identity, Persona, memory and onboarding progress; replay is optional and harmless.
5. Setup Studio opens from Preferences and can later connect/revoke a synthetic integration and pair a disposable Android emulator via the real Core.
6. Cloud/spare-laptop paths show honest requirements and safe resumable steps; no automatic spending or new canonical identity.
7. Owner reviews the packaged Windows build and Android build before declaring a functional alpha ready.

See [Alpha Packaging, Manual Acceptance and Final Branch Consolidation](development/ALPHA-RELEASE-CONSOLIDATION.md) for the later clean-main handoff. This design is an explicit requirement for the non-deferred functional-alpha effort, but **not proof it has already shipped**.
