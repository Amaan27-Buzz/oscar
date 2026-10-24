# Outbound machine execution — local acceptance, 2026-10-21

`oscar.remote_machine.RemoteMachine` extends the existing outbound Worker poll,
execution journal and delivery protocol with the real `MachineWorker` and
`InteractiveWorker` effects. It does not create another Store, Core, Grid,
account registry, owner identity or scheduler. Native execution reuses the
enrolled session and asks the authoritative Core to check the exact current
delivery before effects and at subprocess cancellation checkpoints.

## Scope and authority

The Core must explicitly enroll machine control, and the local configuration
must explicitly share each installed capability. Advertisement uses the actual
native capability contract. Files, directory/search, allowlisted executables,
commands, Git/repository tasks, typed PowerShell, registered applications/UIA,
clipboard, browser plans and installed coding executors reuse their existing
implementations and local restrictions. Unavailable optional executors are not
advertised. Clipboard and browser permissions remain separate.

Ask requires the signed exact task approval. Full Access requires the existing
current signed standing authority; this adapter does not activate it. Target
session, policy, requester, account generation, lease and cancellation checks
remain authoritative on the Core. A local deny callback is checked by the
existing Worker boundary. Every effect has the existing durable pre-effect
claim: an uncertain claim is rejected on retry rather than automatically run
again.

An optional separate private profile root permits browser accounts using the
exact account ID/generation in the authorized action. `BrowserProfiles` accepts
an explicit authoritative callback for this remote case. It obtains no local
account state: the callback checks the active delivery and the Core checks its
current account record. Profile credentials remain outside the artifact
workspace and are generation fenced. Existing path/reparse protections and
profile locks are retained. No existing owner browser profile is imported.

Native command/UI/browser reports provide bounded metadata. Checked UIA text
and clipboard writes derive a separate read-only observation of the exact
reviewed destination and compare text on Core. General objectives remain
`PARTIALLY_VERIFIED`; they cannot masquerade as independently verified effects.
Objective-specific fixtures inspect other resulting state separately.
Private command/DOM output is cleared from the adapter after each
delivery, and artifact references expose the workspace identity rather than a
native host path.

## Native entry point

Desktop Preferences now provides explicit native setup/start/stop and contained
process supervision for this entry point. See the
[native execution-sharing acceptance](SOFTWARE-DESKTOP-WORKER.md), including its
actual synthetic CNG/DPAPI/TLS/readback receipt and installed-runtime boundary.

Use an already enrolled native DPAPI connection and an explicit local scope:

```powershell
python -m oscar.remote_machine --connection C:\OSCAR\worker-connection.json --scope C:\OSCAR\machine-scope.json
```

Example local scope (replace exact paths with provisioned paths):

```json
{
  "workspace": "C:\\OSCAR\\workspace",
  "workspace_id": "desktop-work",
  "journal": "C:\\OSCAR\\worker-execution.sqlite",
  "capabilities": ["machine.command", "machine.browser"],
  "trusted_host_execution": true,
  "allowed_executables": ["C:\\Python\\python.exe"],
  "browser": true,
  "profile_root": "C:\\OSCAR\\private-browser-profiles"
}
```

The journal and optional profile root must be outside the artifact workspace.
This command does not enroll an identity, grant machine control, approve tasks,
borrow credentials or activate owner authority. Installed-app sharing additionally
requires explicit `desktop: true` and `desktop_app_ids`; installed executables
and native OS restrictions remain enforced. Trusted host commands have the
native process user's authority, not an OS sandbox.

## Executed acceptance

On this Windows host with installed Chromium, all nine
`tests.test_remote_machine` tests passed. They exercise the actual authenticated
Core/Worker route with synthetic enrolled identities and disposable fixtures:

- An approved native Python command writes a file; independent file bytes are
  checked. It has no local Store or Grid and retains no transient output.
- Unallowlisted executables and a local policy deny cannot execute.
- Cancellation kills an actual waiting child process before its later write.
- A durable uncertain execution claim rejects repeated execution with no effect.
- A privately owned Windows WPF fixture receives checked text entry and UIA
  invocation; separate read-only UIA and Core comparison verify text entry;
  an independently inspected resulting file confirms invocation in the fixture.
  A wrong process identity is denied. No owner application is targeted.
- Real Chromium fills and submits a loopback form, writes a PNG, and preserves
  a synthetic cookie across separately approved account-bound launches. Profile
  storage is separate from artifacts. The fixture HTTP server observes the
  actual submission and cookie.
- Revoking an account after delivery prevents execution and profile creation.
- Transport bounds, explicit browser origins and forbidden script steps reject
  malformed or out-of-scope plans.

All 31 existing machine, interactive harness, browser profile and Windows app
workflow regression tests also passed. Ruff passed for the changed Python
modules and focused tests; mypy passed for the four adapter/native/profile
modules. All 29 existing `tests.test_remote_grid` tests passed after integration.
`python -m oscar.remote_machine --help` was exercised.

Remote executor freshness is separate from the native control surface heartbeat.
RemoteGrid advertisements bind the current executor session; only authenticated
Worker advertise/poll/check/deliver traffic renews its existing 30-second Grid
freshness window. A connected Desktop or Android UI can remain online while its
stopped Worker has no available capabilities. Lease acquisition, renewal,
delivery checks and envelope acceptance recheck this boundary. Recovery reaps
expired executor leases before advertising or polling can make capabilities
available again, so a recovered Worker cannot revive an uncertain prior effect.
Session rotation requires a fresh executor advertisement. The 56 focused Grid
and RemoteGrid tests pass, including synthetic-clock expiry with a live UI,
lease rejection, recovery without effect replay, session replacement and the
actual RemoteGrid snapshot/poll path. Ruff and mypy pass for the touched Core
modules.

These are local synthetic software receipts. Real owner accounts, hosted remote
commissioning, production provider authentication, personal data, owner Full
Access activation, physical devices and unrestricted app interoperability were
not exercised. The nine-test suite does not claim acceptance for every installed
coding agent, Git mutation, clipboard or PowerShell operation merely because
their existing executor is reachable through the adapter.

**2026-10-25 remote process artifact verification:** outbound coding and terminal
execution now use a separately authorized file reader and Core comparison for
literal expected artifacts. Signed phone/Core/model acceptance creates a named
remote coding Worker under Ask and synthetic Full; no per-action prompts occur
under a matching standing grant. Process-only grants, missing read permission,
permission-specific policy denial, wrong bytes and reader withdrawal fail closed
without effect replay. This uses synthetic model/agent fixtures and actual Python
children; fresh authenticated coding-provider and general adaptive verification
remain open. [Receipt](../evidence/software-completion/remote-artifacts-2026-10-25.json).
