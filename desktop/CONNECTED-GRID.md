# Connected Desktop and Windows Worker

The existing Workspace keeps its design and local `/v1/desktop` reference path.
Preferences now prepares an HTTPS Core connection and shows this installation's
public transport and owner keys. A trusted Core operator creates a short-lived
invitation for those exact keys, the `desktop` role and an explicitly scoped
workspace. Paste the invitation in Preferences; the native Windows confirmation
reviews the Core before enrollment.

The Rust process keeps the persistent transport and owner keys in current-user
Windows CNG. They are not exported. The Core session is encrypted with current-user
DPAPI in the app configuration directory's `connection.dat`; the WebView receives
only public registration details and sanitized projections. This protects saved
credentials for the Windows account; it is not isolation from other programs
already running as that account. HTTPS certificate validation, origin binding,
request proofs, bounded polling, archive generation resets and native review
binding remain enforced. Disconnect revokes the session when reachable and removes
the saved connection and exact installation keys. An unreachable Core leaves
remote revocation explicitly UNKNOWN.

The outbound Worker must be started separately with the same Windows account and
an explicitly chosen existing disposable or authorized workspace. It does not
start an inbound server or replace Core's archive/policy database. For example:

```powershell
python -m oscar.remote_worker --connection "ABSOLUTE_APP_CONFIG\connection.dat" `
  --workspace "ABSOLUTE_AUTHORIZED_WORKSPACE" --workspace-id "ENROLLED_WORKSPACE_ID" `
  --journal "ABSOLUTE_STATE_DIRECTORY\worker-claims.sqlite"
```

The journal must be outside the remotely writable workspace. Only bounded UTF-8
file reads and writes are advertised. Writes require exact Core Ask approval and
local scope/expiry/session checks immediately before replacement. Durable claims
prevent replaying an execution whose post-crash outcome is unknown. Core performs
independent readback before marking a task verified. Other existing typed Windows
capabilities remain local; connected voice, general computer use, Secure and Full
Access are unavailable.

Run the native software acceptance on Windows:

```powershell
cargo +1.99.0 test --manifest-path desktop/src-tauri/Cargo.toml --no-default-features
cargo +1.99.0 build --manifest-path desktop/src-tauri/Cargo.toml --no-default-features
python -m scripts.verify_desktop_grid
```

This starts a real TLS Core and independent Worker against disposable files,
creates actual synthetic CNG identities, reopens DPAPI credentials across native
processes, signs the exact synthetic approval with the native owner key, checks
file effects and Core readback, and observes the same verified task and canonical
conversation through the native adapter. Exact fixture keys/state are removed.
Fixture identity, approval and additional trusted CA entry points exist only in
debug builds and require a `fixture-` installation. Certificate verification stays
enabled. The production Worker PEM mode requires an explicit synthetic fixture.

The 2026-10-18 run was SOFTWARE_VERIFIED on Windows. The automated approval is
synthetic; physical owner confirmation, public Internet/Oracle deployment, real
owner enrollment and physical Android acceptance remain NOT_RUN.
