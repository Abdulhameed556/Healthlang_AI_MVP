# POST /api/v1/knowledge-base/{kb_id}/entries/{entry_id}/confirm-upload

## URL

**Path:** `/api/v1/knowledge-base/{kb_id}/entries/{entry_id}/confirm-upload`

**Full URL:** `<base>/api/v1/knowledge-base/{kb_id}/entries/{entry_id}/confirm-upload`

| Environment | Example full URL |
|-------------|------------------|
| Local | `http://localhost:8000/api/v1/knowledge-base/{kb_id}/entries/{entry_id}/confirm-upload` |

**See also:** [knowledge_bases README](README.md) · [generate-upload-url.md](generate-upload-url.md)

## Summary

Step 2 of the two-step upload flow. Call this immediately after the frontend has successfully PUT the file to the presigned S3 URL. The backend verifies the file exists in S3, then enqueues it for async processing (parse → chunk → embed → store in Pinecone). Returns immediately with `indexing_status: "processing"` — indexing happens in the background.

## Auth

```http
Authorization: Bearer <access_token>
```

| Role | Can call |
|------|----------|
| `super_admin` | yes |
| `admin` | yes |
| `read_only` | yes |

## Path parameters

| Parameter | Type | Notes |
|-----------|------|-------|
| `kb_id` | UUID | Knowledge base that owns the entry. |
| `entry_id` | UUID | The `entry_id` returned by [generate-upload-url.md](generate-upload-url.md). |

## Request body

None. No body required.

## Success (200)

```json
{
  "message": "File confirmed and queued for indexing",
  "status_code": 200,
  "error": false,
  "data": {
    "entry_id": "22222222-2222-2222-2222-222222222222",
    "indexing_status": "processing"
  }
}
```

| Field | Notes |
|-------|-------|
| `entry_id` | Matches the `entry_id` you passed in the URL. |
| `indexing_status` | Always `"processing"` at this point. Poll or use webhooks to track completion. |

## Errors

| Status | When |
|--------|------|
| 401 | Missing or invalid JWT |
| 404 | `entry_id` not found or does not belong to `kb_id` |
| 422 | File has not been uploaded to S3 yet (the presigned PUT has not been made) |

## Frontend notes

- Call this only after the S3 PUT returns `200`. If S3 returns an error, do not call this endpoint.
- On success, show the user a "Processing…" state for the entry. Poll the entry status or use a websocket update to detect when `indexing_status` becomes `indexed` or `failed`.
- A `422` here means the frontend called confirm before the S3 upload finished, or the upload failed silently. Retry after confirming the S3 PUT succeeded.

## Code

- Endpoint: `src/presentation/api/v1/knowledge_base/endpoints/confirm_upload.py`
- Use-case: `src/application/knowledge_base/use_cases/confirm_upload.py`
- S3 check: `src/infrastructure/storage/s3.py` → `object_exists()`
