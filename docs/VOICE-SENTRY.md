# Voice + Sentry

## Voice is a primary interface

OSCAR supports voice across Sunday, desktop, desk hardware and other connected surfaces. Text remains equally valid and shares the same task/context state.

Voice has four distinct layers:

1. **Voice Input** — wake, VAD, STT, barge-in and dictation.
2. **Voice Identity** — OSCAR's stable synthesized voice and speaking behavior.
3. **Voice Match** — authorization-oriented owner/authorized-speaker verification.
4. **Voice Map** — perception-oriented recognition of who appears to be speaking.

Sentry consumes local acoustic/device/environment signals persistently when enabled. This is broader than an ordinary wake-word feature.

## Presentation boundaries

Sunday presents **presence**, **acoustic state** and **attention** separately. `Sentry aware` is local acoustic perception, not an active conversational STT turn. `Listening` belongs to an activated conversational turn. Choosing text changes neither Sentry policy nor voice availability. Conversation mute pauses ordinary conversational turns; configured local perception/reflex/safety paths may remain available. Acoustic-awareness disabled is a separate software policy state, not proof that every microphone is physically disconnected. Missing Sentry/microphone/desktop evidence must become unavailable or unknown rather than an assurance that everything is quiet.

The [current browser study](../prototypes/sunday/README.md) demonstrates these presentation distinctions with explicit scripted fixtures; it does not implement voice processing.

## Runtime audio model

```text
microphone
  ↓
local audio front end
  ├─ echo/self-voice cancellation
  ├─ VAD
  ├─ wake/hot/reflex detection
  ├─ configured sound-event detection
  └─ Voice Map speaker signal
  ↓
Sentry / activation / policy gate
  ↓
streaming STT only when the selected capture/listening mode requires it
  ↓
Jev / capability / model path
  ↓
result
  ↓
OSCAR Voice Identity / TTS
```

## Acoustic states — do not conflate them

### Sentry aware

Persistent local acoustic/event awareness is active. OSCAR can detect wake/hot commands, speech presence, Voice Map events and configured sounds without necessarily producing a transcript.

### Listening

An active conversational turn is underway and speech recognition is running.

### Muted

Normal conversational listening/speaking behavior is suppressed according to policy. Permitted deterministic safety/reflex commands may remain locally available.

`Muted` must not imply physical microphone shutdown unless that stronger state is actually active.

### Acoustic awareness disabled

Local acoustic processing itself is disabled. This is a stronger privacy state than ordinary mute.

### Typing

Typing is another input modality. Choosing text does not automatically turn Sentry or acoustic awareness off.

## Sentry is persistent presence

Sentry is OSCAR's always-present awareness system. It watches local acoustic, device, sensor, communication and presence events and selectively escalates meaningful situations.

When enabled, Sentry should feel like OSCAR is **there**, not dormant until a button is pressed.

```text
microphones / sensors / devices / communications
                         ↓
                  Perception Fabric
                         ↓
                     Sentry
       awareness • correlation • significance
                  /                \
               ordinary          meaningful
                  ↓                  ↓
          update context      policy / act / alert
```

Sentry can remain active while OSCAR is not in an explicit conversational turn.

## Sentry modes

### Passive

- wake/hot/reflex commands;
- essential health/safety signals;
- minimal acoustic/presence awareness.

### Aware

- normal persistent environmental/device awareness;
- Voice Map speaker events when enabled;
- low-noise proactive context updates.

### Guard

- higher-priority security/environment awareness according to configured permissions;
- unknown-speaker/door/camera/sensor evidence may matter more.

### Away

- assumes owner is away;
- stronger anomaly significance;
- prioritizes Sunday alerts and remote verification.

### Sleep

- quiet output;
- nonurgent speech suppressed;
- configured wake/reflex/safety/security awareness remains local.

## Optional Sentry Capture / Daily Journal

Persistent Sentry awareness and recording are different capabilities.

The user may explicitly opt into richer continuity capture.

### Awareness only — default

```text
local wake / VAD / Voice Map / sound / device events
→ compact state
→ no continuous transcript or raw-audio retention
```

### Context capture

Authorized sources may be transcribed/indexed/summarized so OSCAR remembers what happened, while raw media is minimized or short-lived by default.

Possible sources, only where legitimately accessible:

- phone calls;
- supported app calls;
- SMS/messages;
- email;
- meetings;
- voice notes;
- in-person conversations through an authorized microphone;
- ambient day-to-day context/events.

### Daily journal

Explicit durable life-log style capture across selected sources with per-source retention, consent and privacy rules.

A Daily Journal can create a searchable timeline of conversations, commitments, decisions and events without requiring every raw recording to live forever.

## Capture is source-specific

A single `record everything` switch is not sufficient.

OSCAR must know what the platform actually exposes.

Examples:

```text
email/messages
→ authorized channel/API/device access
→ content/event ingestion

phone call
→ call metadata may be available while call-audio access is not
→ audio capture only if OS/platform/law permits

WhatsApp/Telegram/etc.
→ official integration or legitimate device capability
→ never assume call audio/control exists

in-person conversation
→ authorized microphone
→ local VAD/diarization/STT according to capture policy
```

Unsupported capture remains unsupported rather than silently approximated.

## Recording, transcription and retention are separate

The following controls remain independent:

```text
local wake/VAD
Voice Map speaker recognition
sound-event classification
activated conversation STT
ambient/context STT
raw audio retention
transcript retention
summary retention
memory extraction
```

