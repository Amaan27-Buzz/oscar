# Android connected Grid software

This extends the approved Kotlin/Compose application and existing `CoreClient`,
`CoreSession`, `SessionVault` and native owner confirmation. The authoritative
protocol is [Grid 2](../docs/development/GROUP-04-D2-PROTOCOL.md). Android remains
a presentation/control client of the same Core, Grid, Runtime and Event Archive.

## Connection and authority

- Devices → Connect Core exports an installation ID and public RSA device key.
  A trusted offline Core operator verifies that identity and issues a five-minute,
  single-use, role/scope-bound invitation. Paste the invitation and trusted HTTPS
  origin into the existing connection dialog. Conversation sharing/retention is
  a separate explicit choice and still requires the Core retention grant.
- Android Keystore retains the nonexportable device proof key. It is separate
  from the existing authentication-required owner approval key. AES-GCM seals
  sessions, drafts and a bounded presentation cache; backups remain disabled.
  An emulator Keystore test does not establish hardware backing or owner trust.
- Production uses Android's normal TLS certificate and hostname validation.
  Only debug loopback permits HTTP. Redirects, unbounded bodies, generic remote
  shell and automatic mutation retries are absent.
- Foreground lifecycle polls every five seconds, with exponential backoff and
  bounded jitter after loss. Backgrounding cancels transport/polling and fences
  callbacks; server liveness expires independently. Expired/revoked credentials
  stop reconnect attempts. A lost rotation/enrollment response needs trusted
  re-enrollment, because old sessions are fenced rather than retried.
- Snapshot task/node projections replace local views. Stable event IDs, ordered
  cursors and archive generations deduplicate history and clear forgotten cache.
  A fresh Core observation is required before cached conversation appears.
  Offline views withdraw private readback and never queue approvals or actions.
- Authorized `presence:read` carries the existing canonical Core expression into
  the approved Orb. Stale or non-Core expressions fail closed. Companion's
  separate presence-only connection uses the same signed device proof and still
  requires independent Android overlay/notification permissions and an unlocked
  device; connection enrollment does not activate an overlay. Authenticated Core
  observation time advances with local monotonic time for freshness and expiry;
  the full transport round trip is charged against the lease. Canonical events
  and the strict future/expiry limits remain unchanged despite local clock skew.
- Expanded real Worker devices offer scoped file reads and preparation of exact
  file edits. Core validates, routes and verifies operations. Mutations require
  exact digest/capability/target/session/generation-bound owner review and the
  existing native biometric/device-credential abstraction. A UI button supplies
  no authority. Missing owner enrollment/authentication remains unavailable.
- Devices exposes credential renewal, authenticated remote self-revocation and
  local logout. Logout removes app-owned credentials/cache/device and owner keys;
  local deletion alone is not remote revocation or a secure-erasure claim.
  Clearing local private cache does not forget retained Core history. Trusted
  Core forget triggers a new archive generation on the next authorized sync.

## Software and emulator verification

Build/JVM/lint:

```powershell
Set-Location mobile
.\gradlew.bat --no-daemon :app:testDebugUnitTest :app:lintDebug :app:assembleDebug :app:assembleDebugAndroidTest
```

The JVM checks cover exact request signing, incompatible/expired sessions,
canonical ordering/deduplication/process restoration/forget, conflicting history,
bounded backoff, matching independent evidence and approval plan binding.

All device commands must name an explicitly identified disposable emulator.
First list identities and verify both its AVD name and `ro.kernel.qemu=1`.
Never target a physical phone or use an unqualified ADB device command.

After building both APKs, run the actual Core/Worker acceptance from the repository
root, replacing the serial with the verified disposable emulator:

```powershell
python -m scripts.verify_android_grid --serial emulator-5590 --adb "$env:ANDROID_HOME/platform-tools/adb.exe"
```

The launcher checks the emulator identity, reinstalls both exact build outputs,
and runs the five checks below against a temporary real HTTPS Core and Worker.
This reinstall is required because Gradle's connected-test teardown removes the
instrumentation APK. Failures retain redacted output in ignored
`.oscar/d2-android/instrument-<method>.log`; a skip cannot count as acceptance.

`GridKeystoreTest#exportGridIdentity` writes public installation/key JSON to
`files/d2-device-identity.json`. Read that public file with explicit emulator
`run-as`; create an actual offline synthetic invitation using the same identity.
`GridConnectedTest#connectedGrid` accepts `grid_origin`, Base64 JSON
`grid_invitation`, optional independently verified `grid_task`, and optional
`grid_target`/`grid_path` for a real Worker read. It exercises native enrollment,
network snapshots, task/evidence/history inspection, encrypted credentials,
Activity recreation and actual Devices presentation.

`grid_ca` optionally supplies the disposable test CA as Base64 DER. The
instrumentation process trusts exactly that CA through a temporary SSLContext,
keeps certificate/hostname verification, and restores the previous factory.
This is test-only trust setup; release code has no trust override.

Separate invocations of `GridConnectedTest#processRestored` after process death,
`#connectionLostWithdrawsPrivateState` with `grid_core_stopped=true`, and
`#revokeAndLogout` with `grid_revoke=true` exercise real recovery and deletion.
External-fixture tests intentionally require those explicit prerequisites; their
absence is NOT_RUN, never an integration PASS. Current receipts belong in the
[engineering ledger](../docs/development/GROUP-04-D2.md).

## Later owner-device acceptance — NOT_RUN

The current run forbids physical owner-phone access. A later explicitly
authorized manual acceptance must verify production TLS/endpoint trust, secure
enrollment/recovery/revocation, actual owner biometric/PIN binding, process death,
network changes and revoked/expired sessions on the intended Android/OEM. Test
retention/forget, exact approval/cancellation and independent Worker effects.
Microphone, notification capture, assistant/overlay commissioning and physical
hardware-backed key claims remain separate acceptance; this change enables none
of those implicitly. No physical device action is included in the commands above.
