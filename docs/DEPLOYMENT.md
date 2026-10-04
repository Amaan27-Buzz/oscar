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
        Sunday      Desktop     Home Node (future)
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
| Sunday | owner's everyday main-phone embodiment/control surface |
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
remains unknown. Slice 07 NOT STARTED; PR 12 stays DRAFT/UNMERGED.

Oracle deployment, Vercel deployment, Galaxy Tab expansion, post-Gate-B System-1
evaluation and full Auth Broker expansion are later work, not Gate B completion
requirements. Current local control shares SQLite/loopback; these docs do not
claim remote Core deployment or phone control. The bounded GitHub private
read/restart/federation path has been accepted; broader connectors remain unverified.

See [architecture](ARCHITECTURE.md), [Grid](CONNECTION-GRID.md),
[authentication boundary](CONNECTOR-FABRIC.md), [security](SECURITY.md) and
[current gates](BUILD-GATES.md).
