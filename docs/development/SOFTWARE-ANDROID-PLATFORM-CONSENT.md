# Android system consent acceptance

This campaign exercises the production selected-folder picker and Android
MediaProjection consent on disposable API 35 AVD
`oscar_group05_capability_api35`, exact serial `emulator-5582`. It does not access
a physical phone, microphone, camera or owner account.

`NativePlatformConsentTest` renders the existing `NativePlatformSettings`, clicks
actual Android system controls through instrumentation accessibility, and uses
the existing `NativeCapabilities`/`NativePlatform`/`NativeScreenService` adapters.
No document URI permission, MediaProjection consent token or screen frame is
injected. Local selected-app/preferences and an exact adapter authorization
callback are synthetic test fixtures. This is OS and adapter acceptance, separate
from signed Core/Grid task acceptance.

The selected-folder case checks Android's persisted read/write grant, exact tree
identity, provider denial outside that tree, independent document content
readback, traversal rejection, independent local read versus write permission,
and withdrawal of persisted URI access and capability availability. Android may
retain a transient activity-result URI grant until the receiving activity/task
ends; the test does not claim that releasing a persisted permission instantly
removes every transient OS grant.

The screen case declines consent first, then uses Android's app-sharing consent,
requires current exact adapter authority for each transient observation, decodes
a fresh bounded JPEG in memory, rejects cancelled authority, and checks service
withdrawal after explicit stop and actual OS screen-off. Images are not saved.
Neither an OS consent nor the synthetic callback activates a product owner mode.

Run after building the debug app and androidTest APKs:

```powershell
$env:ANDROID_HOME='C:\Users\Amaan\AppData\Local\Android\Sdk'
python -m scripts.software_android_platform_reference
```

The script verifies AVD name, QEMU property, API and boot completion before each
command, restores and reads back prior accessibility settings, uninstalls both
synthetic packages and removes only the newly created exact synthetic document
paths. It aborts rather than reuse an existing acceptance directory.

Status: instrumentation implemented; actual campaign acceptance pending execution.
Physical/OEM behavior and combined signed Grid SAF/MediaProjection acceptance
remain separate obligations.
