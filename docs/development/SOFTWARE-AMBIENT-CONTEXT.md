# Current context and day briefing — local software evidence

2026-10-21, `codex/software-completion`. This extends the existing World Runtime,
Perception Fabric, Sentry and Connector Fabric. It introduces no second Core or
history store and grants no calendar mutation authority.

## Connected implementation

- Native signed Assistance `source_create` configures a Core clock (explicit
  installed IANA timezone), explicit MET Norway weather coordinates, or one
  connected Google/Microsoft calendar account at its exact generation. Review includes selected fields, service,
  capability, rolling time window, interval, freshness and independent retention.
- Desktop Preferences adds source authoring, existing source grants/Sentry
  selection and an explicit refresh of a read-only day briefing. Calendar and weather polling
  require both the source perception grant and selected active awareness.
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

## Weather source — public provider read and local software checks

The signed source contract accepts exactly the common native source fields plus
`latitude`, `longitude` and `place`. Coordinates must be finite, within geographic
bounds, and have at most four decimal places. Desktop Preferences submits these
explicit fields for native owner review; no account or device location grant is
created. Review identifies the fixed MET Norway compact HTTPS endpoint and that
MET Norway receives the selected coordinates and Core network address.

The stdlib HTTPS reader uses the canonical project URL in its User-Agent,
rejects redirects, sends no credential and bounds both compressed/decoded JSON
at 256 KiB. It supports gzip, conditional Last-Modified reads, provider Expires
and Retry-After. Read timeouts and a monotonic response deadline bound a slow
response; inherited proxy and CA trust remain in force. No URL is accepted from
source input. At least ten minutes separate provider attempts, or longer when
provider expiry/throttling requires it. Failed, malformed, expired and out-of-range
reports withdraw the current state rather than preserving an old current claim.

The in-memory cache keeps only selected forecast fields and original acquisition
provenance. Core rechecks cached source authority every 30 seconds with a bounded
60-second source lease; cache use never advances the HTTP observation timestamp.
A successful HTTP 304 is an explicit provider revalidation. Evidence expires at
the earlier of provider expiry, one hour since acquisition/revalidation, or the
selected forecast hour end. Provider update time, forecast time and observation
time remain separate. There is no claim of local measurement or severe-weather
alert coverage. The projection includes temperature Celsius, wind m/s, humidity,
place/coordinates, MET Norway credit and CC BY 4.0 attribution. The brief and
Desktop hide expired or revoked values using Core time.

Perception, retention and action remain separate. Sentry source selection and
Personal Policy are checked before acquisition and after I/O; a revoked response
cannot enter current state. Retention defaults off. Selected retained fields use
the existing canonical archive and configured expiry; no second memory or raw
provider payload is persisted. Calendar account changes have no authority over
this independent public weather source.

Official contracts consulted: [MET Terms of Service](https://docs.api.met.no/doc/TermsOfService.html),
[forecast format](https://docs.api.met.no/doc/ForecastJSON.html) and
[Locationforecast](https://api.met.no/weatherapi/locationforecast/2.0/documentation).
The implementation deliberately fails closed on redirects instead of accepting
another destination.

Verification: **90 tests passed** (25.382 seconds);
`.oscar/software-weather-checks.log` covers the ambient, World
Runtime/Model and Assistance suites, including signed source material, invalid
coordinates/extra URL/account fields, no account dependence, explicit awareness,
policy denial, revoke during I/O, selected retention/expiry, provider loss,
stale/future timestamps, units, malformed data, cache provenance, 304, expiry,
throttle, gzip/bounds, redirect rejection and slow-response deadline. Desktop's
seven OperatingSettings checks and TypeScript typecheck pass. The public-provider
reference `python -m scripts.software_weather_reference` makes one explicit
read for a fixed public city through the actual Harness/World/Sentry/HTTPS path
and writes `docs/evidence/software-completion/weather-2026-10-21.json`, including
source hashes and zero retained archive events. Avoid re-running before the
provider expiry recorded in its receipt. On this host the Python OpenSSL trust
store lacked the required chain; supplying the already installed certifi CA
bundle through `SSL_CERT_FILE` verified TLS without disabling validation or
adding a product dependency. Deployment must provide working trusted CA roots.
This is public-provider read evidence, not personal location, owner activation,
real account or physical acceptance.

## Remaining executable/acceptance boundaries

No real account was enrolled. Native Android notification,
location/media and communication context still need live authorized Core source
adapters; no source is advertised for those inputs here. A calendar overlap report does
not implement automatic schedule replanning, communication delivery or action
verification. Android source authoring/briefing presentation is tracked with the
parent native integration. Real-provider recurrence/timezone/OEM behavior,
sustained personal use and owner visual acceptance remain unverified.
