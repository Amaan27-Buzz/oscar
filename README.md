# OSCAR

The local [Group 5 C1/C2 foundation](docs/development/GROUP-05-CAPABILITY-IDENTITY.md)
adds operational identity, account-bound authentication, real MCP sessions,
isolated persistent browser profiles and native connection management to the
same Core. It depends on the unmerged D2 candidate and is not published or
owner/provider commissioned. Ask remains active; Secure/Full Access is unavailable.

Group 4/D1 provides the persistent Linux Cloud Core. The D2/D3–D4 integration
candidate adds authenticated outbound Grid transport, scoped file execution and
native connection support using that same Core. [Connected integration evidence](docs/development/GROUP-04-D2.md)
separates actual local TLS/process tests, native/emulator checks and remaining
hosted/owner acceptance. [Deployment and commissioning](docs/CLOUD-CORE.md).

**One intelligence. One continuing relationship. Many devices.**

OSCAR is Dawnlight Labs' persistent multimodal personal assistant: one authoritative Core, durable memory, a Controller and verified execution runtime, with native Windows and Android embodiments. Its intended capabilities include natural conversation, full authorized computer use, plugins/MCP, owner-controlled delegation, durable Workers, voice, awareness and eventually physical Edge.

**Project status — 2026-10-18:** Slices 00–17 have **integrated software foundations**, including [Group 3 PR #7](https://github.com/Amaan27-Buzz/oscar/pull/7). GitHub Actions is enabled and ran successfully. **Gate A and Gate B PASS for documented scopes. Gate C and Gate D PARTIAL. Gate E NOT PASSED.** The Cloud–Desktop–Phone product is **not yet deployed or owner-accepted**.

**Start here:** [Current checked status](docs/CURRENT-STATUS.md) · [New groups and indicative timeline](docs/DELIVERY-PLAN.md) · [Canonical slice numbering](docs/SLICE-NUMBERING.md) · [Build gates](docs/BUILD-GATES.md) · [Deployment](docs/DEPLOYMENT.md)

## One OSCAR, many embodiments

```text
         OSCAR Core: identity / Controller / Policy
       Event Archive + Memory Fabric + Executive
                         |
            authenticated Connection Grid
                 /                \
        Windows Desktop      Android Mobile
         apps + Workers       owner controls
                \               /
           one relationship / one task truth

      Later: dedicated owner home-server laptop
      Later: ESP32 + Pico / optional home devices
```

**Hosted/owner acceptance remains outstanding.** The connected candidate uses
versioned HTTPS, device proof of possession, explicit trusted enrollment and
outbound Worker polling. Legacy reference servers remain private loopback APIs.
Oracle Always Free is the preferred replaceable **candidate**, not deployed;
Vercel can complement it with bounded web/API/callback functions.

## What's implemented versus still missing

| Subsystem | Integrated reference/software | Outstanding |
| --- | --- | --- |
| Core / model routing / Grid | Evidence-backed decision loop, model routing, persistent Core and authenticated outbound Grid candidate | Hosted Internet and owner-device commissioning |
| Memory / Personal Policy | Canonical SQLite WAL/FTS5 archive and derived retrieval, policy | Hosted restore and real multi-device memory |
| Windows | Tauri Companion + Workspace; existing machine tools plus bounded outbound file Worker candidate | Broad real computer use and owner deployment |
| Android | Owner-approved native Compose UI, scoped sessions, shared Presence | Actual phone pairing, OEM/audio/notification acceptance |
| Voice | Portable core/identity reference | Real microphone, wake/barge-in, Match/Map and owner testing |
| World/Executive | Local Sentry lifecycle, durable bounded Workers and schedules | Real source delivery, distributed execution, native authoring |
| Plugins/MCP | Connector Fabric, manifest/auth and MCP boundaries, accepted GitHub OAuth path | Live general MCP sessions, provider enrollment and verified workflows |
| Access | Ask-style policy and scoped action confirmations | Secure and genuine Full Access signed standing delegation/revocation |
| Edge | Firmware/protocol software and simulation | Physical ESP32/Pico safety tests later |

## Active delivery sequence

1. **Group 4 — Cloud and remote Grid (D1–D2):** deploy persistent secure Core, then real authenticated cross-host connections.
2. **Group 5 — Connected and capable (D3–D4, C1–C4):** Windows/Android, computer use, plugins/MCP, Ask/Secure/Full Access, voice, automation and Chief of Staff.
3. **Group 6 — Operational Alpha:** real daily Cloud–Desktop–Phone experience, verified results, recovery and scope-specific owner acceptance.
4. **Group 7 — Home-server laptop:** add when available; move progressively toward local independence.
5. **Group 8 — Physical Edge and formal gates:** physical Slice 18, residual Slice 19 hardening and formal Slice 20 acceptance.

Preserve Slices 00–20 and historical evidence. A **scoped** Group 6 alpha does not imply physical Gate C/E PASS. Prioritize critical remote security during Group 4, not at the end.

## Engineering and provenance

Follow [AGENTS.md](AGENTS.md), [ENGINEERING.md](ENGINEERING.md), [DEVELOPMENT.md](DEVELOPMENT.md), [product direction](docs/PRODUCT-DIRECTION.md), [architecture](docs/ARCHITECTURE.md) and [active roadmap](docs/ROADMAP.md). Preserve approved [OSCAR Orb](assets/brand/oscar-orb.svg), Desktop and Mobile designs, epistemic truth, separate capture/retention/action grants and the OSCAR-owned Core. Latch/SwitchRoute are **not required external runtimes**.

Evidence: [Group 3 CI/integration](docs/evidence/group03/ACTIONS-INTEGRATION.md) · [Group 3 Gate D](docs/evidence/group03/GATE-D-REPORT.md) · [Gate B](docs/GATE-B-COMPLETION.md) · [Mobile approved UI/UX](docs/ui/mobile/group25b/README.md). Older PR-specific instructions survive in Git history as provenance, not as the active work order.