A user can, for example, allow local ambient transcription, discard raw audio immediately and retain only a daily summary.

## Consent and legal boundary

Recording laws differ by place, channel and participant.

OSCAR must support:

- clear recording/capture state;
- jurisdiction/policy-aware consent requirements where known;
- explicit per-source enablement;
- participant/person exclusions;
- privacy zones/times;
- fast pause/stop commands;
- delete/forget controls;
- configurable retention;
- disclosure when OSCAR acts/records where required.

OSCAR must not be designed around covert recording.

## Continuity processing

When capture is enabled, the preferred pipeline is:

```text
source event/audio/text
→ local/device processing where practical
→ classify/diarize/transcribe if permitted
→ extract people/projects/tasks/commitments
→ create provenance-qualified context record
→ update World Model if current
→ update LRA/memory only according to retention policy
→ raw material expires according to policy
```

Long transcripts are not automatically permanent memory. Summary/fact extraction and raw retention are separate.

## Fast privacy controls

Sunday and desktop/physical surfaces should make these easy:

- `Pause capture`;
- `Mute`;
- `Sentry off`;
- `Acoustic awareness off`;
- `Forget the last 10 minutes` where technically possible;
- delete a conversation/day/source;
- exclude a person/place/source from durable capture.

Deletion claims must match actual storage/backups/connected-source behavior.

# OSCAR Voice Identity

OSCAR's voice is a first-class product asset, not a provider default.

A provider-independent `VoiceProfile` can include:

```text
voice/model reference
speaking rate
pitch/range policy
prosody/expressiveness
pronunciation lexicon
pause/rhythm behavior
volume/ducking policy
speaking mode
fallback mapping
version
```

Persona affects tone/humor/formality/timing while Voice Identity stays recognizably OSCAR.

See `docs/PERSONA.md`.

## Speaking modes

- normal;
- quiet/night;
- focused/serious;
- alert;
- representative/professional.

Safety/security contexts suppress inappropriate humor/playfulness regardless of Persona.

## Barge-in

Barge-in is mandatory.

If a real person interrupts while OSCAR speaks, current TTS should stop promptly and input becomes authoritative according to policy.

Requires:

- cancellable TTS;
- active utterance/task IDs;
- VAD while TTS is active;
- echo cancellation;
- playback reference;
- explicit interruption semantics.

## Self-voice suppression

OSCAR must not hear itself as another person.

Use where available:

- acoustic echo cancellation;
- playback-reference audio;
- TTS-origin tagging;
- timing/correlation;
- exclusion of OSCAR TTS from Voice Map learning.

Self-voice suppression must preserve human barge-in.

# Voice Match

Voice Match answers primarily: **is this an authorized speaker for this action?**

It is convenient identity evidence, not cryptographic authentication.

High-risk actions require stronger factors such as Sunday biometric/PIN/explicit approval.

## Authorization levels

| Level | Typical actions | Voice policy |
|---|---|---|
| 0 — Safety | stop dangerous hardware / silence | available broadly where safe |
| 1 — Harmless | time, basic local state | configurable |
| 2 — Personal | private calendar/memory/device context | authorized speaker normally required |
| 3 — Sensitive | messages, important app/file actions, capture/Sentry settings | stronger identity + contextual/explicit confirmation |
| 4 — Critical | financial/security/destructive actions | voice alone insufficient |

# Voice Map

Voice Map answers: **who appears to be speaking?**

It is perception, not authorization.

Possible states:

```text
owner
known_person
recognized_but_unverified
unknown_speaker
multiple_speakers
uncertain
```

Rules:

- unknown remains unknown rather than guessed;
- real-world identity linkage requires evidence/confirmation;
- confidence remains explicit;
- recognition grants no permission by itself;
- profiles/embeddings are sensitive biometric-like data;
- OSCAR's own TTS is excluded.

Where enabled, Voice Map can emit compact events without full transcription:

```text
speech_started
speech_ended
speaker_changed
known_speaker_present
unknown_speaker_present
multiple_speakers_detected
```

# Reflex / hot commands

Initial deterministic candidates:

- `Oscar`;
- `Mute`;
- `Stop`;
- `Cancel`;
- `Enough`;
- `Listen`;
- `Sentry`;
- `Stand down`;
- `Pause capture`.

These should not require frontier-model reasoning.

# Event policy

Sentry events should carry:

```text
importance
urgency
confidence
interruptibility
source
correlation/task ID
```

Typical outcomes:

- ignore/discard;
- compact context update;
- durable journal entry if enabled;
- Sunday notification;
- spoken alert;
- urgent interruption/action within authority.

## Safety separation

Physical emergency protections remain deterministic:

- thermal cutoffs;
- over-current protection;
- motor/relay interlocks;
- emergency stop;
- battery protection.

Sentry/cloud intelligence may coordinate or alert but never replaces those paths.

## Invariants

1. Sentry is persistent awareness when enabled, not merely a wake-word screen.
2. Sentry awareness does not automatically mean cloud transcription or durable recording.
3. Optional Context Capture/Daily Journal may retain authorized day-to-day communications/conversations under explicit policy.
4. Every source is capability- and consent-aware; unsupported capture is never fabricated.
5. Raw audio, transcripts, summaries and memory extraction have separate retention controls.
6. Voice Match and Voice Map remain separate.
7. Persona cannot weaken voice/privacy/security rules.
8. OSCAR's own TTS never becomes an external speaker identity.
9. Local safety/reflex paths continue if cloud/model layers fail.
