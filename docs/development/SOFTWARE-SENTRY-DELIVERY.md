# Sentry notice delivery — local software candidate, 2026-10-22

World Runtime now consumes Sentry's interruption proposal instead of discarding
it. `SentryDelivery` uses the existing Perception Fabric, Sentry, World Model and
Personal Policy. It creates at most sixteen transient generic notices. No
observation value enters the notice, notification body or Event Archive. A
bounded persistent fingerprint receipt suppresses identical source values after
polling, reconnection or Core restart; it is delivery metadata, not memory or a
retention grant. Restart discards pending notices rather than replaying them.

Delivery requires a separately signed, explicit `Allow` Personal Policy for
`sentry:deliver`, as well as the current source's perception/action grants,
selected source/trigger, Sentry interruption setting and `sentry:interrupt`
policy. There is no default delivery permission. Policy conflict, revocation,
source epoch/lease loss, configuration generation changes, conflicting or changed
current state, sleep and expiry suppress projection. Each notice is tied to its
original observation, source epoch and configuration generation. Its lifetime is
the earlier of observation expiry and sixty seconds. Identical fresh polls do
not renew that lifetime. Delivery never executes a task or mutates a schedule.

The existing authenticated management snapshot carries generic notice metadata.
Desktop awareness renders it in-app using the native Core clock and current
grants; it does not claim an operating-system notification. Android awareness
does the same and `TaskNotifications` can additionally post a generic native
notification, only with local activity-alert opt-in and actual Android
notification permission. Native notification IDs and consumed receipts prevent
replay after native process recreation. Receipts are written before dispatch:
an uncertain platform outcome is not retried. Revoked metadata cancels posted
notices on readback, and Android timeout bounds disconnected notifications.
Notifications contain no source ID, observation value or private task text.

Desktop and Android source settings now allow explicit trigger-key editing;
Desktop also exposes the existing signed interruption toggle. These controls do
not grant microphone/camera access, raw capture, durable retention or delivery
permission. Calendar and weather reports retain their confidence; no confidence
upgrade or automatic urgency inference was introduced. Sleep suppresses all
notices from these nonurgent poll adapters. Configuring a source does not assert
that an unavailable source is operational.

Validation currently established:

- 56 Python tests passed across delivery, World Runtime and World Model,
  including an actual selected-file poll, absent delivery/action grants, sleep,
  nontriggers, stale/conflicting state, policy conflict/revocation, generation
  changes, no canonical retention and identical-value restart suppression.
- Nine Desktop tests across the awareness notice and operating settings suites
  passed; TypeScript type checking passed. The rendered attention status is
  asserted, along with stale/revoked/changed-generation suppression.
- Android debug APK, instrumentation APK compilation, 75 JVM tests across 18
  suites and lint passed. Android instrumentation cases include actual Compose
  and NotificationManager resulting-state checks. The actual disposable API35 emulator campaign then passed its one native
  surface test in 6.057 seconds: real Compose display, Android permission/local
  opt-in denial, aged-response rejection, shortened remaining timeout, generic
  NotificationManager readback, receipt replay suppression and source-act
  withdrawal. Source/APK hashes remained stable; both fixture packages were
  uninstalled and their absence was read back. This campaign uses synthetic
  metadata, so it is native rendering/delivery evidence, not signed remote Core
  or live perception acceptance.

The Android test requires a fresh explicitly disposable AVD installation with
notification permission initially denied and `sentry_disposable=true`. It grants
that permission during acceptance; the campaign must uninstall its fixture on
completion. It does not touch a physical phone, real accounts, private messages,
microphone or camera. Hosted background push, Desktop OS notifications and
spoken interruptions are not established by this candidate.

[Source-scoped receipt](../evidence/software-completion/sentry-delivery-2026-10-22.json) records exact commands, hashes, results and limitations.
