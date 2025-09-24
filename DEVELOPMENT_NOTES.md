# Development Notes

Internal engineering reference outlining architecture, data flows, and future considerations for the Discord File Splitter Bot.

---

## 1. High-Level Architecture

Component | Responsibility | Notes
---------|----------------|------
Command Interface | Parses user commands (split, upload, status, cancel) | Likely Discord slash commands or prefixed text commands.
Chunking Engine | Splits large source files into bounded-size chunks | Enforces configured chunk size; last chunk may be smaller.
Transfer Orchestrator | Coordinates the lifecycle of an active transfer | Updates runtime progress state, schedules chunk uploads.
Uploader / Transport Layer | Sends chunks to Discord (or alternate destination) | Observes Discord file size limits (current hard cap per file).
Runtime Progress Store | Maintains `transfer_progress.json` ephemeral state | Format documented in `TRANSFER_PROGRESS_FORMAT.md`.
Integrity Layer (future) | Validates chunk integrity & final assembly | Hashing strategies, retry logic.
Resume / Recovery Module (future) | Restarts interrupted transfers | Depends on expanded runtime schema (chunk attempts, etc.).
Metrics / Logging (optional) | Diagnostics, throughput metrics | Could emit structured logs (JSON) or simple console output.

---

## 2. Data & State Flows (Current Baseline)

1. User invokes a transfer command with a file reference.
2. File metadata (size, name) is captured.
3. Chunking Engine calculates:
   - `chunk_size_bytes`
   - `total_chunks`
   - Derived chunk boundaries.
4. A new transfer object is appended to `active_transfers` in `transfer_progress.json`.
5. For each chunk:
   - Extract slice / in-memory buffer.
   - Upload via Discord API (or placeholder).
   - On success: append chunk index to `completed_chunks`, update `updated_at`.
6. When all indices are present:
   - Optionally verify (future hashing).
   - Set `status = complete`.
7. Cleanup or retention strategy applied (remove or archive object).

Failure: If any chunk hard-fails, mark `status = error` and preserve diagnostic notes.

Cancel: User-driven cancel sets `status = cancelled` and halts further dispatch.

---

## 3. Chunking Strategy

Current assumptions:
- Fixed chunk size (e.g. 8 MB) chosen under Discord’s per-file upload ceiling (give margin for overhead).
- Simple sequential upload; no concurrency required initially.
- No per-chunk hashing yet (keeps overhead low).

Potential upgrades:
- Adaptive chunking: shrink remaining chunk sizes to align with residual bandwidth or rate limits.
- Parallel dispatch with bounded worker pool (risk: ordering / rate limit management).
- Streamed hashing: compute full-file hash while splitting to avoid double I/O.

---

## 4. Transfer Progress Runtime (Tie-In)

Refer to `TRANSFER_PROGRESS_FORMAT.md` for schema details.

Write policy (recommended):
- Load file -> mutate in-memory -> write temp -> atomic rename.
- Reject stale write if on-disk `updated_at` is newer than in-memory (prevents lost updates under eventual concurrency).

Locking (future):
- Simple advisory lock file `transfer_progress.lock` during mutation OR per-transfer lock segments.

---

## 5. Error Handling Patterns

Category | Example | Strategy
--------|---------|---------
Transient HTTP | Rate limit (429) | Exponential backoff + retry; do NOT mark chunk complete.
Payload Too Large | Discord rejects chunk | Reduce `chunk_size_bytes` future default; abort transfer with `error`.
IO Error (Read) | File read interrupted | Attempt re-read; if persistent -> `error`.
Integrity Mismatch (future) | Chunk hash mismatch | Requeue chunk, increment attempt counter; escalate after threshold.

Recommended addition (future):
```
"chunk_attempts": { "0": 1, "1": 3 }
```
for diagnosing flakiness hot spots.

---

## 6. Logging Guidance

Log Level | Emit When | Sample
----------|-----------|-------
INFO | Transfer start / completion | transfer_started id=upload_123 size=104857600
DEBUG | Per-chunk success | chunk_ok id=upload_123 idx=5 latency_ms=420
WARN | Retry/backoff | chunk_retry id=upload_123 idx=5 attempt=2 reason=rate_limit
ERROR | Terminal failure | transfer_error id=upload_123 reason=discord_reject status_code=400

