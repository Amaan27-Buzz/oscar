# Voice + Sentry

## Voice is a primary interface

OSCAR should support voice natively across desk hardware, Sunday, desktop and other connected surfaces. Text remains equally valid and must share the same task/conversation state.

Voice is not just STT wrapped around commands. OSCAR needs four related but distinct voice layers:

1. **Voice Input** — wake, VAD, speech recognition, barge-in and dictation.
2. **Voice Identity** — OSCAR's own stable synthesized voice and speaking behavior.
3. **Voice Match** — authorization-oriented verification of the enrolled owner/authorized speakers.
4. **Voice Map** — perception-oriented recognition of known/unknown speakers in the environment, linked to canonical people only when confidence and policy allow.

Sentry consumes the local acoustic layer continuously when enabled, but that does **not** mean continuous cloud transcription or recording.

## Target interaction loop

```text
microphone
  ↓
local audio front end
  ├─ echo/self-voice cancellation
  ├─ VAD
  ├─ wake/reflex detection
  ├─ sound-event detection
  └─ Voice Map speaker signal
  ↓
activation / policy gate
  ↓
streaming speech recognition when needed
  ↓
intent/context decision
  ├─ reflex/local execution
  ├─ tool/capability path
  ├─ ChatGPT
  └─ native OSCAR Model Router
  ↓
streamed result
  ↓
OSCAR Voice Identity / streaming TTS
  ↓
speaker
```

## Latency rules

- Wake acknowledgement should be effectively immediate.
- Reflex commands should stay local.
- Begin speaking as soon as a useful first chunk exists; do not wait for a full paragraph.
- Deep jobs may take time, but OSCAR should acknowledge immediately and work asynchronously.
- Instrument end-to-end latency from audio onset to action/first audio.
- Speaker recognition must not block harmless reflexes that do not require identity.

## Barge-in

Barge-in is mandatory.

If OSCAR is speaking and the user says `mute`, `stop`, `no`, `not that`, or begins a new request, current TTS should stop immediately and the input should become authoritative.

The voice stack therefore needs:

- cancellable TTS;
- active utterance/task IDs;
- VAD while TTS is active;
- acoustic echo cancellation;
- an explicit playback reference so OSCAR can distinguish its own speech from external speech;
- clear interruption semantics.

# OSCAR Voice Identity

OSCAR's own voice is a first-class product asset, not an arbitrary provider default.

The voice identity should remain recognizably OSCAR across Sunday, desktop, desk hardware and provider fallbacks.

A provider-independent `VoiceProfile` should capture, where supported:

```text
voice identity / model reference
speaking rate
pitch/range policy
prosody/expressiveness policy
pronunciation lexicon
pause/rhythm behavior
volume/ducking policy
contextual speaking mode
fallback voice mapping
version
```

## Speaking modes

The same identity can adapt without becoming a different character:

- **normal** — understated conversational default;
- **quiet/night** — softer, shorter and less interruptive;
- **focused/serious** — restrained for failures, security or important work;
- **alert** — concise, high-clarity warnings;
- **meeting/call representative** — controlled and professional when speaking on the user's behalf.

OSCAR should avoid exaggerated theatrical emotion by default. Expressiveness should come from intent, modulation, timing, pacing and emphasis rather than random emotional presets.

## Voice-provider abstraction

The speech stack may use native, local or cloud engines, but OSCAR owns the voice contract.

A provider can be replaced without changing:

- OSCAR's voice identity;
- interruption behavior;
- pronunciation rules;
- speaking modes;
- task/utterance state;
- privacy policy.

Fallbacks should preserve identity as closely as the available engine allows and should report material degradation when they cannot.

## Self-voice suppression

OSCAR must not treat its own speaker output as a person speaking to it.

Use, where available:

- hardware/software acoustic echo cancellation;
- known playback-reference audio;
- TTS-origin tagging;
- timing/correlation between generated frames and microphone input;
- suppression of OSCAR's own synthesized voice from Voice Map enrollment/identity updates.

Self-audio suppression must not prevent real user barge-in while OSCAR is speaking.

