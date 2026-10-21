# OSCAR — Deployment Architecture and Hosting Decision

**2026-10-21 software candidate:** writable account credentials use an encrypted
vault under a separately protected service key; optional public OAuth client
registration configuration is described in [Cloud operations](CLOUD-CORE.md).
The [completion ledger](development/OSCAR-FULL-SOFTWARE-COMPLETION.md) tracks
local acceptance. This is not hosted deployment or real provider commissioning.

**Owner priority (2026-10-18):** bring up one OSCAR on a persistent cloud host, then make Windows Desktop and the owner's Android phone connect to that same Core. When the owner returns home, add the dedicated home-server laptop; integrate ESP32/Pico physical hardware later. **No Oracle/Vercel/Internet deployment is currently accepted.** [Live checklist](CURRENT-STATUS.md) · [New delivery groups](DELIVERY-PLAN.md).

**Persistent Core and connected candidate:** `python -m oscar.cloud --config /etc/oscar/cloud.json` composes the existing Harness, Controller, Grid, Router, Event Archive/Memory and Executive. Production configuration and explicit initialization are mandatory. One local volume holds both canonical databases, identity and artifacts under an exclusive lifecycle lock. D1 bounded diagnostics and D2's two versioned Grid POST interfaces use explicit authentication and durable replay fences. Legacy privileged reference APIs remain private. [Operations and commissioning](CLOUD-CORE.md) · [D1 evidence](development/GROUP-04-D1.md) · [Connected software evidence](development/GROUP-04-D2.md).

## Target topology

```text
              Persistent OSCAR Core (cloud host)
    Controller / Policy / Event Archive / Memory / Executive
                           |
              authenticated Connection Grid
                /                       \
       Windows Desktop Worker       OSCAR Android
         tools / apps / GPU        owner control / voice
                \                       /
                 one identity / one task truth

    Later: dedicated home-server laptop (local/hybrid Core)
    Later: ESP32 and Pico (deterministic Edge safety/reflexes)
    Optional later: Galaxy Tab home-presence node
```

The current Python reference HTTP adapter `oscar/transport.py` and `oscar/mobile.py` bind `127.0.0.1`, not a production public endpoint. **Do not forward these reference ports to the Internet.** Remote operation requires a designed TLS ingress, per-node authentication/enrollment, a safe server-side credentials store, replay-resistant authorization, revocation and actual remote readback/recovery tests.

## Hosts (replaceable; free-first where actually available)

| Host | Intended role | Selection / limit |
| --- | --- | --- |
| **Oracle Cloud Always Free VM** | First candidate for long-running stateful Core: tasks, Event Archive, coordination and Grid | **Preferred but not deployed.** Verify own tenancy/region, A1 ARM64 instance capacity, monthly compute/storage allowances, reclamation and Python/native/index compatibility. |
| **Vercel Hobby** | Optional bounded API/web/frontend/OAuth callback/webhook/relay surface | Not the persistent Core; functions cannot assume long-running Coordinator, filesystem persistence or always-on Worker scheduling. Check personal/non-commercial eligibility, current quotas and terms. |
| Alternative Linux VM / approved BYOC | Fallback persistent Core if Oracle unavailable or unsuitable | Explicit cost, storage, transport, ARM/x86 and backup compatibility review first. |
| Dedicated owner home-server laptop | Later hosting and local inference/voice/model Worker pool | **Group 7**, physically available only when owner returns home; migration/hybrid must preserve one authority/identity. |
| ESP32/Pico | Deterministic hardware reflexes/sensors and safety interlocks | **Group 8**; never full Core, no physical test yet. |

The prior free-tier research was collected **2026-10-04**. Provider capacity and quota are not constants: check current official data and real account state, not old plan numbers. [Oracle Always Free resources](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm), [Vercel Hobby](https://vercel.com/docs/plans/hobby), [Vercel Python functions](https://vercel.com/docs/functions/runtimes/python), [Vercel function limitations](https://vercel.com/docs/functions/limitations).

**Oracle ARM64 risk:** verify all actual OSCAR dependencies (Python runtime, OS wheels, SQLite FTS5, embeddings/ONNX, Qdrant, Graphiti/Neo4j, memory/resource footprint) and any container images on the selected VM before suggesting "the full stack fits." Prefer canonical durable SQLite/archive plus rebuildable derived indexes over moving identity/history into ephemeral Functions. Oracle Always Free can reclaim underutilized capacity; backups and recoverability matter. Never manufacture artificial load to defeat provider rules.

## Group 4 — deploy safely (D1/D2)

**D1: secure persistent Core.** Implemented candidate provides a digest-pinned multiarchitecture Linux package, nonroot constrained service, canonical durable volume, read-only injected secrets, opt-in TLS ingress, authenticated diagnostics, health/degraded readback, bounded logs and independent backup/restore with crash/restart tests. This authorizes software verification only. Actual Oracle account capacity, host storage, public domain/certificate/firewall, off-host backups and owner commissioning require separate acceptance. See the evidence ledger for native ARM64 CI results; image manifests and dependency metadata alone are not runtime acceptance.

**D2: authenticated Connection Grid software candidate.** Bounded outbound HTTPS
polling works through standard TLS on Linux, Windows and Android without inbound
device ports or another broker. Stable device keys prove possession independently
of expiring bearer sessions; trusted offline invitations bind role, installation,
workspace and scopes. Worker acceptance and pre-effect checks revalidate authority.
Separate readback verifies scoped file results; uncertain mutations remain blocked
after process loss. [Protocol 2](development/GROUP-04-D2-PROTOCOL.md) defines exact
messages and recovery. Local process/container TLS evidence is not independent
Internet-host acceptance.

**D3/D4 software is integrated in the current candidate.** Real owner installation,
host pairing and OEM/background commissioning still require separate acceptance.
Only disposable Android emulators may be tested in this run; the owner phone is
explicitly prohibited. Native/physical evidence stays separate in the ledger.

## Later owner home server and physical Edge

The intended mature target is an **owner-controlled dedicated home-server laptop**, not permanent dependence on today's development laptop. When hardware permits, it can host the Core, memory derived services, a local Model Router/model pool, voice services, durable Workers and local device coordination. Cloud models stay available as explicit optional escalation for major work. Design an observable, reversible migration with **one canonical Core writer**; never run two independent OSCAR archives or conflicting executives as equals. See [post-alpha evolution](POST-ALPHA-EVOLUTION.md).

The previously discussed **Samsung Galaxy Tab S6 Lite (2021)** is an *optional distinct future Home Node*, not a substitute for the dedicated home-server laptop and not a Group 4–6 dependency. ESP32/Pico physical onboarding, serial GPIO/Watchdog/E-stop/sensor checks and smart-home actuators stay in **Group 8**. Physical safety must work locally during cloud/Grid loss.

## Acceptance boundary

- Gate A/B existing software PASS is not hosted acceptance.
- Gate C/D remain PARTIAL, irrespective of successful GitHub Actions.
- Group 6 may earn **only** a clearly scoped Cloud–Desktop–Phone operational-alpha milestone.
- Original full Slice 20/Gate E requires the separately deferred physical and live acceptance unless the owner explicitly revises that gate.

See [security](SECURITY.md), [Grid](CONNECTION-GRID.md), [onboarding](ONBOARDING.md), [gates](BUILD-GATES.md) and the [active delivery plan](DELIVERY-PLAN.md).