Structured logging (JSON lines) future example:
```
{"ts":"2025-09-24T10:20:01Z","level":"debug","event":"chunk_ok","transfer_id":"upload_123","chunk":5,"ms":420}
```

---

## 7. Configuration Surface (Proposed)

Config Key | Purpose | Default
-----------|---------|--------
`DEFAULT_CHUNK_SIZE_BYTES` | Base chunk size | 8_000_000
`MAX_PARALLEL_UPLOADS` | Concurrency limit (future) | 1
`RETRY_LIMIT_PER_CHUNK` | Hard retry ceiling | 5
`RETRY_BACKOFF_BASE_MS` | Exponential base | 500
`PROGRESS_FILE_PATH` | Runtime state path | ./transfer_progress.json
`HASH_ALGO` (future) | Integrity algorithm | sha256

---

## 8. Future Enhancements Backlog

Priority (H/M/L) | Idea | Notes
-----------------|------|------
H | Resume incomplete transfers | Requires chunk presence validation + re-dispatch of missing indices.
H | Robust rate limit handling | Inspect Discord headers for remaining quota.
M | Per-chunk hashing | Enables early corruption detection.
M | Parallel uploads | Throughput boost; must respect API constraints.
M | Metrics export (Prometheus) | Optional observability.
L | Encryption at rest for temp chunks | If handling sensitive user data.
L | CLI wrapper | Local non-Discord testing harness.
L | Web dashboard | Visual progress & control.

---

## 9. Testing Strategy

Test Type | Focus
---------|------
Unit: Chunk boundaries | Off-by-one errors at file tail.
Unit: Progress writer | Atomicity, schema integrity.
Unit: Status transitions | Valid vs invalid state transitions.
Integration: Full transfer | End-to-end simulated upload (stub Discord).
Stress: Large file | Memory footprint and throughput.
Chaos (future) | Inject network timeouts to validate retry logic.

Suggested fixture generator: create synthetic binary blobs with deterministic pattern (repeatable pseudo-random seeded bytes) for hashing tests later.

---

## 10. Security & Privacy Considerations

Aspect | Note
-------|-----
Token Handling | Keep Discord token out of repo (.env + .gitignore).
Temporary Chunks | Ensure they are deleted post-success (avoid disk bloat).
Logging | Avoid logging entire filenames if sensitive; truncate or hash optional.
Integrity Data | Hashes optional now—avoid false sense of guarantees until implemented.

---

## 11. Performance Notes

Current sequential model is IO + network bound; CPU minimal.

Potential bottlenecks:
- Large memory mapping if entire file loaded at once (avoid; stream slices instead).
- Repeated open/close operations (batch reading can help).
- JSON rewrite cost when many transfers (if list grows) — consider switching to per-transfer JSON files or lightweight DB if scaling.

---

## 12. Migration & Schema Evolution

When adding fields:
1. Add field (optional parsing).
2. Default gracefully when missing.
3. Document in `TRANSFER_PROGRESS_FORMAT.md`.
4. Only bump `schema_version` if removal/rename occurs.

Provide an upgrade helper if a breaking change is ever introduced (one-shot script to transform old schema).

---

## 13. Developer Workflow Notes

Typical loop:
1. Add feature behind small helper.
2. Write / update unit tests (if testing harness established).
3. Run lint / format.
4. Manual test: small file, large file, induced error (e.g. force chunk failure).
5. Commit with conventional message (see CONTRIBUTING.md — pending).

---

## 14. Open Questions (Track & Resolve Later)

Question | Rationale
---------|----------
Should we persist historical completed transfers? | Impacts file size & privacy.
Do we need encryption for temp chunk storage? | Depends on user data sensitivity.
Parallel vs sequential upload baseline? | Impacts complexity + rate limit risk.
How to surface progress to user (percent, ETA)? | Needs timing metrics per chunk.

---

End of file.