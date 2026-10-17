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

## Group 4 (next): make one persistent, secure OSCAR

- [ ] **D1 Cloud Core:** check actual Oracle tenancy/Always Free A1 region/capacity, Linux ARM64 Python/native/Qdrant/Neo4j feasibility and costs; package existing Core (not a parallel backend); durable Event Archive and task leases, least-privileged OS service, secret storage, TLS ingress, health, independent backup/restore and restart. **Oracle is a candidate, not deployed.** Vercel may serve bounded UI/OAuth/webhooks/relay, not an in-memory canonical Core.
- [ ] **D2 Remote Grid:** authenticated independent node enrollment, scoped capability routing, persistent *outbound* Worker connectivity, rotation/revocation/replay fencing, offline/resume and independent result readback. Current local HTTP adapters on `127.0.0.1` are **not** Internet-ready.
- [ ] Verify cross-host actual transport, shutdown/restart and uncertain side effects; never expose Core before security evidence. No paid charges or cloud credentials provisioned without separate permission.

## Group 5: make OSCAR capable and pleasant to use

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
