# Transfer Progress Runtime Format

This document describes the ephemeral JSON state file used at runtime to track multi-chunk file uploads/splits.  
The real live state file (`transfer_progress.json`) is **not tracked** by Git; only the template `transfer_progress.example.json` is versioned.

## Purpose

- Allow resumable / inspectable progress for long-running chunked transfers.
- Persist minimal state between process restarts (if you later choose to).
- Provide a stable structure for future tooling (e.g. a resume command, integrity verifier).

## File Location

Currently expected at repository root (alongside the bot code).  
You may later relocate it (e.g. to a `runtime/` or `state/` directory); if so, update any path references in code.

## Top-Level Structure

```json
{
  "schema_version": 1,
  "active_transfers": []
}
```

Field | Type | Required | Description
------|------|----------|------------
`schema_version` | integer | yes | Increment when you make a breaking structural change.
`active_transfers` | array | yes | Zero or more transfer objects (see below).

## Transfer Object

Example (expanded):

```jsonc
{
  "id": "upload_123456789012345678",
  "original_filename": "big_archive.zip",
  "total_size_bytes": 104857600,
  "chunk_size_bytes": 8000000,
  "total_chunks": 14,
  "completed_chunks": [0,1,2],
  "status": "in_progress",              // in_progress | complete | cancelled | error
  "started_at": "2025-09-24T10:12:00Z",
  "updated_at": "2025-09-24T10:13:42Z",
  "hash": {
    "algo": "sha256",
    "value": "optional-full-file-hash"
  },
  "notes": "Optional free-form field"
}
```

Field | Type | Required | Description
------|------|----------|------------
`id` | string | yes | Unique identifier for the transfer (could be a snowflake, UUID, or synthetic).
`original_filename` | string | yes | Source file name before splitting/upload.
`total_size_bytes` | integer | yes | Size of the original file in bytes.
`chunk_size_bytes` | integer | yes | Target chunk size in bytes (actual last chunk may be smaller).
`total_chunks` | integer | yes | Computed total number of chunks.
`completed_chunks` | int[] | yes | Zero-based chunk indices that have been fully processed.
`status` | string | yes | One of: `in_progress`, `complete`, `cancelled`, `error`.
`started_at` | RFC 3339 string | yes | ISO timestamp when tracking began.
`updated_at` | RFC 3339 string | yes | Last mutation time.
`hash.algo` | string | no | Algorithm name (e.g. `sha256`, `md5`, `blake3`).
`hash.value` | string | no | Full-file hash or future aggregate; optional until integrity verification is implemented.
`notes` | string | no | Free-form developer or runtime annotations.

### Status Lifecycle

Status | Allowed Previous States | Typical Transition Trigger
-------|-------------------------|----------------------------
`in_progress` | (initial) | Transfer begins; chunks dispatching.
`complete` | `in_progress` | All chunks acknowledged & (optionally) final validation passes.
`cancelled` | `in_progress` | User or system abort.
`error` | `in_progress` | Irrecoverable failure (e.g. hash mismatch, remote API rejection).

(You may later permit `error -> in_progress` if you add robust retry/resume.)

### Integrity Considerations (Future)

Planned / optional enhancements:
- Per-chunk hash list: `chunk_hashes: [{index, algo, value}]`
- Redundant total hash: compare pre/post recombination.
- `validated_at` timestamp once final assembly succeeds.
- `encryption`: `{ enabled: true, method: "aes-256-gcm", key_id: "k1" }`

### Concurrency & Atomicity (Future Note)

If you later allow concurrent processes:
- Write to a temp file then atomic rename (`transfer_progress.json.tmp` → `transfer_progress.json`).
- Maintain a monotonic `updated_at` to detect stale writes.
- Consider using a per-transfer sub-document lock or migrating to a lightweight embedded DB.

### Truncation & Cleanup

When `status = complete|cancelled|error`:
- Either remove the object from `active_transfers` (lean)  
  OR keep it for a short retention window (audit/troubleshooting) with an added `finished_at`.

If you keep history, consider a top-level key:
```json
{
  "schema_version": 1,
  "active_transfers": [],
  "recent_transfers": []
}
```

### Schema Versioning Strategy

Increment `schema_version` only for breaking changes (rename/remove field).  
Additive (backwards compatible) fields do NOT require a bump, but document them here.

### Minimal Valid Entry

```json
{
  "id": "upload_X",
  "original_filename": "file.bin",
  "total_size_bytes": 12345,
  "chunk_size_bytes": 8000000,
  "total_chunks": 2,
  "completed_chunks": [],
  "status": "in_progress",
  "started_at": "2025-09-24T10:00:00Z",
  "updated_at": "2025-09-24T10:00:00Z"
}
```

### Error Handling Patterns (Suggested)

Scenario | Action
---------|-------
Chunk failure (retryable) | Do NOT append index to `completed_chunks`; log attempt count elsewhere (future `chunk_attempts` map).
Final hash mismatch | Set `status = error`, add `notes` describing mismatch, optionally include `expected_hash` & `computed_hash`.
User abort | Set `status = cancelled`, optionally prune partially uploaded chunks remotely.

### Extension Ideas (Backlog)

- `bandwidth_bytes_per_sec` rolling average
- `last_chunk_duration_ms`
- `partial_path` for staging chunk storage
- `resume_token` for remote service continuity
- `priority` for scheduling multiple transfers

---

End of file.