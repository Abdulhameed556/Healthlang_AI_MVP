# PUT /api/v1/agents/{agent_id}

## URL

**Path:** `/api/v1/agents/{agent_id}`

**Full URL:** `<base>/api/v1/agents/{agent_id}`

| Environment | Example full URL |
|-------------|------------------|
| Local | `http://localhost:8000/api/v1/agents/550e8400-e29b-41d4-a716-446655440000` |

**See also:** [agents README](README.md) · [get-agent.md](get-agent.md) · [publish-agent.md](publish-agent.md)

## Summary

Fully replaces the agent configuration in one request. Nested rules, scenarios, and attachment links are **synced**: items omitted from the payload are removed. Agent `type` cannot be changed (not in request body).

## Auth

```http
Authorization: Bearer <access_token>
```

| Role | Can call |
|------|----------|
| `super_admin` | yes |
| `admin` | yes |
| `read_only` | no (403) |

## Path parameters

| Param | Type | Description |
|-------|------|-------------|
| `agent_id` | UUID | Agent to update |

## Request body

`Content-Type: application/json`

```json
{
  "name": "Support Bot",
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
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "title": "Privacy",
      "description": "Never ask for passwords or full card numbers."
    }
  ],
  "scenarios": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440002",
      "title": "Refund request",
      "short_description": "Customer asks for a refund.",
      "prompt": "Verify order details, explain policy, and escalate when needed."
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
| `brand_config` | no | Same shape as create; `languages` must be `["english"]` for now |
| `personalization_config` | no | Same shape as create; `voice_identity` required for voice agents |
| `rules` | no | Default `[]` — **replaces** all existing rules |
| `scenarios` | no | Default `[]` — **replaces** all existing scenarios |
| `knowledge_base_ids` | no | **Replaces** all KB links |
| `api_tool_ids` | no | **Replaces** all API tool links |

### Rules and scenarios sync

| `id` in payload | Behavior |
|-----------------|----------|
| Existing UUID | Update that row in place |
| `null` or omitted on a new row | Create a new rule/scenario |
| Existing row not in payload | Deleted |

Categorical values and field limits: [README](README.md).

## Success (200)

```json
{
  "message": "Agent updated successfully",
  "status_code": 200,
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
        "description": "Never ask for passwords or full card numbers."
      }
    ],
    "scenarios": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440002",
        "title": "Refund request",
        "short_description": "Customer asks for a refund.",
        "prompt": "Verify order details, explain policy, and escalate when needed."
      }
    ],
    "knowledge_base_ids": [],
    "api_tool_ids": [],
    "created_at": "2026-06-04T12:00:00Z",
    "updated_at": "2026-06-04T12:45:00Z"
  }
}
```

Response `data` matches [get-agent.md](get-agent.md). Update does **not** change `status` or create a version — call [publish-agent.md](publish-agent.md) when the draft is ready, then [deploy-version.md](deploy-version.md) to go live.

## Errors

| Status | When |
|--------|------|
| 401 | Missing or invalid JWT / session |
| 403 | `read_only` caller |
| 404 | Agent not found or not in caller's organization |
| 409 | Conflict (e.g. duplicate name) |
| 422 | Validation failure, invalid attachment IDs, unsupported language, rule/scenario field limits |

## Frontend notes

- Always send the **full** desired state (full replace), not a partial patch.
- After save, refresh `id` values for newly created rules/scenarios from `data`.
- Updates the **draft** only. Live runtime still uses the deployed snapshot until the user [publishes](publish-agent.md) and [deploys](deploy-version.md) another version.

## Code

- Endpoint: `src/presentation/api/v1/agents/endpoints/update.py`
- Use-case: `src/application/agents/use_cases/update_agent.py`
