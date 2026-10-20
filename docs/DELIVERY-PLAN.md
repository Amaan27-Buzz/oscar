# OSCAR — Active Delivery Plan

**Owner decision, 2026-10-18:** Get one OSCAR operational across **Cloud, Windows Desktop and Android phone** first; add the dedicated home-server laptop when available, then ESP32/Pico. This supersedes the former "hardware Slice 18 is next" sequencing. Slices **00–20 remain canonical**; **Groups 4–8** are the new delivery batches, and D/C stage labels are *not* new numbered slices. Preserve historic PRs and evidence.

[Verified checklist](CURRENT-STATUS.md) · [Slice map](SLICE-NUMBERING.md) · [Acceptance gates](BUILD-GATES.md) · [Deployment architecture](DEPLOYMENT.md)

## Groups and order

| Group | Deliverables | Exit / boundary |
| --- | --- | --- |
| **Completed** | Gate A/B foundations, Desktop/Mobile Groups 1/2/2.5, one **Group 3 Slices 14–17**, PR #7 merged | Software integrated; Gate C/D still PARTIAL |
| **4 — Cloud and Grid** | **D1:** persistent secure hosted Core; **D2:** distributed authenticated Grid and outbound desktop Worker | Real separate hosts and restart/recovery; no unauthenticated public Core |
| **5 — Connected, capable OSCAR** | **D3:** real Windows/Android; **D4:** owner commissioning; **C1:** computer use; **C2:** plugins/MCP; **C3:** Secure/Full Access; **C4:** voice, Workers, Sentry, Chief of Staff, AIE | Owner-evidenced natural requests across real phone/desktop, providers and safe authority |
| **6 — Operational Alpha** | Sustained Cloud–Desktop–Phone daily usage, verified cross-device task flow, failures and recovery | **Scoped operational-alpha checkpoint**, *not* formal Slice 20/Gate E PASS |
| **7 — Home-server laptop** | Owner-controlled local compute/Core hosting or safe hybrid; cloud as optional escalation | Depends on available laptop; one identity, no split-brain or double writers |
| **8 — Physical Edge/full acceptance** | **Slice 18** ESP32/Pico hardware acceptance, remaining **Slice 19** hardening and **Slice 20** full integrated scenarios | Genuine hardware/owner acceptance; complete applicable Gate C/D/E evidence |

**Slice 19 hardening is continuous**, starting with Group 4 TLS, identity, secrets and revocation; do not defer network security until Group 8. Outstanding Slices 05–10 and 14–17 requirements are carried forward into Groups 4–6 rather than falsely reaccepted. Physical Slice 18 is deferred, **not removed from the original comprehensive gates**.

## Group 4: make one persistent, secure OSCAR