# Wake word and ambient audio

The default privacy model is **local awareness first**.

Ambient audio should remain on-device for wake/reflex detection, speech-presence detection, authorized Voice Map classification and configured sound events wherever practical.

Raw room audio is not continuously uploaded to a cloud model.

Cloud STT/transcription begins only after a valid trigger or explicitly enabled mode, such as:

- wake/request activation;
- deliberate meeting/call capture;
- an approved Sentry event requiring transcription;
- an explicit always-transcribe mode configured by the user.

Speech presence is not equivalent to permission to retain a transcript.

# Recognition strategy

The speech layer must be provider-abstracted and selected through OSCAR's native routing logic.

Possible implementations may use:

- native/on-device Android recognition for Sunday;
- local wake-word/VAD/speaker processing on capable devices;
- cloud Whisper-class transcription for activated speech;
- alternate STT engines selected by latency, quality, availability and privacy policy.

Exact providers can change; contracts and measured latency/quality matter more than vendor lock-in.

# Voice Match

## Purpose

Voice Match answers primarily: **is this an authorized speaker for this action?**

It provides fast owner/authorized-speaker verification for personal commands and Sentry behavior. It improves convenience and context but is **not cryptographic authentication**.

Voice Match is distinct from Voice Map. A speaker can be recognized perceptually without being authorized to perform personal actions.

## Enrollment

First-run setup should gather samples across:

- multiple phrases;
- normal/quiet/loud delivery;
- close/far microphone distance;
- different room positions;
- realistic background noise;
- desk microphone and Sunday where applicable.

The resulting speaker profile should be tested before enrollment is accepted.

## Runtime decision

```text
speech
  ├─ what was said? ──────► intent / transcript
  └─ who said it? ────────► speaker score
                  \        /
                   policy
                     ↓
               allow / confirm / deny
```

Speaker verification should expose confidence rather than only a boolean.

## Authorization levels

| Level | Typical actions | Voice policy |
|---|---|---|
| 0 — Safety | emergency stop, stop motor, silence dangerous alarm path | should work for anyone nearby where safe |
| 1 — Harmless | time, weather, simple lights/volume | Voice Match optional/configurable |
| 2 — Personal | calendar, notifications, personal memory, PC context | owner/authorized speaker required |
| 3 — Sensitive | messages, important file/app actions, Sentry configuration | strong Voice Match + contextual/explicit confirmation |
| 4 — Critical | financial/security/destructive actions | voice alone insufficient; require biometric/PIN/explicit approval |

The user can tighten these policies, but local emergency stop should fail safe.

# Voice Map

## Purpose

Voice Map answers: **who appears to be speaking around OSCAR?**

It is a perception layer, not an authorization database.

A Voice Map entry may represent:

```text
speaker_profile_id
canonical_person_id (optional)
display label (optional)
embedding/model metadata
confidence history
source devices / acoustic conditions
last observed time
consent / retention policy
enrollment provenance
```

Possible runtime states include:

```text
owner
known_person
recognized_but_unverified
unknown_speaker
multiple_speakers
uncertain
```

## Identity rules

- Unknown voices remain unknown rather than being guessed.
- OSCAR should not silently assign a real-world identity from one weak acoustic match.
- Linking a voice profile to a canonical person should require deliberate enrollment, strong corroborating evidence or user confirmation.
- Speaker recognition confidence is evidence, not truth.
- Voice Map does not grant permissions; Voice Match + permissions + Personal Policy still decide authority.
- OSCAR's own synthesized voice is excluded from Voice Map learning.
- Voice profiles and embeddings are sensitive biometric-like data and require explicit retention/privacy controls.

## Speaker and conversation awareness

Where enabled and technically feasible, Voice Map can provide local events such as:

```text
speech_started
speech_ended
speaker_changed
known_speaker_present
unknown_speaker_present
multiple_speakers_detected
speaker_confidence_changed
```

Full transcription is not required for these events.

Meeting/call diarization may reuse Voice Map signals, but communication-specific speaker labels should remain confidence-qualified.

