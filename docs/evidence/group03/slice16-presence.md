# Slice 16 software verification

Core `PresenceRuntime` publishes one relationship-scoped, content-free state with
stable source identity, monotonic persisted generations, transition identity and
a 30-second lease. Active task state is qualified by executor/node/lease truth;
expired ownership becomes unknown. Historical memory never supplies present truth.
Explicit `presence:read`, current node/session scopes and Personal Policy gate
standalone projection and snapshot subscriptions. Existing native polling owns
connect/reconnect and lifecycle invalidation. Old clients retain bounded fallback.

Desktop and Android use the same Expression contract and immutable canonical Orb.
Local microphone/output presentation remains a separate platform observation.
Core preferences select reduced motion and Companion visibility without authority.
The tiny Companion never hosts AIE, task details or approval material. Task views
use three whitelisted primitives with readable fallback, evidence references,
typed Core inspection and 30-second expiry. No arbitrary generated UI executes.

Android's optional overlay starts only from an explicit in-process UI request,
with display-over-apps and visible notification permission. A separate read-only
CoreClient requests only Presence; it never keeps CoreSession/private responses or
audio alive. Hide/dismiss/disable, local disconnect, lock, permission/source loss,
pairing changes and service destruction stop it. START_NOT_STICKY; no boot start.
The foreground service declares the concrete `specialUse` subtype. This follows
[Android service type guidance](https://developer.android.com/develop/background-work/services/fgs/service-types)
and [background-start restrictions](https://developer.android.com/develop/background-work/services/fgs/restrictions-bg-start).
Play distribution admission and OEM behavior remain separate owner gates.

Local verification: 57 focused Python tests passed; Desktop 84 frontend tests,
TypeScript/build, Rust format/Clippy/tests and Windows debug executable passed.
Android JVM tests, debug/test APK assembly and lint passed; canonical SVG/PNG hash
checks passed. New schema tests reject scripts, untrusted primitives, null actions,
oversized descriptors, wrong versions and expired leases. Hardware/emulator tests
were not run. Overlay interaction/dragging, device permission revocation, power,
TalkBack and visual owner acceptance remain pending; no device PASS is claimed.