- [x] **D1 software engineering closure:** existing Core deployment composition, explicit production configuration, private Grid-authenticated diagnostic API, injected secrets, canonical volume identity/locking, WAL/FTS5, task/Worker/schedule recovery, backup/independent restore and nonroot Linux/TLS packaging are implemented. Independent review corrections add transactional offline credential delivery, fixed production port and authenticated admission fairness, with 44 Cloud regression tests. [Evidence and CI](development/GROUP-04-D1.md) and the existing [PR #8 closure receipt](https://github.com/Amaan27-Buzz/oscar/pull/8) distinguish software, exact-head integration/main checks and commissioning; [operations guide](CLOUD-CORE.md) includes exact commands and current Oracle constraints. This does not mark hosted D1 accepted.
- [ ] **D1 host commissioning:** authenticate actual Oracle tenancy/Always Free A1 region/capacity and eligibility; approve/provision host and persistent storage, execute candidate on that host, commission approved domain/TLS/firewall, independent network verification and off-host backup restore. **Oracle is not deployed.** Optional derived Memory services need separate capacity/runtime acceptance; no full-stack free-tier fit claim. Vercel remains complementary, never the canonical in-memory Core.
- [ ] **D2 Remote Grid candidate and acceptance:** [current connected software draft](development/GROUP-04-D2.md) extends the canonical Core with authenticated independent node enrollment, scoped outbound Worker connectivity, rotation/revocation/replay fencing, durable history and independent readback. Genuine same-host TLS/process verification is separate from independent hosted commissioning. Legacy local adapters on `127.0.0.1` remain private.
- [ ] Verify cross-host actual transport, shutdown/restart and uncertain side effects; never expose Core before security evidence. No paid charges or cloud credentials provisioned without separate permission.

The [independent D2 local closure](development/GROUP-04-D2-CLOSURE.md) records the
software candidate and exact evidence boundaries. Publication/CI resumption
requires owner authorization. The next separate run is Cloud commissioning and
connected-client operation: verify Oracle account/capacity, approve provisioning,
establish one persistent writer, TLS/DNS, encrypted off-host restore and actual
independent-network Windows operation. Physical Android stays separately gated.

## Group 5: make OSCAR capable and pleasant to use

**2026-10-20:** [C1/C2 local foundation](development/GROUP-05-CAPABILITY-IDENTITY.md)
now has executable synthetic acceptance for identity/account binding, official
MCP transports, isolated browser profiles and Windows UIA, plus emulator-tested
Android adapters. Native Desktop manages enrolled account/plugin state with
signed Ask review. Trusted enrollment remains required; Android is not yet a
remote execution Worker. This is a local branch based on unmerged D2, with no
push/CI/merge, owner credentials or physical-phone access. C3 signed standing
delegation and C4 portable voice/awareness requirements are in that ledger.

The current owner brief authorizes **D3/D4 software integration alongside D2**:
existing Tauri and Kotlin/Compose connectivity, synthetic credentials, builds,
unit tests and explicitly selected disposable emulators. It prohibits physical
phone access, real owner/provider commissioning and standing Secure/Full Access.
The [connected ledger](development/GROUP-04-D2.md) records actual evidence; these
software checks do not complete the real-device checklist below.

- [ ] **D3/D4 Real devices and commissioning:** native Desktop and Android installs, pairing to the same hosted Core, shared chronological conversation, real Memory Fabric, Presence, Activity, task inspection, approval/cancel from phone, honest offline state, actual provider/voice setup and OEM verification.
- [ ] **C1 Real computer use / full PC control:** extend tested typed PowerShell/files/Git, registered UIA, isolated browser into reliable observed natural-language computer/app/browser execution, optional authorized visual fallback and independent verification. The real PC Worker acts; cloud services do not imply a magic omnipotent host.
- [ ] **C2 Plugin/MCP ecosystem:** native Capability Catalog; official API, reviewed MCP/connector, authorized browser fallback, appropriate OAuth/scoped vault, discover/install/revoke; real GitHub/Google trials and failures recorded. Do not grant arbitrary plugin authority.
- [ ] **C3 Ask / Secure / Full Access:** Ask current; Secure needs protected-action confirmation; Full Access needs explicit owner activation and **genuine** signed standing delegation without OSCAR per-action prompts, bounded scope/expiry, immediate distributed revocation and audit. Platform permissions, externally mandated controls and deterministic physical safety still apply.
- [ ] **C4 Everyday assistant:** real portable voice, barge-in, Sentry source-specific permission/retention, notifications, Chief of Staff, native automation schedule creation/editing, Worker continuity, useful trusted AIE/widgets; maintain separately verified/unavailable states.

## Group 6: scoped alpha

- [ ] Real request from Windows or Android → same Cloud Core and canonical memory → authorized Desktop Worker/provider/plugin → readback/verification → result/Presence on both devices.
- [ ] Test node disconnect, restart, device loss, revocation, private data isolation, backup and restore, no double execution and a bounded real-day usage period.
- [ ] Accept **only** the demonstrated Cloud–Desktop–Phone scope. Gate C/D remain PARTIAL and Gate E NOT PASSED until their mandatory physical/live cases are actually accepted.

## Deliberate deferrals and quality requirements

- **Later hardware:** owner home-server laptop (Group 7), ESP32/Pico physical (Group 8), optional Galaxy Tab Home Node afterward. Neither physical Edge nor Home server is a prerequisite for the earlier scoped operational alpha.
- **Still required during normal alpha:** computer use, plugins/MCP, appropriate real voice, verified tasks, essential authoring, core security, owner/device commissioning and critical revocation; these are not cancelled or silently pushed into post-alpha.
- **After stable alpha:** deep Jarvis-like latency/power/quality campaign, telemetry-driven specialist models and learning, larger interactive AIE surface and broader integrations. Do not use premature optimization as an excuse to defer a usable product.
- **Every phase:** one OSCAR Core identity, immutable canonical history, separate capture/retention/action grants, approved Orb and native UI, source-backed truth, independent verification and fail-closed permissions.

## Execution pace — capability and acceptance driven

No estimated weeks, calendar deadlines or artificial waiting periods. Progress as quickly as possible through verified work, parallelizing independent implementation and testing where safe:

1. **Start immediately** on the highest-value unblocked stage. Keep implementation, CI, evidence and documentation in the same cohesive delivery.
2. **Parallelize independent work** (e.g., ARM64 packaging, remote transport threat-model/tests, native client compatibility) when interfaces and ownership are clear; do not fork OSCAR's authoritative Core or duplicate a planned slice.
3. **Integrate after genuine checks** of the current head and observable acceptance, not after elapsed time. Do not delay a complete stage merely to match an estimate.
4. **Expose blockers early** (Oracle quota/capacity, unavailable real phone, permissions, account commissioning, network failures); choose an evidence-backed fallback rather than assume success or spend money silently.
5. **Keep safety and correctness non-negotiable**. Fast delivery does not justify insecure public endpoints, weakening authority/CI, skipping necessary owner approvals or relabeling simulated evidence as physical PASS.

The project is tracked by **completed checklists and acceptance evidence**, not dates or predicted durations.
