# SSM Parameter Store — SupportOS prod

ECS reads app config from **`/supportos/prod/<ENV_VAR>`** (see `cloudformation/services-template.yml`).

## Generate secrets (JWT, Fernet, internal keys)

```bash
# JWT_SECRET_KEY, ADMIN_JWT_SECRET_KEY, API_TOOL_SECRETS_ENCRYPTION_KEY (JSON)
python scripts/ssm/generate_secrets.py

# Same keys + shared INTERNAL_API_KEY / BACKEND_INTERNAL_API_KEY / etc.
python scripts/ssm/generate_secrets.py --include-internal-keys

# .env-style lines instead of JSON
python scripts/ssm/generate_secrets.py --format env
```

Copy the output into `supportos-prod.parameters.json`, then upload.

**One-liners without the script:**

```bash
# Backend JWT (64 hex chars)
python -c "import secrets; print(secrets.token_hex(32))"

# Admin JWT — run again; must differ from backend JWT
python -c "import secrets; print(secrets.token_hex(32))"

# Fernet key for API_TOOL_SECRETS_ENCRYPTION_KEY
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## Quick start

```bash
cp scripts/ssm/supportos-prod.parameters.example.json scripts/ssm/supportos-prod.parameters.json
# Edit supportos-prod.parameters.json — real secrets, Redis endpoint, etc.

# Preview (no AWS writes)
python scripts/ssm/upload_parameters.py \
  --file scripts/ssm/supportos-prod.parameters.json \
  --dry-run

# Upload
python scripts/ssm/upload_parameters.py \
  --file scripts/ssm/supportos-prod.parameters.json

# Verify
aws ssm get-parameters-by-path \
  --region us-east-1 \
  --path /supportos/prod \
  --recursive \
  --query 'Parameters[].Name' \
  --output table
```

## Notes

- **`supportos-prod.parameters.json`** is gitignored — never commit real secrets.
- **`DATABASE_URL`** is already in SSM if you uploaded it earlier; re-upload overwrites with `--overwrite`.
- Use **`--skip-empty`** to upload only keys you have filled in.
- **`APP_ENV`** is not in the ECS template today; set **`CORS_ORIGINS`** explicitly for prod (included in the example JSON).
- **`AI_SERVICE_BASE_URL`**: loopback for web container (`http://127.0.0.1:8000/ai/api/v1`). **`BACKEND_BASE_URL`**: public API URL for the worker service.
