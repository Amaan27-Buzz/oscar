# Signed responsibility and procedure authoring - local software candidate

The existing Executive now accepts native action-line authoring through the
same `Assistance` signed owner-review family as exact file responsibilities.
No Worker, goal or action is registered while constructing a review. Core
compiles the instructions against currently advertised capabilities, checks the
owner's actual grants, and displays the complete resolved steps, dependencies,
executor identities, contracts and bounded schedule. Completion recomputes that
material before accepting it. A changed capability or executor session requires
a new review. Every later effect still rechecks policy, owner/session authority,
current access mode and the existing Runtime/Worker contracts.

## Supported instructions

The Desktop Automations form accepts one explicit action per line, at most
sixteen actions and 512 characters in total. It reuses the existing Desktop
action grammar: exact file write/read, list/find files, Git status/diff/branch,
page inspection, and bounded integer addition. Each action depends on successful
independent verification of its predecessor. A missing capability, missing
argument or ambiguous executor is rejected; no inferred action is substituted.
The exact file form remains available for larger or whitespace-sensitive text.

Example instructions with an explicitly selected capable executor:

```text
Write notes/agenda.txt with text Reviewed synthetic agenda
Read file notes/agenda.txt
```

The existing schedule controls supply the start time, fixed interval and
1..100 runs. The Core helper `Assistance.natural_change` also recognizes explicit
bounded phrases such as `Every day for 3 runs: 2 + 2`. An incomplete `Every day`
request does not silently create indefinite standing work. This is deterministic
bounded authoring; arbitrary model-generated plans still use the existing
separately reviewed model-planning contract.

The primary Desktop and connected Android conversation also accepts
`Every day for 3 runs: 2 + 2` and `Create automation: 2 + 2`. Core returns an
unsigned proposal, and the native client opens the same complete signed
Assistance review. Receiving that proposal creates no task, Worker or goal.
Unsupported schedules remain blocked; cancelling review leaves the draft
available. Account/permission/executor changes still invalidate the exact plan.
Desktop keeps the original Core client and content revision while requesting
review, so a late response cannot move private instructions into a replacement
connection. Android checks its connection epoch and management stamp.

## Reusable procedures

Native `learn` requires a completed exact goal, independent canonical evidence
for every step, an explicit retention selection, current owner `retain` scope
and current retention policy. It appends a REPORTED candidate to the Event
Archive for at most seven days. The derived procedure record contains the
canonical event reference rather than a second copy of memory.

`reuse` retrieves that canonical source and proposes the exact original steps
under current executor capabilities and owner grants. A fresh signed review is
required before registration, and the new goal receives the current native
owner binding. It never copies the original action's consent or standing access.

`evaluate` separately reviews retention of an independently verified, completed
replay with the same steps/conditions and different canonical tasks. Its readback
is **exact replay verified**, never unrestricted reliability or new authority.
Expired, forgotten or invalid source/evidence records withdraw the procedure.
Replay does not parameterize or generalize the original instructions.

Native retention writes use the challenge ID as their immutable archive receipt.
If the archive append succeeds but the State transaction fails, retrying the
still-valid signed completion recovers the same event without extending its
retention or appending a second copy. Expired/forgotten receipts cannot be
resurrected by this recovery path.

## Review and lifecycle corrections

All Assistance reviews now sign and display `material.review`, containing the
original change, relevant current state and any resolved create proposal.
Android's management parser checks this exact object and its original change.
Resume shows the complete prior goal/Worker scope and renews the current signed
owner binding, so an expired owner session can be replaced through explicit
review. It does not make an expired session valid.

Source-grant and Sentry reviews bind configuration/epoch rather than volatile
connection refresh timestamps. Live polling therefore does not constantly
invalidate the owner's prompt. Actual grant/contract changes still invalidate
it. World source grants rebind the poll epoch atomically through WorldRuntime.
The native `source_create` review includes the ambient adapter's exact fields,
account/service scope, filters, freshness and independent retention/action grants.

## Verification and limits

Local synthetic checks exercise signed creation, real Executive arithmetic,
dependency ordering, no execution before review, unsupported/missing arguments,
separate retention, source/evaluation provenance, reviewed replay, expiry,
owner-session renewal, archive/State failure recovery, stable live-source review,
and signed Core-clock source registration. Existing Executive tests additionally
exercise real scoped files, restart/recovery, revocation, ambiguity and policy ASK.

Reproduce with:

```powershell
python -m unittest tests.test_assistance tests.test_executive -v
python -m mypy oscar/assistance.py oscar/executive.py
python -m ruff check oscar/assistance.py oscar/executive.py tests/test_assistance.py
npm.cmd --prefix desktop test
npm.cmd --prefix desktop run build
```

The parent completion ledger records current aggregate counts. This evidence
does not establish physical-device, real-provider, hosted, owner-biometric or
visual acceptance, and does not promote a formal project gate.
