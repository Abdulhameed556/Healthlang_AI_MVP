# POST /api/v1/agents/

## URL

**Path:** `/api/v1/agents/`

**Full URL:** `<base>/api/v1/agents/`

| Environment | Example full URL |
|-------------|------------------|
| Local | `http://localhost:8000/api/v1/agents/` |

**See also:** [agents README](README.md) (field reference) · [update-agent.md](update-agent.md) · [publish-agent.md](publish-agent.md)

## Summary

Creates a new agent with brand identity, personalization, rules, scenarios, and optional knowledge base / API tool links in one request. New agents start with status `inactive`.

## Auth

```http
Authorization: Bearer <access_token>
```

| Role | Can call |
|------|----------|
| `super_admin` | yes |
| `admin` | yes |
| `read_only` | no (403) |

## Request body

`Content-Type: application/json`

```json
{
  "name": "Support Bot",
  "type": "chat",
  "brand_config": {
    "company_name": "Acme Global Solutions",
    "languages": ["english"],
    "prompt": "Represent Acme with warmth and clarity. Never promise refunds without checking policy.",
    "identity_name": "Alex",
    "timezone": "America/New_York"
  },
  "personalization_config": {
    "tone_profile": "empathetic_professional",
    "pacing": 1.0,
    "formality": "balanced",
    "custom_greeting": "Hello! Thank you for contacting Acme Support. How can I help you today?",
    "custom_sign_off": "Is there anything else I can assist you with before we finish?",
    "enable_sentiment_analysis": true
  },
  "rules": [
    {
      "title": "Privacy",
      "description": "Never ask for passwords."
    }
  ],
  "scenarios": [
    {
      "title": "Refund request",
      "short_description": "Customer asks for a refund.",
      "prompt": "Verify order details, explain policy, and process eligible refunds."
    }
  ],
  "knowledge_base_ids": [],
  "api_tool_ids": []
}
```

### Top-level fields

| Field | Required | Notes |
|-------|----------|-------|
| `name` | yes | 1–255 characters |
| `type` | yes | `chat` \| `voice` — cannot be changed after create |
| `brand_config` | no | Defaults: `company_name` `""`, `languages` `["english"]`, `prompt` `""`, `identity_name` `""`, `timezone` `UTC` |
| `personalization_config` | no | See [README](README.md#personalization_config) |
| `rules` | no | Default `[]` |
| `scenarios` | no | Default `[]` |
| `knowledge_base_ids` | no | Default `[]`; org-scoped UUIDs only |
| `api_tool_ids` | no | Default `[]`; org-scoped UUIDs only |

### Languages

Only English is supported for now. Always send `"languages": ["english"]`. See [README — languages](README.md#brand_configlanguages).

### Voice agents

When `type` is `voice`, `personalization_config.voice_identity` is **required** (non-empty string, max 255).

```json
{
  "name": "Voice Support",
  "type": "voice",
  "personalization_config": {
    "voice_identity": "allison_us_female_neural"
  }
}
```

Categorical values: [README — categorical fields](README.md#categorical-fields).

## Success (201)

```json
{
  "message": "Agent created successfully",
  "status_code": 201,
  "error": false,
  "data": {
    "agent_id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Support Bot",
    "type": "chat",
    "status": "inactive",
    "brand_config": {
      "company_name": "Acme Global Solutions",
      "languages": ["english"],
      "prompt": "Represent Acme with warmth and clarity. Never promise refunds without checking policy.",
      "identity_name": "Alex",
      "timezone": "America/New_York"
    },
    "personalization_config": {
      "tone_profile": "empathetic_professional",
      "voice_identity": null,
      "pacing": 1.0,
      "formality": "balanced",
      "custom_greeting": "Hello! Thank you for contacting Acme Support. How can I help you today?",
      "custom_sign_off": "Is there anything else I can assist you with before we finish?",
      "enable_sentiment_analysis": true
    },
    "rules": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440001",
        "title": "Privacy",
        "description": "Never ask for passwords."
      }
    ],
    "scenarios": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440002",
        "title": "Refund request",
        "short_description": "Customer asks for a refund.",
        "prompt": "Verify order details, explain policy, and process eligible refunds."
      }
    ],
    "knowledge_base_ids": [],
    "api_tool_ids": [],
    "created_at": "2026-06-04T12:00:00Z",
    "updated_at": "2026-06-04T12:00:00Z"
  }
}
```

Response `data` matches [get-agent.md](get-agent.md). Server assigns `agent_id`, rule/scenario `id` values, `status`, and timestamps.

## Errors

| Status | When |
|--------|------|
| 401 | Missing or invalid JWT / session |
| 403 | `read_only` caller |
| 409 | Duplicate agent name in organization (if enforced) |
| 422 | Validation failure (field limits, invalid attachment IDs, missing `voice_identity` for voice, unsupported language, etc.) |

## Frontend notes

- After create, redirect to the agent editor using `data.agent_id`.
- Status remains `inactive` until a version is published ([publish-agent.md](publish-agent.md)) and deployed ([deploy-version.md](deploy-version.md)).
- Store returned rule/scenario `id` values for subsequent [update-agent.md](update-agent.md) calls.
- Hide multi-language UI for now; send `["english"]` only.

## Code

- Endpoint: `src/presentation/api/v1/agents/endpoints/create.py`
- Schemas: `src/presentation/api/v1/agents/schemas.py`
- Use-case: `src/application/agents/use_cases/create_agent.py`
