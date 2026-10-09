# Deployment architecture

OSCAR is one intelligence across replaceable hosts and nodes. OSCAR Core owns
identity/state/memory/task coordination; no particular cloud account or ordinary
desktop defines its identity. This is target architecture, not deployed acceptance.

```text
                  OSCAR Core
            persistent coordination
                      |
               Connection Grid
          +-----------+-----------+
          |           |           |
        OSCAR Mobile      Desktop     Home Node (future)
      main phone     Worker     spare Android
                                  |
                             ESP32 / Pico
```

## Free-first host selection

Official sources checked on **2026-10-04**. Recheck the actual account, region and
current limits before deployment. Free-first means working within verified free
allowances, not treating trial credits or paid tiers as the baseline.

| Host | Intended OSCAR role | Current selection status |
| --- | --- | --- |
| Oracle Cloud Always Free VM | persistent/stateful Core candidate | preferred first candidate, subject to capacity, eligibility and ARM64 acceptance |
| Vercel Hobby Python/Fluid Functions | bounded web/API/callback/webhook/relay surface | strong complementary candidate within personal-use eligibility and free usage limits |

Both remain replaceable. Neither deployment is performed or accepted in Gate B.

## Persistent Core: Oracle Cloud Always Free

Oracle is the strongest current candidate for OSCAR's first persistent stateful
Core because it provides VM compute and durable block storage. This is OSCAR's
selection judgment, not a provider availability or workload-fit guarantee.

For Always Free A1 tenancies, Oracle documents 1,500 OCPU-hours and 9,000 GB-hours
monthly, equivalent to **2 OCPUs and 12 GB RAM total**, across the tenancy's A1
instances. It also documents **200 GB combined boot/block storage** in the home
region. [Oracle Always Free resources](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm)

Selection depends on regional capacity and account eligibility. A1 is ARM-based:
verify OSCAR's Python runtime, Qdrant, Neo4j/Graphiti, ONNX/local ML packages,
images and representative workloads on ARM64 before claiming compatibility or
that the full memory stack fits this allowance. Core coordination can be separated
from derived retrieval/ML services without moving canonical ownership.

Oracle can reclaim idle Always Free compute. Its documented seven-day criteria
are CPU 95th-percentile utilization below 20%, network below 20%, and, for A1,
memory below 20%. Plan durable backups, restore, coordinator replacement and
explicit unavailable states; an Always Free VM is not an uptime guarantee.
Do not manufacture load to evade reclamation.
[Oracle idle-instance rules](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm)

## Bounded API/web surface: Vercel