# Reflex command set

Initial candidates:

- `Oscar`;
- `Mute`;
- `Stop`;
- `Cancel`;
- `Enough`;
- `Listen`;
- `Sentry`;
- `Stand down`.

These commands should have deterministic semantics and should not depend on a frontier model.

# Sentry Mode

## Definition

Sentry Mode is OSCAR's always-on low-power awareness system. It watches local acoustic, sensor, device and presence events, then escalates only meaningful situations.

It is not `stream the room to AI all day`.

```text
microphone / sensors / devices / presence
                  ↓
          local perception plane
     wake • VAD • Voice Map • sound events
                  ↓
            local event engine
                  ↓
        rules + baseline/anomaly check
             /                \
          normal             meaningful
            ↓                    ↓
         ignore/log       policy + escalation
                               ↓
                notify / speak / cloud reason
```

## Acoustic Sentry plane

When Sentry voice awareness is enabled, the microphone front end can remain locally active for low-cost signals such as:

- wake word;
- speech/non-speech presence;
- owner/known/unknown speaker classification;
- speaker changes/multiple-speaker events;
- unusual configured sound classes;
- acoustic activity useful for room/presence state;
- barge-in while OSCAR is speaking.

This local acoustic plane should feed compact events into the Perception Fabric/World Model. It should not continuously retain raw audio or produce cloud transcripts unless policy explicitly permits it.

Sentry must distinguish OSCAR's own playback from external speech.

## Modes

### Passive

- wake word;
- basic hardware health;
- minimal speech/presence awareness;
- self-voice suppression.

### Aware

- normal presence/device/environment monitoring;
- local Voice Map events when enabled;
- low-noise proactive events.

### Guard

- security-oriented sensors/cameras/audio-event classes according to configured permissions;
- unknown-speaker events can carry higher priority;
- higher alert priority.

### Away

- assumes the owner is not present;
- stronger anomaly sensitivity;
- checks configured devices/workbench conditions;
- prioritizes Sunday alerts;
- configured speech/unknown-speaker activity may be treated as relevant evidence.

### Sleep

- quiet interaction behavior;
- wake/reflex/safety/security awareness continues;
- suppress nonurgent speech;
- acoustic processing remains local unless an event requires authorized escalation.

## Events Sentry may monitor

Subject to installed hardware and permissions:

- room entry/motion;
- door/window state;
- device power state;
- workbench power draw;
- temperature/environment changes;
- smoke/gas/water sensors;
- OSCAR node health;
- network/device failures;
- phone/PC arrival or departure;
- unusual sound classifications;
- speech presence;
- known/unknown speaker events from Voice Map;
- multiple-speaker/speaker-change events;
- scheduled conditions.

## Event policy

Every event should carry at least:

```text
importance
urgency
confidence
interruptibility
source
correlation/task ID
```

Voice/speaker events should additionally carry speaker-profile/canonical-person references only when supported by the evidence and retention policy.

Typical outcomes:

- low value → log compact state or discard;
- useful but nonurgent → Sunday notification;
- important while user nearby → speak;
- urgent/safety → interrupt immediately.

## Example

```text
no presence for 45 min
+ workbench device drawing 58 W
+ room light off
+ Sunday indicates user away
        ↓
possible_device_left_on
        ↓
OSCAR may verify with another sensor/camera
        ↓
notify: “The soldering station appears to still be powered. Turn it off?”
```

No frontier model is needed to detect the initial condition.

Another example:

```text
Away mode
+ speech detected in room
+ Voice Map: unknown speaker, high confidence
+ phone confirms owner is away
        ↓
meaningful presence event
        ↓
verify with configured sensor/camera if allowed
        ↓
alert according to Personal Policy
```

## Safety separation

Sentry may decide that something deserves attention, but physical emergency protections remain deterministic:

- thermal cutoffs;
- over-current protection;
- motor/relay interlocks;
- emergency stop;
- battery protection.

Those paths must remain safe if OSCAR Core, native OSCAR transport, cloud intelligence or the Internet is unavailable.
