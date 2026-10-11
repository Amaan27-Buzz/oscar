# 13.6 privacy and permission implementation / independent review

Implemented by the Mobile reviewer; independently reviewed by the parent agent
before native validation. **ACCEPT bounded software/reference closure.** The parent
challenged immediate voice-epoch revocation and SharedPreferences failure claims;
both were corrected before the final native run. This is not a claim that the
implementer independently reviewed their own changes.

## Narrow architecture change

Privacy/notification surfaces and existing grant helpers moved from SettingsScreen
to `PrivacySettings.kt`; existing Voice/Platform callers keep the same helpers.
No Voice implementation, theme, Core authority or networking client was replaced.
Android grant state refreshes on foreground resume, and local grants observe actual
preference changes. Settings/permission handoffs use legitimate Android flows;
missing platform flows return unavailable feedback rather than inventing a grant.

CAN PERCEIVE, CAN RETAIN and CAN ACT remain independent. Notification perception
requires actual Android listener access, a separate local grant and an explicit
source allowlist; empty/unlisted sources are excluded. Source validation does not
enable reply or retention. Raw audio/notification retention remains off. Only an
unsent text draft is locally encrypted for recovery; Core retains its independent
memory-policy boundary. Camera/location, overlay, local/cloud configuration and
person-level policy authoring are not fabricated as supported controls.

Notification rows now expose source metadata rather than raw private notification
titles. Content changes remain bound into the notification identity hash. Source
revocation/removal, lifecycle changes and Core epoch changes retire cached reply
rows/drafts; current source identity and the separate reply grant gate review.
Final native send still rechecks actual permissions/source/fingerprint/permit.
Transient source context can be cleared. Local revoke atomically withdraws
perception/reply/source preferences and immediately cancels VoicePresentation's
epoch plus service. No listener, microphone or background capture is implicitly
started. Persistence failures say unverified; they do not assume that a failed disk
commit preserved previous in-memory state. Generic task alerts remain private and
carry no objective/response text.

## Validation and actual capture

App debug and instrumentation APK assembly passed. JVM app **20 tests PASS**, zero
failures; shared expression's **5-test result** was Gradle up-to-date in this
implementation run, not a fresh independent expression execution.

Serial API 35 `MobilePrivacyTest`: **3 executed, zero failures/errors/skips**,
13.52 seconds testcase total; Gradle 24 seconds. Tests cover allowlist/revocation
with explicitly simulated platform-policy input, sensitive synthetic notification
metadata redaction and changed-content identity, and actual denied Android access,
invalid source input, foreground preference refresh, independent reply grant and
voice epoch invalidation. No Android permissions, private account, actual message
or owner recording were used. Tests assert emulator-only isolation before touching
fixture preferences; a skipped real-device run does not clear owner settings.

Actual native capture: `13-6-reference-privacy.png`. It shows denied microphone
and listener access, separate off grants and excluded/empty sources. A single
capture test rerun also passed after explicitly hiding the native IME; it was
justified because Compose root capture excludes the system keyboard. Root/inset
settling in this still is not accepted as full IME/landscape/accessibility proof;
that belongs to the 13.8 convergence pass. Production FLAG_SECURE is asserted,
cleared only for disposable test capture and restored in finally.

Receipts: `.tmp/13-6-native-privacy.log` and
`.tmp/13-6-native-privacy-capture.log`; final curated PNG is separate from raw
emulator MediaStore copies. Parent independent code review approved final source
fixes. No demonstrated P0/P1 remains in the scoped paths.

Not checked: real listener ingestion/reply delivery, physical microphone/OEM,
remote revocation or person-level policy authoring. Remaining risk: real permission
revocation, platform settings and sustained accessibility require consolidated
owner/device acceptance; final inset geometry remains a 13.8 obligation.
