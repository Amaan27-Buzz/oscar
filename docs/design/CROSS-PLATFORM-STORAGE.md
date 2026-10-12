# Storage inventory — 2026-10-12

Read-only inventory. **No deletion authorized or performed.** Sizes are logical file lengths, not guaranteed allocated/reclaimable bytes. No emulator/qemu process was running at inventory time. Existing worktrees contain unmerged code and evidence; preserve all six Git checkouts.

| Main checkout `.tmp/` directory | GiB | Proposed disposition |
|---|---:|---|
| sunday-avd-ge9ec72i | 13.12 | Candidate disposable API36.1 AVD; preserve until owner approval |
| mobile-avd-y1soh4ru | 12.57 | Candidate disposable API36.1 AVD |
| expression-avd | 10.36 | Candidate disposable API36.1 expression AVD |
| mobile-api35-avd-n18hdpcb | 7.28 | Despite name, config points to API36.1; candidate disposable |
| expression-api35-avd | 3.38 | Keep fallback API35 AVD |
| expression-api35 | 5.12 | Keep reusable API35 image/runtime dependency |
| api35-system-image | 3.50 | Keep until image dependency/hash comparison |
| api35-parts | 1.62 | Download fragments; deletion candidate after owner approval |
| mobile-gradle-cache | 1.17 | Reuse compilation cache |
| voice-env | 0.56 | Preserve voice dependency environment |
| gradle-runtime / gradle-8.13 / gradle-parts | 0.54 | Keep runtime; parts candidate only after dependency check |
| sunday-env | 0.15 | Preserve until dependency check |

Four old API36.1 AVDs total **43.33 GiB logical candidate space**. Fragments add 1.75 GiB. Recoverable disk allocation may differ; snapshots and sparse disks must not be counted twice. Owner authorization must name exact absolute paths before any deletion.

## Reuse plan

Use existing `C:/Users/Amaan/.codex/worktrees/mobile-completion/reference-api35-avd` registered as `oscar_group02_api35`; port5582, one emulator, no snapshot save/load, no wipe. Preserve its userdata and reused system images. Its generated `config.ini` mentions API36.1, so launch metadata and SDK readback must resolve the actual working image before claiming API35.

Preserve `.oscar` voice models and the source checkout's Rust outputs. Reuse desktop-completion Cargo target, mobile Gradle cache, installed SDK/JDK and node modules only after checking versions/paths. This worktree is source-only; do not duplicate multi-gigabyte AVDs or models. Curated PNGs and short motion recordings only; raw native regression outputs remain ignored.

Free space at inventory: C about169.4GiB; D about176.7GiB. Sufficient to continue without cleanup.

## Final reuse verification

The existing `oscar_group02_api35` emulator was launched with the explicit reusable image `D:/TheDawnlightGroup/DawnlightLabs/oscar/.tmp/api35-system-image/x86_64`; native SDK readback was35. Final working launch: port5582, `-no-snapshot -no-window -no-audio -gpu software -feature -Vulkan -memory 2048 -cores 4`. No new AVD, snapshot copy, wipe or cleanup deletion. Initial lower-memory runs produced system ANR dialogs and were excluded from visual evidence. Restarts reused the same existing userdata. Compilation reused desktop-completion Cargo outputs and the original mobile Gradle cache.
