# Local derived-memory acceptance — 2026-10-22

The current working tree passed the existing real-index verifier's **12 checks**
and the existing synthetic **A–R evaluation's 18 cases** in 26.109 seconds.
The [source-hashed receipt](../evidence/software-completion/memory-indexes-2026-10-22.json)
records the 26 imported source/harness hashes, pinned dependencies, model
fingerprints, exact fixture results and setup limitations. This receipt covers
those source hashes, including uncommitted files; it does not certify every file
at the recorded Git HEAD or promote a formal gate.

Actual Qdrant local dense/sparse hybrid retrieval and Graphiti hybrid search
against Neo4j Community exercised canonical provenance, current/historical
correction intervals, relationship isolation, unrelated-node preservation,
foreign-relationship rebuild refusal, independent Neo4j source/validity readback,
archive/index reopen, injected model outages, deleted-index fallback/rebuild and
forget propagation. The A–R cases additionally exercise alias ambiguity, project
scope, live evidence outranking recall and an expected-memory miss. Five positive
queries had 100% combined/dense top-five recall; lexical recall was 80%. Six
unsupported claims had zero accepted claims. These are small synthetic fixture
measurements, with no general accuracy guarantee.

The existing Python 3.12.10 environment supplied Qdrant 1.19.1, Graphiti 0.30.2,
FastEmbed 0.8.1, ONNX Runtime 1.30.0 and Neo4j driver 6.3.1. Existing dense and
reranker artifacts loaded offline and all model inference ran on local CPU.
The pinned BM25 SDK rejects its legitimately downloaded snapshot in offline mode
because its cache validation requests absent `mock.file` and `tamil.txt` files.
The exercised production constructor therefore made public artifact metadata
requests; its 18 actual files and hashes are recorded. No replacement cache files
were fabricated and no dependency was installed.

Neo4j 2026.09.0 used the existing cached image, a 1 GiB / 2 CPU container and only
`127.0.0.1:17687` publication. Anonymous usage reporting and fleet discovery were
disabled in the accepted run. Its unauthenticated database contained synthetic
records only. The named container and anonymous volumes were removed, with
absence independently checked; ignored synthetic fixture records remain as local
evidence. No production archive, owner credentials or historical receipt changed.

This verifies local derived-index composition. A network Qdrant server, hosted
resource fit, private owner data, secure disk erasure and owner commissioning were
not exercised. Canonical SQLite remains authoritative; derived indexes grant no
retention, recall or action authority.