Vercel supports Python ASGI/WSGI applications as Functions. Hobby is free for
personal, non-commercial use. It is a strong candidate for the public frontend,
web/API surface, OAuth callbacks where the provider flow needs them, lightweight
relay/rendezvous endpoints, webhooks, stateless connector endpoints and bounded
event/function workloads.
[Python runtime](https://vercel.com/docs/functions/runtimes/python),
[Hobby plan](https://vercel.com/docs/plans/hobby).

Current Fluid Hobby allowances include 4 active CPU-hours, 360 GB-hours of
provisioned memory and one million invocations per month. Python Fluid Functions
have a 300-second Hobby maximum invocation duration and 2 GB memory limit.
Exceeding free usage can pause service. Keep budgets and explicit degradation;
do not silently require a paid plan.
[Fluid usage](https://vercel.com/docs/functions/usage-and-pricing),
[Function limits](https://vercel.com/docs/functions/limitations),
[Hobby limits](https://vercel.com/docs/plans/hobby).

Functions alone are not the sole canonical persistent OSCAR Core. Durable archive,
task/lease state, idempotency, recovery, scheduling and node/session lifecycles need
separately demonstrated persistence and lifecycle contracts. Function instance
memory or a temporary filesystem is not canonical durable history. A later design
can use durable external state/services if it proves the whole contract; Python
deployment support alone does not prove it. Callback endpoints never supply owner
authorization or turn local disconnect into remote revocation evidence.

```text
Oracle VM -> persistent/stateful Core candidate
Vercel    -> stateless/bounded API + web + relay surface
```

## Embodiments and future Home Node

| Node | Role and boundary |
| --- | --- |
| OSCAR Core | identity/state/memory/task coordination on replaceable hosts |
| OSCAR Mobile | owner's everyday main-phone embodiment/control surface |
| Desktop | powerful execution Worker; optional to Core availability |
| Samsung Galaxy Tab S6 Lite (2021), owner-described device | future always-on local Home Node |
| ESP32 / Pico | Edge nerves/reflexes/sensors/actuators; deterministic local hardware safety |

**Owner sequencing decision:** build the Tab/Home Node only after OSCAR is fully
deployed and the main Core architecture is operational. Do not start Android or
Termux implementation now, and do not make the tablet a Gate B requirement.

Future candidate roles, each subject to Android capability and owner permission:

- always-on local Grid presence and LAN/Bluetooth connectivity;
- ESP32/Pico bridge and sensors/peripherals where Android permits;
- notification/local-control surface with separately granted permissions;
- lightweight cache/checkpoint/survival state if later justified;
- optional local services only after practical device tests.

Do not assume the tablet hosts the full canonical Qdrant + Neo4j + ML stack.
Background longevity, OEM behavior, battery/thermal management and local service
feasibility remain untested on the actual device. Home Node presence, perception,
retention and action are separate grants. ESP32/Pico do not host the full Core;
physical safety remains local and deterministic during Core/Grid/network loss.

## Gate and deployment boundary

Slice 05/06 COMPLETE for the documented local-alpha scope; Gate B PASS after
owner physical machine and GitHub OAuth/federation acceptance. Remote revocation
remains unknown. Slice 07 software is accepted; physical acceptance is deferred by owner; PR 12 is MERGED; Gate B frozen PASS.

Oracle deployment, Vercel deployment, Galaxy Tab expansion, post-Gate-B System-1
evaluation and full Auth Broker expansion are later work, not Gate B completion
requirements. Current local control shares SQLite/loopback; these docs do not
claim remote Core deployment or phone control. The bounded GitHub private
read/restart/federation path has been accepted; broader connectors remain unverified.

See [architecture](ARCHITECTURE.md), [Grid](CONNECTION-GRID.md),
[authentication boundary](CONNECTOR-FABRIC.md), [security](SECURITY.md) and
[current gates](BUILD-GATES.md).

## Owner scope decision — 2026-10-05

Slice 07: **COMPLETE FOR SOFTWARE / SIMULATED EDGE FOUNDATION**.
**PHYSICAL EDGE ACCEPTANCE DEFERRED BY OWNER** — `DEFERRED_BY_OWNER / NOT_PHYSICALLY_VERIFIED`.
Protocol, firmware, Grid integration, ESP32/Pico cross-builds and deterministic
safety contracts in simulation are accepted for continuation. Historical
simulator evidence remains **SIMULATED**. No physical GPIO, watchdog, UART,
E-stop or ESP32/Pico silicon PASS is claimed. Gate C remains **PARTIAL**.

Return to real ESP32/Pico acceptance during Slice 15 physical/device expansion
and/or Slice 16 reliability/security hardening. Physical failure, loss/recovery,
watchdog and safety/reflex verification remain mandatory before Slice 17
Unified Alpha can PASS. The hardware acceptance guide is preserved.
The 2026-10-05 scope authorized Slice 08. The 2026-10-06 owner decision additionally
authorizes Slice 09 software after Slice 08 integration; Slice 10, deployment and
Galaxy Tab Home Node remain outside this work.

## Post-alpha evolution direction

### Dedicated home-server target

The intended mature deployment is an owner-controlled dedicated home-server
laptop, not the current development machine.

Where hardware permits it should eventually host the persistent Core, Memory
Fabric, local Model Router, Operating Logs, specialist model pool, local voice
services, durable Workers/queues and home/device coordination.

The baseline daily experience should progressively become cloud-independent.
Cloud models remain available as explicit replaceable escalation for major work,
frontier capability, recovery and temporary orchestration while local
orchestration matures.

This migration happens after measured stable-alpha use; it does not change current
Gate/Cloud deployment claims.

See [Post-Alpha Evolution](POST-ALPHA-EVOLUTION.md).

## Historical Slice 09 checkpoint — 2026-10-06 (superseded)

Slice 08 PR #14 merged; accepted main/work baseline
`92a11aa05083f1983186976ba64bd30aa9f1f2a0`. Slice 08 is
**COMPLETE FOR SOFTWARE / REFERENCE VOICE FOUNDATION**; physical voice is
`DEFERRED_BY_OWNER / CONSOLIDATED_GATE_C_ACCEPTANCE_REQUIRED`, never physical PASS.
OSCAR Mobile Kotlin/Compose rebuild is on `club-c/slice-09-sunday`, draft PR #15
into `work`, **PARTIAL / OWNER_DEVICE_ACCEPTANCE_NOT_RUN**. Core/loopback,
Gradle/JVM/emulated evidence is separate from actual phone/OEM acceptance.
See [OSCAR Mobile foundation](MOBILE-FOUNDATION.md) for implementation, limits and the next owner boundary.
Slice 09 must not merge in this run. Gate C remains PARTIAL. Slice 10, deployment
and Home Node are not started. Post-alpha Operating Logs, specialist-model training
and home-server migration remain documented future work, not implemented.
