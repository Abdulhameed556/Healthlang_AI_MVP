# POST /api/v1/knowledge-base/{kb_id}/entries/upload-url

## URL

**Path:** `/api/v1/knowledge-base/{kb_id}/entries/upload-url`

**Full URL:** `<base>/api/v1/knowledge-base/{kb_id}/entries/upload-url`

| Environment | Example full URL |
|-------------|------------------|
| Local | `http://localhost:8000/api/v1/knowledge-base/{kb_id}/entries/upload-url` |

**See also:** [knowledge_bases README](README.md) · [confirm-upload.md](confirm-upload.md)

## Summary

Step 1 of the two-step upload flow. Creates a `knowledge_base_entry` row in the database (status `processing`) and returns a short-lived presigned S3 PUT URL. The frontend uploads the file directly to S3 using that URL — no file bytes pass through the backend. After the upload, call [confirm-upload.md](confirm-upload.md) to verify the file landed and trigger indexing.

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
| `kb_id` | UUID | Knowledge base the entry will belong to. Must be owned by the caller's organization. |

## Request body

`Content-Type: application/json`

```json
{
  "file_name": "employee-handbook.docx",
  "file_type": "docx"
}
```

| Field | Required | Notes |
|-------|----------|-------|
| `file_name` | yes | Display name shown in the UI. Any non-empty string. |
| `file_type` | yes | `docx` \| `md` \| `txt` — PDF is not supported. |

## Success (201)

```json
{
  "message": "Upload URL generated",
  "status_code": 201,
  "error": false,
  "data": {
    "entry_id": "22222222-2222-2222-2222-222222222222",
    "upload_url": "https://s3.amazonaws.com/my-bucket/knowledge-bases/...?X-Amz-Signature=...",
    "expires_in": 900
  }
}
```

| Field | Notes |
|-------|-------|
| `entry_id` | Save this — you need it to call confirm-upload. |
| `upload_url` | Presigned S3 PUT URL. Valid for `expires_in` seconds (15 minutes). |
| `expires_in` | Seconds until the URL expires (always `900`). |

### How to use the presigned URL

```http
PUT <upload_url>
Content-Type: <mime-type matching file_type>
Content-Length: <file size in bytes>

<raw file bytes>
```

| `file_type` | `Content-Type` to send |
|-------------|------------------------|
| `docx` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `md` | `text/markdown` |
| `txt` | `text/plain` |

S3 returns `200 OK` with an empty body on success.

## Errors

| Status | When |
|--------|------|
| 401 | Missing or invalid JWT |
| 404 | `kb_id` does not exist in the caller's organization |
| 422 | `file_type` is not `docx`, `md`, or `txt`; or `file_name` is missing |

## Frontend notes

- Enforce the **15 MB** file size limit before calling this endpoint. The backend does not check.
- Store `entry_id` from the response — you need it for the confirm step.
- After the S3 PUT succeeds, immediately call [confirm-upload.md](confirm-upload.md).
- If the presigned URL expires (15 min), call this endpoint again to get a fresh one; the orphaned DB row can be cleaned up by a background job later.

## Code

- Endpoint: `src/presentation/api/v1/knowledge_base/endpoints/upload_url.py`
- Use-case: `src/application/knowledge_base/use_cases/create_upload_url.py`
- S3: `src/infrastructure/storage/s3.py`
