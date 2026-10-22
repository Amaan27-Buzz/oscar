# Native Desktop execution sharing — local software acceptance, 2026-10-21

Preferences now exposes setup, explicit native review, start and stop for the
existing outbound `RemoteMachine`. This reuses the saved DPAPI connection,
nonexportable CNG transport key, canonical Core, execution journal, capabilities
and task approval/standing-authority checks. It creates no second Core or owner.

The owner chooses an existing installed Python executable with OSCAR installed,
an existing absolute local workspace, an exact capability subset, and any host
execution, executable-path and registered-application allowances. Rust checks
these against the actual enrollment and displays the complete local scope in
native owner review. The native runtime independently rejects unavailable
executors and missing grants. Selecting local sharing never activates Secure or
Full Access, and capture/retention are not implied.

The signed invitation's actual workspace identity is saved in the encrypted
connection. Older connections without that binding can still connect but cannot
share execution until explicitly re-enrolled. The artifact directory is distinct
from that identity. Existing local paths are canonicalized consistently; the
Windows verbatim prefix produced by Rust is normalized to the local-drive form
accepted by existing `ScopedFiles`. A shared directory cannot contain the native
configuration, execution journal or isolated browser profiles.

The child starts suspended, joins a kill-on-close Windows Job, and only then has
its own suspended thread resumed. It receives the reviewed scope over stdin
after containment. There is no shell, credential argument, plaintext credential
copy or automatic startup. Bounded status messages report actual runtime state;
invalid status, failed startup and missing installed packages remain unavailable.
Private process output and stderr are not forwarded to either WebView.

Stop closes the local execution grant through the parent pipe and gives the
runtime up to three seconds to cancel and disconnect. The existing action guard
rechecks that grant; the Job then terminates remaining descendants. Disconnect
and forget, app exit and unexpected parent termination also remove the local
executor. Existing durable uncertain-action claims prevent automatic replay.
Closing Workspace to the tray intentionally keeps explicitly started sharing
running; there is no background startup after relaunch.

## Executed checks

- `cargo +1.99.0 test`: 36 passed, one existing opt-in fixture ignored. After
  the final path/containment changes, all seven focused `worker_sharing` tests
  passed, including suspended contained launch, cooperative stop, descendant
  termination, bounded status, exact argv, old-enrollment rejection and scope
  exclusion. Native debug build passed.
- Three `WorkerSharing` UI tests and TypeScript typecheck passed. They cover
  explicit capability selection, separate host consent, command allowlists,
  unavailable enrollment and local stop during Core loss.
- Two Python supervision boundary tests, Ruff and focused mypy passed.
- `python -m scripts.software_desktop_worker_reference` passed the actual native
  supervisor route. It copied the current package into only a disposable
  interpreter's ordinary site-packages, used real synthetic Windows CNG/DPAPI
  enrollment and loopback TLS, submitted a signed Ask file write, checked Core's
  independent readback and separate resulting file bytes, then stopped sharing
  and observed capability withdrawal. Synthetic keys, processes, credentials and
  the disposable interpreter were removed. The host Python installation was not
  modified. [Machine-readable receipt](../evidence/software-completion/desktop-worker-2026-10-21.json).

The fixture bypasses the interactive native consent dialog only through the
existing debug-only synthetic fixture identity boundary. Production starts use
native owner review. Owner visual/dialog acceptance, unrestricted application
interoperability, installed-product distribution of Python/OSCAR, hosted Internet
commissioning and real owner activation remain unverified. The application
requires an explicitly installed current runtime and does not claim to bundle it.
