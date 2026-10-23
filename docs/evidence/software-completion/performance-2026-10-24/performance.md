# Local performance acceptance

| Operation | Samples | Baseline p50 / p95 ms | Candidate p50 / p95 ms |
| --- | ---: | ---: | ---: |
| arithmetic | 80 | 12.621 / 16.3876 | 12.7356 / 15.7383 |
| file | 80 | 22.1797 / 29.0794 | 22.0191 / 29.4625 |
| loopback_http | 80 | 94.8611 / 128.7542 | 97.3511 / 136.696 |
| reviewed_executive_goal | 80 | 22.2045 / 25.8365 | 21.6267 / 28.7237 |

![Ordered samples](performance.png)

Real disposable local SQLite/files/loopback; three warm-ups per operation. SQL trace enabled equally; no tracemalloc. Separate fresh processes, alternating revision order, authorized local Grid source with normal vs stopped background services. Cold samples are Harness startup/first task, not OS cold cache. RSS is Windows working set, not all-system memory/battery. Laptop cache/load and thermal state uncontrolled. Baseline extraction includes only runtime/config to reduce unrelated asset I/O. No model/provider/device performance claim.

Candidate source hashes in JSON identify the measured working tree. The candidate HEAD alone does not identify uncommitted source. No Internet, real account, device battery, room audio or sustained-use claim.
