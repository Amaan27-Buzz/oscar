# Group 2.5B final closure — 2026-10-16

**Owner decision: UI/UX APPROVED / PASS.** The final-closure handoff explicitly
approves all 15 hero experiences, the warm editorial direction, integrated
artwork, native controls, Preferences, navigation, fluid motion and canonical Orb.
This is owner visual approval, separate from engineering evidence and real
audio, biometric/PIN, OEM commissioning, remote CI and Gate C.

The existing branch and draft [PR #6](https://github.com/Amaan27-Buzz/oscar/pull/6)
are retained. Fetch confirmed the clean starting checkout and remote head
`bf1bef17c0ef1fff557b8c0799da110a55909b74`. No new worktree, redesign, rejected
Argon integration, merge or Slice 14 work is included. Earlier receipts,
screenshots and all original design assets remain historical evidence.

## Theme contract and correction

`OscarTheme` previously combined `forceDark` with the saved preference using OR.
Consequently an explicit Light selection could not affect Activity, Voice or
Awareness. A new native regression reproduced that failure on the unchanged
application before the correction.

Explicit **Light** and **Dark** now select that palette on every route, including
these three pages and their details. **System** follows Android on ordinary
routes; Activity, Voice and Awareness intentionally retain the approved immersive
graphite composition as a documented presentation exception. Their appearance
does not indicate active capture, extra permission or authority. No palette,
artwork, typography or navigation design was replaced. The parameter is named
`preferDark` to express that it cannot override explicit preferences.

Existing appearance preferences/listeners remain the persistence mechanism.
Native checks cover switching through Preferences, Activity recreation, restored
selection, both system night configurations in the test composition, all three
immersive routes, and matching status/navigation-bar icon contrast. Android-wide
theme and animation settings are not changed.

## Lifecycle investigation

Historical evidence records two different symptoms:

- `craft-initial-full-native.log`: approval epoch 2 → 3, later CONNECTED, with
  only CREATE/START/RESUME recorded during the wait. An Activity STOP was not
  observed. In the traced production paths, transport/validation failure can
  invalidate the epoch and polling can later reconnect. The old log does not
  identify the underlying exception; this is a mechanism, not a proven cause.
- `canvas-before-header-shade-native.log`: the final denial-readback capture
  found no Compose hierarchy. Cleanup then queried an already-destroyed Activity
  and failed too. The capture failure and secondary cleanup exception are
  established; what initiated destruction is not recorded.

Two fresh expiry runs on the unchanged app passed (37.359s and 37.797s). They
do not disprove the historical failures. Debug builds now record lifecycle
events with configuration/finishing flags, session STOP epochs and current
snapshot/request exception class names. No exception messages, payloads,
credentials, task content or signing material are logged. Every diagnostic is
guarded by `BuildConfig.DEBUG`; no release runtime was exercised.

The first fresh full run was interrupted by the phone call screen: OSCAR's
PAUSE/STOP and epoch invalidation were observed before the expiry refresh timed
out. This explains that attempt, not the historical failures. The same run
also exposed a craft fixture that assumed Awareness ignored explicit Light;
it now checks dark ink under Light, then light ink under explicit Dark.
A subsequent full retry reused a Core whose private seed had correctly been
removed by the previous discard test, failing the seed assertion. Complete
suites must start a new disposable Core, as the existing reference runner does;
that setup error does not justify changing app authority or weakening assertions.

The new integration check exercises actual Activity STOP/resume and recreation,
retained ViewModel identity, cancelled review/reconnect, stale completion
callbacks and fresh challenge IDs. Old approvals must stay absent, a fresh plan
must be opened again, and authoritative Core readback must remain `planned`.
It never approves the owner's biometric prompt or signs a synthetic success.

Authority checks, 30-second Core challenge expiry, Keystore signing, native
confirmation, generation/source fencing, cancellation and mutation retry policy
are unchanged. No historical initiating cause is claimed fixed. The existing
expiry assertions and cleanup failures remain visible rather than being removed
or converted into skips.

The lifecycle pattern was checked against the official Android guidance on
[lifecycle-aware coroutines](https://developer.android.com/topic/libraries/architecture/coroutines)
and [theme configuration changes](https://developer.android.com/develop/ui/views/theming/darktheme).

## Fresh verification

The [machine-readable receipt](closure.json) binds source hashes, installed APK
hashes, every native outcome (including failed attempts), capture hashes,
JVM/lint counts and process-recovery evidence.

| Check | Fresh result |
|---|---|
| Debug/review app builds, review test APK | PASS; Gradle offline, one worker, 768MB heap, existing toolchain/cache |
| App + shared Expression JVM | 28 PASS, zero failures/errors/skips |
| Debug and review lint | PASS; zero errors, 11 warnings in each variant |
| Scoped Python Mobile/Core/reference + canonical docs | 24 PASS |
| Full Samsung native instrumentation | 37 PASS / 4 intentional SKIPS / 0 FAIL, 169.140s |
| Additional expiry/denial/freshness repeats | 1 PASS at 35.597s; 1 PASS at 35.425s |
| Native theme checks | Explicit Light/Dark on Activity/Voice/Awareness, persistence/recreation, both simulated System configurations and the documented immersive exception: PASS |
| Lifecycle authority | STOP/resume, recreation, retained ViewModel, cancellation/reconnect, stale completion callbacks, fresh challenge and plan-review reset: PASS |
| Actual process replacement | Review PID 15339 → 15479 after scoped force-stop/relaunch; encrypted synthetic draft recovered; separate clear hook and empty session XML verified; no automatic task replay |
| Other native coverage | Core/Grid loss/reconnect; native navigation/control semantics; privacy grants/source exclusions/revocation; encrypted recovery; 1.8× text, real IME insets, landscape, rich responses, reduced motion and navigation animation: PASS in the tested reference scope |
| Canonical assets | 21 original PNGs, Orb source and packaged bytes, shared motion bytes and illustration provenance: verified unchanged |
| Repository checks | Required files, local links, removed references and value-silent secret scan: PASS |

Four full-suite skips remain explicit: the optional legacy loopback fixture,
two opt-in process-recovery preparation/clear hooks (run separately), and the
Android-wide disabled-animation condition. Global animation settings were not
changed. A skip is not PASS. Sustained TalkBack is outside this automated check.

All six palette captures were retrieved from the real review app. The Awareness
pair was visually inspected; heading contrast also has native layout assertions.
These supplement the approved 15-hero comparisons without replacing them.

| Route | Explicit Light | Explicit Dark |
|---|---|---|
| Activity | [Capture](closure/closure-light-activity.png) | [Capture](closure/closure-dark-activity.png) |
| Voice | [Capture](closure/closure-light-voice.png) | [Capture](closure/closure-dark-voice.png) |
| Awareness | [Capture](closure/closure-light-awareness.png) | [Capture](closure/closure-dark-awareness.png) |

The normal debug app was updated with `adb install -r`, preserving its app data.
Installed debug, review and test APK hashes match their built artifacts. The
process harness uses the review application ID with the fully qualified
`io.dawnlight.oscar.mobile.MainActivity` class; an initial shorthand component
attempt failed before replacement, and its cleanup passed. That setup attempt
is retained separately from the verified replacement.

For reproduction, start `python -m scripts.mobile_completion_reference --serve`
fresh for each complete native suite, reverse its two loopback ports over ADB,
and use the isolated `.review` runner with `oscar_review_device=true` plus the
fixture's `group02_*` arguments. Tokens remain in ignored local files, never
in this document. Prepare/clear hooks need `group02_process_prepare=true` and
run separately. Ordinary tests never commission an owner account.

## Merge review verdict

**Ready for owner merge review for the bounded Group 2.5B UI/software scope.**
Keep PR #6 draft and unmerged. Explicit theme choices are corrected; fresh native,
Core/Grid, persistence, recovery, JVM, Python and lint checks pass. No failing
test remains on the final verified candidate. Historical intermittent initiating
causes are still unknown, and their absence from final runs is not a proof of
eradication. No authority change was justified by that uncertainty. Remote CI
and the commissioning boundaries below remain open; this is not a production
release, complete Slice 13/Gate C acceptance or permission to begin Slice 14.

## Acceptance limits

The Samsung SM-S721B/API 36 review identity uses synthetic/disposable data over
the production Core/Grid HTTP path. This is real phone rendering/instrumentation
and reference integration evidence, not owner consent, live provider inference,
microphone/playback/AEC/barge-in/Match/Map, biometric/PIN or OEM commissioning.
Sustained TalkBack and assistant/notification commissioning remain pending.
The emulator stays off. GitHub Actions was freshly queried and remains disabled;
remote CI is BLOCKED, not PASS. Gate C remains PARTIAL.

The 56-entry experience map remains a provisional reconstruction because the
original individually numbered source was unavailable. Scheduling/persistent
Workers, provider briefs, Sentry, signed standing Secure/Full Access delegation
and AIE backends remain unavailable. No future capability is added for closure.
