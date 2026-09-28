# Voice + Sentry

## Voice is a primary interface

OSCAR should support voice natively across desk hardware, Sunday and other connected surfaces. Text remains equally valid and must share the same task/conversation state.

A voice interaction should feel conversational rather than like a smart-speaker request cycle.

## Target interaction loop

```text
microphone
  ↓
local audio front end
  ├─ noise handling / echo cancellation
  ├─ VAD
  └─ wake/reflex detection
  ↓
streaming speech recognition
  ↓
intent/context decision
  ├─ reflex/local execution
  ├─ tool path
  ├─ ChatGPT
  └─ SwitchRoute
  ↓
streamed result
  ↓
chunked natural TTS
  ↓
speaker
```

## Latency rules

- Wake acknowledgement should be effectively immediate.
- Reflex commands should stay local.
- Begin speaking as soon as a useful first chunk exists; do not wait for a full paragraph.
- Deep jobs may take time, but OSCAR should acknowledge immediately and work asynchronously.
- Instrument end-to-end latency from audio onset to action/first audio.

## Barge-in

Barge-in is mandatory.

If OSCAR is speaking and the user says “mute”, “stop”, “no”, “not that”, or begins a new request, current TTS should stop immediately and the input should become authoritative.

The voice stack therefore needs:

- cancellable TTS
- active utterance/task IDs
- VAD while TTS is active
- echo cancellation so OSCAR does not transcribe itself
- clear interruption semantics

## Wake word and ambient audio

The default privacy model is **local awareness first**.

Ambient audio should remain on-device for wake/reflex detection wherever practical. Audio is sent to cloud STT only after activation or another explicitly enabled event.

OSCAR should not require a permanent raw microphone stream to a cloud model.

## Recognition strategy

The speech layer must be provider-abstracted.

Possible implementations may use:

- on-device/native Android recognition for Sunday
- local wake-word/VAD on ESP32-class hardware
- high-quality cloud Whisper-class transcription for activated speech
- fallback providers via SwitchRoute/voice routing

Exact providers can change; contracts and latency/quality tests matter more than vendor lock-in.

## TTS strategy

Requirements:

- natural voice quality
- low first-audio latency
- streaming/chunking support
- interruption support
- stable OSCAR voice identity
- pronunciation controls where needed
- provider abstraction

OSCAR's voice should sound natural and understated, not theatrical by default.

# Voice Match

## Purpose

Voice Match provides fast owner recognition for Sentry Mode and personal commands. It improves convenience and context but is **not cryptographic authentication**.

## Enrollment

First-run setup should gather samples across:

- multiple phrases
- normal/quiet/loud delivery
- close/far microphone distance
- different room positions
- realistic background noise
- desk microphone and Sunday where applicable

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
| 1 — Harmless | time, weather, simple lights/volume | voice match optional/configurable |
| 2 — Personal | calendar, notifications, personal memory, PC context | owner/authorized speaker required |
| 3 — Sensitive | messages, important file/app actions, Sentry configuration | strong voice match + contextual/explicit confirmation |
| 4 — Critical | financial/security/destructive actions | voice alone insufficient; require biometric/PIN/explicit approval |

The user can tighten these policies, but local emergency stop should fail safe.

## Reflex command set

Initial candidates:

- `Oscar`
- `Mute`
- `Stop`
- `Cancel`
- `Enough`
- `Listen`
- `Sentry`
- `Stand down`

These commands should have deterministic semantics and should not depend on a frontier model.

# Sentry Mode

## Definition

Sentry Mode is OSCAR's always-on low-power awareness system. It watches local events and state, then escalates only meaningful situations.

It is not “stream the room to AI all day.”

```text
sensors / wake audio / devices / presence
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

## Modes

### Passive

- wake word
- basic hardware health
- minimal presence awareness

### Aware

- normal presence/device/environment monitoring
- low-noise proactive events

### Guard

- security-oriented sensors/cameras according to configured permissions
- higher alert priority

### Away

- assumes the owner is not present
- stronger anomaly sensitivity
- checks configured devices/workbench conditions
- prioritizes Sunday alerts

### Sleep

- quiet interaction behavior
- safety/security continues
- suppress nonurgent speech

## Events Sentry may monitor

Subject to installed hardware and permissions:

- room entry/motion
- door/window state
- device power state
- workbench power draw
- temperature/environment changes
- smoke/gas/water sensors
- OSCAR node health
- network/device failures
- phone/PC arrival or departure
- unusual sound classifications
- known/unknown speaker events
- scheduled conditions

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

Typical outcomes:

- low value → log silently
- useful but nonurgent → Sunday notification
- important while user nearby → speak
- urgent/safety → interrupt immediately

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

## Safety separation

Sentry may *decide that something deserves attention*, but physical emergency protections remain deterministic:

- thermal cutoffs
- over-current protection
- motor/relay interlocks
- emergency stop
- battery protection

Those paths must remain safe if OSCAR Core, Latch, ChatGPT or the Internet is unavailable.
