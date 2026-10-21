# Current context and day briefing — local software evidence

2026-10-21, `codex/software-completion`. This extends the existing World Runtime,
Perception Fabric, Sentry and Connector Fabric. It introduces no second Core or
history store and grants no calendar mutation authority.

## Connected implementation

- Native signed Assistance `source_create` configures a Core clock (explicit
  installed IANA timezone) or one existing connected Google/Microsoft calendar
  account at its exact generation. Review includes selected fields, service,
  capability, rolling time window, interval, freshness and independent retention.
- Desktop Preferences adds source authoring, existing source grants/Sentry
  selection and an explicit refresh of a read-only day briefing. Calendar polling
  requires both the source perception grant and selected active awareness.
  Clock polling is an explicitly granted internal source, like Grid/task state.
- Calendar acquisition reuses official connector manifests, vault resolution,
  endpoint validation, bounded HTTP and credential redaction. Only account-bound
  read-only GET capabilities are admitted. Personal Policy, account generation,
  service scope, source epoch and awareness generation are checked around I/O.
- Google reads a selected calendar; Microsoft's existing adapter supports the
  primary calendar. The request covers a rolling 24-hour window in the native
  form (Core contract permits 5 minutes through 7 days), with at most eight
  events. The projection selects identity/title/start/end/cancellation fields;
  pagination is explicitly incomplete. Oversized observations become unavailable.
- Payloads remain transient unless source retention is separately granted.
  Retained selected observations use the canonical Event Archive and expiry.
  A source read does not create a task, Action, mutation grant or retained raw
  provider response.
- `WorldRuntime.brief()` returns at most eight source reports with epistemic
  labels, evidence/observation/freshness, source epoch, account generation and
  explicit omissions. Only current timed calendar events enter bounded overlap
  detection. Missing timezone, all-day dates, expired/disconnected sources and
  missing pages prevent a claim of complete coverage or free time.
- The `world:read` native query is separate from source metadata. Desktop labels
  it as an observed report, hides content after freshness expiry, account changes
  or perception/epoch revocation, and requires explicit refresh. It cannot act or
  send an interruption. Core/native query routing is integrated by the parent
  software-completion change.
- Source grant changes atomically advance both source and polling epochs; this
  fixes polling remaining permanently blocked after a legitimate grant change.
  Signed source reviews use stable contracts rather than changing lease counters.
  Store transactions and epoch fences allow revocation during acquisition without
  waiting for a network operation or inverting World/Store lock order.

## Local verification

- `python -m unittest tests.test_ambient tests.test_world_runtime
  tests.test_connectors tests.test_assistance -q`: **82 passed** in the focused
  run; log `.oscar/software-ambient-checks.log`. All 13 ambient checks passed, including selected-field retention and expiry.
- Ambient checks cover actual Core World integration with synthetic provider
  responses, selected fields/no durable payload, explicit timezone, awareness off,
  account generation change before next poll, revoke during I/O, read Policy,
  provider loss, pagination, payload bounds, Microsoft primary scope, provenance,
  conflict detection, stale reports, grant re-enable and mutation rejection.
- Desktop `OperatingSettings.test.tsx` plus existing `Assistance.test.tsx`:
  **12 passed**. Source creation grants no retention/action by default; no account
  means no calendar activation; stale/revoked briefing data is hidden.
- TypeScript typecheck, Ruff and strict mypy for ambient/World/Connector modules
  passed. These are local synthetic software receipts, not provider commissioning
  or owner/native visual acceptance.

## Remaining executable/acceptance boundaries

No real account or provider was enrolled. Weather, native Android notification,
location/media and communication context still need live authorized Core source
adapters; no source is advertised for them here. A calendar overlap report does
not implement automatic schedule replanning, communication delivery or action
verification. Android source authoring/briefing presentation is tracked with the
parent native integration. Real-provider recurrence/timezone/OEM behavior,
sustained personal use and owner visual acceptance remain unverified.
