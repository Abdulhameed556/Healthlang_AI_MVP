# GET /api/v1/agents/{agent_id}

## URL

**Path:** `/api/v1/agents/{agent_id}`

**Full URL:** `<base>/api/v1/agents/{agent_id}`

| Environment | Example full URL |
|-------------|------------------|
| Local | `http://localhost:8000/api/v1/agents/550e8400-e29b-41d4-a716-446655440000` |

**See also:** [agents README](README.md) · [list-agents.md](list-agents.md) · [update-agent.md](update-agent.md)

## Summary

Returns the **editable draft** agent configuration for the caller's organization, including brand settings, personalization, rules, scenarios, and attachment IDs. This is not necessarily what is live at runtime — see [agents README](README.md#draft-vs-live) and [list-versions.md](list-versions.md).

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

| Param | Type | Description |
|-------|------|-------------|
| `agent_id` | UUID | Agent to load |

## Success (200)

```json
{
  "message": "Agent retrieved successfully",
  "status_code": 200,
  "error": false,
  "data": {
    "agent_id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Support Bot",
    "type": "chat",
    "status": "deployed",
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
    "updated_at": "2026-06-04T12:30:00Z"
  }
}
```

Field reference and categorical values: [README](README.md). `brand_config.languages` is `["english"]` in v1.

## Errors

| Status | When |
|--------|------|
| 401 | Missing or invalid JWT / session |
| 404 | Agent not found or not in caller's organization |
| 422 | Invalid `agent_id` format |

## Frontend notes

- Use this to populate the configuration wizard; `type` is read-only in the UI after create.
- `status` is informational — only [deploy-version.md](deploy-version.md) changes it to `deployed`.
- For the agents list view, prefer [list-agents.md](list-agents.md) (lighter payload).

## Code

- Endpoint: `src/presentation/api/v1/agents/endpoints/detail.py`
- Use-case: `src/application/agents/use_cases/get_agent.py`
