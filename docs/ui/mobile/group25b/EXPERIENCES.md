# Mobile experience mapping

The active docs refer to a 56-experience scope but do not contain a numbered
56-row source inventory. This reconciliation enumerates 56 experiences from
`MOBILE-DESIGN.md`, `SURFACES.md`, `FEATURES.md`, existing native screens and the
15 approved heroes. It is an implementation coverage map, not an invented
claim that an original numbered owner inventory was retrieved.

Primary destinations are Conversation, Automations and Activity. Secondary
destinations use native navigation; contextual details use full-screen native
dialogs. Planned capabilities remain explicitly unavailable.

| # | Experience | Surface / current behavior |
|---|---|---|
| 01 | Home / presence | Conversation, real connection/task/voice state |
| 02 | Continuous interaction | Conversation, chronological session readback; archive retrieval unavailable |
| 03 | Text composition | Pinned native composer, bounded encrypted draft |
| 04 | Expanded response | Full-screen editorial reading, Core response/evidence |
| 05 | Contextual follow-up | Reading returns to the same composer |
| 06 | Attachments | Unavailable, no attachment API or fake picker |
| 07 | Action result | Conversation/task detail, verified value vs reported prose |
| 08 | Related task | Contextual Activity link and inspect |
| 09 | Waiting / loading | Actual Core busy state, indeterminate indicator |
| 10 | Stop waiting | Existing request cancellation, no inferred task cancellation |
| 11 | Offline / degraded | Connection status, disabled sending, reconnect entry |
| 12 | Private context discard | Existing discard command and authoritative message |
| 13 | Encrypted draft recovery | SessionVault recovery; content excluded from saved Bundles |
| 14 | Voice entry | Immersive native Voice presentation |
| 15 | Start listening | Existing Android/OSCAR grant + commissioned adapter boundary |
| 16 | Mute / cancel voice | Actual adapter cancellation and capture state |
| 17 | Speech playback | Uncommissioned, explicit unavailable state |
| 18 | Voice Identity | Settings/Voice; Core-owned identity, no vendor identity switch |
| 19 | Voice Match / Map | Voice detail, unavailable until enrolled; never authorization |
| 20 | Headset / Bluetooth | Real Android permission/communication-route inspection |
| 21 | Automations overview | Primary destination; persistent runtime unavailable |
| 22 | Worker detail | Secondary Automation view; unconfigured responsibility/scope/state |
| 23 | Create responsibility | Native draft form, creation unavailable |
| 24 | Timing / schedule review | Draft timing; no parsed or deployed schedule claimed |
| 25 | Worker autonomy | Unavailable; separate from Access |
| 26 | Scope / assigned devices | Worker detail, no grants or assignments invented |
| 27 | Linked automations | Worker detail, no configured links |
| 28 | Run / pause Worker | Disabled; current task controls remain Activity |
| 29 | Activity timeline | Primary destination, actual Core tasks |
| 30 | Active / finished filtering | Native selection controls over current readback |
| 31 | Active task detail | Full-screen task/evidence inspector |
| 32 | Worker checkpoint | Only actual reported fraction/step; no simulated percentage |
| 33 | Task cancel | Fresh Core review and signed native decision |
| 34 | Task continuation / retry | Only advertised Core actions; fresh review |
| 35 | Approval / decision | Exact request/material/target/consequence with expiry checks |
| 36 | Deny request | Fresh denial review, Android confirmation; no tap-as-execution |
| 37 | Evidence / artifact detail | Task inspector; provenance/verification distinctions |
| 38 | Grid / Devices | One-tap app-bar secondary destination, current snapshot |
| 39 | Node / capability detail | Expandable real nodes; no uncommissioned node examples |
| 40 | Pair / connect | Scoped-session native dialog, password-obscured token |
| 41 | Local disconnect | Existing local credential removal; remote revocation separate |
| 42 | Remote power / wake | Unavailable; no Mobile capability advertised |
| 43 | Today / planning brief | Secondary Conversation view, local date/current Core tasks |
| 44 | Calendar / commitments | Explicit disconnected provider state |
| 45 | Weather / travel context | Unavailable; no forecast or location invented |
| 46 | Communications brief | Unavailable until supported Core provider integration |
| 47 | Awareness / Sentry | Preferences secondary view; Manual, Sentry unavailable |
| 48 | Capture / recording | Uncommissioned; no false observation or recording indicator |
| 49 | Retention / journal | Privacy explains off/unavailable policies; no new storage backend |
| 50 | Access modes | Ask semantics, Secure/Full Access activation unavailable |
| 51 | Persona | Explicit simulated expression preview; Core policy unchanged |
| 52 | Privacy / Android grants | Actual independent observe/retain/act grants and revocation |
| 53 | Notifications / replies | Existing listener/exclusions/alerts/RemoteInput reviewed flow |
| 54 | Assistant / overlay / widget | Android role selection; overlay/widgets unavailable |
| 55 | Appearance / accessibility | Light/dark/system, reduced motion, native font scaling |
| 56 | Memory / diagnostics / about | Human-facing Memory boundary; technical details in diagnostics |

No canonical roadmap numbering changed. Backend work for Sentry, standing
delegation, persistent Executive and Adaptive Interface Engine is not included.
