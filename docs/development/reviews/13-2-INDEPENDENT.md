# 13.2 independent interaction, privacy and lifecycle review

Reviewed 2026-10-11 in the separate Mobile completion worktree. This reviewer
changed no app or test code. **ACCEPT bounded software/reference closure** after
the source-switch and atomic-discard corrections below. Owner/device acceptance
and the separate 13.3 consequential-review obligation remain open.

## Native evidence first

Inspected `13-2-reference-home-response.png` before the implementation summary.
This is actual native Compose rendering connected to an isolated Core reference
service, with a pending arithmetic request; it is not yet Desktop interoperability.
Owner attention, the shared Orb and one relevant task remain dominant. The compact
response exposes deeper reading/inspection and explicit discard without a chat
transcript wall. Pending approval is not presented as execution or verified success.
The state-driven character differs from unavailable presentation. Keyboard comfort,
sustained motion and owner visual judgement are not established by this still.

## Architecture and privacy

Core remains task/context/authority owner. Android keeps bounded transient
readback plus an encrypted unsent form draft, not a conversation archive or a
second reasoning/memory runtime. Android Keystore AES-GCM protects recovery; AAD
binds a draft to the Core origin/node/session. Replacement pairing removes old
draft/pending-discard recovery material. Foreign-source decryption fails closed.
Private content is not placed in `rememberSaveable`/activity state bundles.

Transport operations and vault mutations share the existing mutex. Epoch fences
apply before a request and before readback admission. Foreground loss withdraws
private task/result/approval state; recovery restores the bounded form draft and
pending privacy suppression. Network failure withdraws old private readback and
does not retry an ambiguous mutation. Stop waiting is explicitly local; Core work
may continue. Discard suppresses readback, clears private forms and invokes Core's
scoped discard without implicitly cancelling active work. VERIFIED, REPORTED,
verifying, partial and UNKNOWN labels remain distinct. Full responses wrap/scroll;
bounded Core excerpts retain an omission warning.

## Findings independently challenged and corrected

Initial HOLD: `connect` left the old client in memory while a noncancellable new
vault save could finish after lifecycle epoch change. Resume could therefore use
the old client despite the newly stored source. Corrected by retiring the client
immediately on source change. The native regression starts replacement pairing,
stops during the save and verifies restored binding against the newly stored source.

Initial HOLD: draft removal and pending privacy suppression used separate commits,
and offline discard success appeared before durable persistence. Corrected to one
editor commit for draft/privacy state, with persistence-verifying feedback and Core
discard initiation only after that save. A new CoreSession restores pending
suppression without restoring private draft/readback. Local deletion is not claimed
as remote revocation or physical secure erasure.

## Independent execution

- Fresh `:app:testDebugUnitTest :expression:testDebugUnitTest --rerun-tasks`:
  **12 app + 5 expression tests, zero failures/skips**, all 46 Gradle tasks executed.
- Serial API 35 native targeted run: replacement/interrupted-pairing regression
  **PASS**; draft recreation regression initially **FAILED** because its immediate
  post-recreation assertion observed an empty field during asynchronous restore.
  Failure receipt is `.tmp/reviewer-13-2-native.log`; it is not counted as PASS.
- Unchanged isolated draft regression rerun: **1 test PASS, zero skips**, 14 seconds,
  `.tmp/reviewer-13-2-draft-retry.log`. Add a bounded wait for restored draft before
  the UI assertion so the test follows asynchronous restoration rather than racing it.
- Inspected the actual crypto/source tests and captured semantics. Parent full
  instrumentation/Core results remain separately attributed, not independent runs.

No demonstrated P0/P1 remains in the reviewed 13.2 paths after these corrections.
The intermittent assertion is preserved as a test reliability finding; no data-loss
conclusion is inferred from a transient empty field. The exact approval disclosure,
expiry and biometric callback review belongs to 13.3 and is not waived here.

### Narrow restoration recheck

Inspected the subsequent timing correction: restoration now has explicit loading
state, disables draft editing during encrypted load, and `stop` does not save an
unknown empty draft while that load is in flight. A foreign draft-save binding
raises rather than silently returning persistence success. The native assertion
waits for the restored ViewModel draft before inspecting the field. Parent reports
the corrected two targeted native tests passed with zero skips, JVM 12+5 passed and
serial expression instrumentation 3 passed. These subsequent runs were not launched
by this reviewer; the independent executions and original failure above remain.
This correction addresses both test timing and the real potential for editing an
empty form before recovery completes. Acceptance recommendation is unchanged.

Not checked: physical phone/OEM, actual speech, human biometric/PIN confirmation,
Desktop networking or abrupt OS process-kill recovery. Remaining risk: activity
recreation/new-session recovery evidence is narrower than real process death and
sustained owner use.
