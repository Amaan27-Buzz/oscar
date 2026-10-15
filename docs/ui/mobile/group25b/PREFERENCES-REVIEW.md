# Preferences redesign — 2026-10-15

The owner requested a redesign of the Preferences subpages after the whole-app
review. This follow-up replaces loose text and links with grouped native controls,
short status rows and page-specific layouts. It preserves the original reference
artwork and the owner's later preference for functional, compact screens.

The current phone captures are in [preferences/](preferences/). The previous
`native/` and `screens/` captures remain historical evidence for their receipts.
The exact build, test and APK record is [preferences-review.json](preferences-review.json).

Final validation: **29 native PASS / 4 intentionally SKIPPED / 0 FAIL** in
129.587 seconds; 23 app and five shared-expression JVM tests passed; Gradle
assembly/lint passed with zero errors and 13 warnings. The 24 Mobile/reference/
canonical-document Python checks passed. All three installed APK hashes match
the built artifacts, and the updated normal OSCAR app was opened on the phone.
The emulator stayed off and the temporary reference Core was stopped.

The initial focused run had one timeout while checking corrupted-session
restoration. Its isolated recheck and the full final run passed. The native
session implementation was unchanged; both results are retained in the receipt.

| Page | Revised presentation | Phone capture |
|---|---|---|
| Preferences | Personal, Your context, Control and Application groups with labelled glyphs | [Light](preferences/review-preferences.png) |
| Persona | Larger canonical expression preview and four single-target radio rows; preview-only scope remains visible | [Light](preferences/review-persona.png) |
| Voice | Setup status, Android audio grants and current output route | [Light](preferences/review-voice-settings.png) |
| Privacy | Separate Perception, Notification context, Retention and Actions groups; source editor and details expand; local revoke remains explicit | [Light](preferences/review-privacy.png) |
| Awareness | Compact dark mode/status, permissions and retention groups; unavailable modes remain disabled | [Phone](preferences/review-awareness.png) |
| Memory | Core ownership, unavailable phone history tools, and local draft/response handling | [Light](preferences/review-memory.png) |
| Access | Current Ask status and unavailable Secure/Full Access modes; delegation constraints expand | [Light](preferences/review-access.png) |
| Android permissions | Actual assistant-role status and native selection action | [Light](preferences/review-android.png) |
| Notifications | Actual Android alert grant, task-alert switch, source access and available reply controls | [Light](preferences/review-notifications.png) |
| Appearance | Three selectable theme previews and a separate Comfort group | [Light](preferences/review-appearance.png) |
| Diagnostics | Connection and app/device label-value rows; runtime notes expand | [Light](preferences/review-diagnostics.png) |
| About | Compact canonical Orb identity, version and surface; privacy/device details expand | [Light](preferences/review-about.png) |

[Normal-text contact sheet](preferences/light-contact.jpg) ·
[Dark, 1.8× text contact sheet](preferences/large-dark-contact.jpg).
The enlarged-text run uses Compose's font-scale override within the isolated
review app; it does not change the owner's Android settings. At larger text sizes,
values stack below labels, controls move below their descriptions and theme
previews become full-width rows. Section labels expose accessibility headings.

Every subpage retains one Back toolbar and no bottom navigation. Shared entry,
press and expanding-section motion remains active unless Android or the owner
requests reduced motion. The canonical expression engine remains unchanged.

`PreferencesReviewTest` checks all three theme selections, persistence through
Activity recreation, normal-size preview alignment, all 11 subpages in dark 1.8×
text, and scroll access to the lower Privacy and Appearance controls.
Existing settings/privacy tests cover local grant independence, source validation,
revocation, reduced-motion persistence, landscape, keyboard clearance and native
navigation. Test fixtures and screen capture remain restricted to the opted-in
`.review` identity; owner app data, system grants and global settings are untouched.

These are native rendering and software checks on the owner's Samsung phone with
disposable data. Final owner visual acceptance, real audio, biometric signing and
OEM capability commissioning remain separate. No merge or later backend work is
included; unavailable capabilities remain unavailable.
