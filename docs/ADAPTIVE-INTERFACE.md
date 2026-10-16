# OSCAR Adaptive Interface Engine (AIE)

**Status: bounded software contract implemented in Group 3 (2026-10-16).**
`oscar/adaptive.py` validates versioned, expiring task views and negotiates three
trusted primitives: `prose`, `task_progress`, `result_evidence`. Core derives state
and evidence references from authorized canonical tasks. React and Compose render
these as accessible text with typed task inspection, freshness fallback and no
arbitrary code, WebView, signing or execution authority. The richer examples below
remain future expansion. No Group 2.5 visual redesign. Related: [surfaces](SURFACES.md),
[Core architecture](ARCHITECTURE.md), [permissions](SECURITY.md),
[canonical roadmap](SLICE-NUMBERING.md).

## User outcome

In the same continuing OSCAR conversation, a request can yield a **contextual interactive interface**, not only prose. OSCAR may compose or update a comparison table, draggable planning calendar, circuit diagram, financial visualization, live Worker view, contextual device controls, structured decision review or guided simulation when such a view improves understanding or control. The user should not need to open a standalone utility app or switch assistant personas.

Examples are illustrative, not implemented capabilities. Real execution remains subject to the actual connected tool/device and authorization model.

## Authority and ownership

```text
User request + fresh context + authorized memory
  → OSCAR Controller / Executive decides whether an interactive view helps
  → Presentation planner chooses approved component types and binds data/actions
  → Core validates data provenance, authority, privacy and task/source identity
  → typed, versioned UI descriptor with capability and freshness metadata
  → Desktop React/Tauri renderer | Android Compose renderer | accessible text fallback
  → user interaction emits typed intention
  → Core authorization → target capability → verified result
  → authoritative state updates the rendered view and conversation
```

The AIE is a **presentation layer**, not a second agent, new source of memory, sandbox-escape mechanism or executor. A generated view cannot grant access, sign approvals, call arbitrary privileged APIs, own durable facts or unilaterally mutate state. Existing Controller, Personal Policy, scoped Grid, Worker, Action Ledger and verification gates remain authoritative.

## Proposed typed descriptor (contract concept only)

A versioned envelope should carry:
- `schema_version`, unique `view_id`, `relationship_id`, `origin_task_id`/source references where present;
- `purpose` and negotiated supported component/interaction versions;
- a bounded `layout`/component tree chosen from trusted registered primitives;
- source-backed data bindings with freshness, provenance, truncation and visibility flags;
- typed, explicit user-action references (such as `inspect_task`, `propose_schedule_change`, `filter_table`), never script fragments or signed execution claims;
- accessibility semantics, presentation fallbacks, display limits, lifecycle/revision/expiry and appropriate privacy classification.

Examples of approved primitives to investigate: `prose`, `comparison_table`, `chart`, `timeline`, `calendar`, `diagram`, `stepper`, `form`, `task_progress`, `device_controls`, `result_evidence`, `approval_summary`. These names are **not** committed wire-format identifiers.

Use a validated bounded schema, reasonable depth/size/update-frequency limits, explicit version negotiation and semantic/readable fallback. Long-lived views must reacquire current state rather than pretending stale UI is live. Actions go through typed Core intents and authoritative readback.

## Rendering principles

- **Desktop:** Tauri/React workspace hosts richer interaction and wide layouts, with its native confirmation/security boundary. The tiny Companion stays a glanceable Orb, **not** an arbitrary AIE host.
- **Android:** Jetpack Compose native components, sheets and adaptive dimensions. Phone-specific input/inset/accessibility behavior; no arbitrary WebView execution under AIE's authority.
- **Same source, native embodiment:** shared intent/data/component semantics, not shared HTML pixels or identical navigation.
- **Continuity:** AIE views are embedded within the chronological Conversation and can evolve as work progresses. Preserve original text/source/interaction evidence for recall and explanation. Rendering/compaction should not erase conversation history.
- **Preference for crafted components:** reusable curated primitives first, newly generated compositions only inside approved boundaries. Attractive or reactive UI does not equal reliable data.
- **Fallback:** unsupported schema/version, missing permission, unavailable device, slow renderer, reduced motion or stale data should degrade to accessible prose/read-only representation, with truthful capability feedback.

## Safety and testing

No arbitrary LLM-authored frontend code, `eval`, unrestricted remote scripts, untrusted clickable command payloads or direct signing/credential access by components. Treat generated layouts, labels, content, images and bindings as untrusted. Validate and escape output, separate data from authority, bound resource usage and prevent prompt-injection in retrieved artifacts from becoming actions. Require an explicit authorized typed action with expected-value/epoch/revocation checks, and a clear native review only where the active access policy requires one.

Test component-schema rejection, cross-device version mismatch, privacy isolation, stale readings, long data, offline fallbacks, accessibility/TalkBack/keyboard/reduced motion, source provenance and high-frequency updates. Validate all policy modes, including eventual owner-authorized Full Access **without allowing UI rendering to be its authorizer**.

## Planned rollout (no new numbered slices)

| Slice | Contribution | Acceptance |
|---|---|---|
| **16 — Full Presence** | Define typed shared interactive presentation envelope, component capability negotiation and initial trusted Desktop/Android renderers | Cross-platform bounded render and readable fallback with authoritative state; no autonomy implied |
| **17 — Executive** | Intent-driven selection/composition, Worker/task-bound live views, model-assisted structured proposal generation and safe interaction loop | Real typed action round trips with provenance, verified outcomes and applicable consent |
| **19 — Hardening** | Security, privacy, isolation, performance, accessibility, failure, versioning and abuse-resistance validation | No generated view bypasses policy or native security |
| **20 — Unified Alpha** | End-to-end adaptive conversation on actual supported Desktop/Mobile scenarios | Demonstrated and owner-reviewed within genuine capability scope |

Do not alter Slice 14 Sentry/World Model commitments or rush AIE into Group 2.5B. The selected ImageGen/Figma baseline and OSCAR-owned production Compose primitives may inform later trusted component design; they do not implement AIE. The separate Gemini Argon prototype is rejected and must not supply code, layouts, tokens or reusable component references.
