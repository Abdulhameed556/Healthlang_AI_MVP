# Agents API (`/api/v1/agents`)

JWT-protected, organization-scoped routes for configuring support agents (chat and voice).

Send `Authorization: Bearer <access_token>` on every call. Obtain the token from
[login](../auth/login.md) or [Google login](../auth/google-login.md). For multi-org
users, optionally add `X-Organization-Id` — see
[organization context](../auth/organization-context.md).

| Doc | Method | Path | Who can call |
|-----|--------|------|--------------|
| [list-agents.md](list-agents.md) | GET | `/api/v1/agents/` | All roles |
| [create-agent.md](create-agent.md) | POST | `/api/v1/agents/` | `super_admin`, `admin` |
| [get-agent.md](get-agent.md) | GET | `/api/v1/agents/{agent_id}` | All roles |
| [update-agent.md](update-agent.md) | PUT | `/api/v1/agents/{agent_id}` | `super_admin`, `admin` |
| [delete-agent.md](delete-agent.md) | DELETE | `/api/v1/agents/{agent_id}` | `super_admin`, `admin` |
| [publish-agent.md](publish-agent.md) | POST | `/api/v1/agents/{agent_id}/publish` | `super_admin`, `admin` |
| [deploy-version.md](deploy-version.md) | POST | `/api/v1/agents/{agent_id}/versions/{version_id}/deploy` | `super_admin`, `admin` |
| [list-versions.md](list-versions.md) | GET | `/api/v1/agents/{agent_id}/versions` | All roles |
| [get-version.md](get-version.md) | GET | `/api/v1/agents/{agent_id}/versions/{version_id}` | All roles |
| [deployed-version.md](deployed-version.md) | GET | `/api/v1/agents/{agent_id}/deployed-version` | All roles |
| [list-conversations.md](list-conversations.md) | GET | `/api/v1/agents/{agent_id}/conversations` | All roles |

## Draft, publish, deploy

Agents have one mutable **draft** plus a history of immutable **versions**, and at most one of those versions is **live**:

| Concept | Source | Mutable? | Used by runtime |
|---------|--------|----------|-----------------|
| **Draft** | Agent row ([get-agent.md](get-agent.md) / [update-agent.md](update-agent.md)) | yes | no |
| **Version** | Published snapshot (`v1`, `v2`, …) | no (immutable) | only when deployed |
| **Live** | The deployed version (`deployed_version_id` on the agent) | no | yes |

- **Publish** ([publish-agent.md](publish-agent.md)) freezes the current draft as a **new** immutable version with author + `changes_applied` diff. It does **not** go live.
- **Deploy** ([deploy-version.md](deploy-version.md)) promotes an **existing** version to live (and invalidates the runtime cache). Use it to go live with a fresh publish or to **roll back** to an older version. It does **not** create a version.
- **Restore:** load any version via [get-version.md](get-version.md) and save it back into the draft with [update-agent.md](update-agent.md); the version row stays immutable.
- Editing the draft after deploy does **not** change live until you publish again and deploy that version.


All endpoints return:

```json
{
  "message": "…",
  "status_code": 200,
  "error": false,
  "data": { }
}
```

On failure, `error` is `true` and `data` is typically `null`.

## Categorical fields

### `type` (create only; immutable after create)

| Value | Description |
|-------|-------------|
| `chat` | Text-based support agent |
| `voice` | Voice agent; `personalization_config.voice_identity` is **required** on create |

### `status` (read-only in requests; set by the API)

| Value | Description |
|-------|-------------|
| `inactive` | No version is live yet (may still have published-but-undeployed versions) |
| `deployed` | A version is marked live via `deployed_version_id` |

New agents are created with `inactive`. Publishing ([publish-agent.md](publish-agent.md)) alone keeps status `inactive`; the first [deploy-version.md](deploy-version.md) sets status to `deployed` and points live at the chosen version. Deploying another version (newer or older) re-points live without changing status.

### `brand_config.languages`

Only **English** is supported in v1. Send `["english"]` (array with one item).

| Value | Supported |
|-------|-----------|
| `english` | yes |

Additional languages will be added in a future release. The frontend should not offer other options yet.

### `brand_config.timezone`

IANA timezone from the **supported catalog** below. Default `UTC`.

At chat time the platform computes **current local date and time** from this value and injects it into:

- **Orchestrator** system prompt (`format_current_datetime_context` under Brand identity)
- **Scenario routing** system prompt (`Session context` block)

The value is recomputed on **every turn** (not stored as a static string). Unsupported values sent via the API return **422**; legacy stored values outside the catalog are normalized to `UTC` when loaded.

Canonical source: `backend/src/domain/agents/timezones.py` (demo UI: `demo-ui/agent-catalog.js`).

| Value | Supported |
|-------|-----------|
| `UTC` | yes |
| `America/New_York` | yes |
| `America/Chicago` | yes |
| `America/Denver` | yes |
| `America/Los_Angeles` | yes |
| `America/Phoenix` | yes |
| `America/Anchorage` | yes |
| `America/Toronto` | yes |
| `America/Vancouver` | yes |
| `America/Mexico_City` | yes |
| `America/Bogota` | yes |
| `America/Lima` | yes |
| `America/Santiago` | yes |
| `America/Sao_Paulo` | yes |
| `America/Buenos_Aires` | yes |
| `America/Panama` | yes |
| `America/Jamaica` | yes |
| `Pacific/Honolulu` | yes |
| `Europe/London` | yes |
| `Europe/Dublin` | yes |
| `Europe/Paris` | yes |
| `Europe/Berlin` | yes |
| `Europe/Amsterdam` | yes |
| `Europe/Brussels` | yes |
| `Europe/Madrid` | yes |
| `Europe/Rome` | yes |
| `Europe/Zurich` | yes |
| `Europe/Stockholm` | yes |
| `Europe/Warsaw` | yes |
| `Europe/Athens` | yes |
| `Europe/Istanbul` | yes |
| `Europe/Moscow` | yes |
| `Africa/Lagos` | yes |
| `Africa/Accra` | yes |
| `Africa/Abidjan` | yes |
| `Africa/Douala` | yes |
| `Africa/Kinshasa` | yes |
| `Africa/Luanda` | yes |
| `Africa/Nairobi` | yes |
| `Africa/Addis_Ababa` | yes |
| `Africa/Kampala` | yes |
| `Africa/Kigali` | yes |
| `Africa/Dar_es_Salaam` | yes |
| `Africa/Johannesburg` | yes |
| `Africa/Harare` | yes |
| `Africa/Lusaka` | yes |
| `Africa/Maputo` | yes |
| `Africa/Windhoek` | yes |
| `Africa/Cairo` | yes |
| `Africa/Casablanca` | yes |
| `Africa/Algiers` | yes |
| `Africa/Tunis` | yes |
| `Asia/Dubai` | yes |
| `Asia/Riyadh` | yes |
| `Asia/Jerusalem` | yes |
| `Asia/Karachi` | yes |
| `Asia/Kolkata` | yes |
| `Asia/Dhaka` | yes |
| `Asia/Bangkok` | yes |
| `Asia/Singapore` | yes |
| `Asia/Hong_Kong` | yes |
| `Asia/Shanghai` | yes |
| `Asia/Tokyo` | yes |
| `Asia/Seoul` | yes |
| `Asia/Manila` | yes |
| `Asia/Jakarta` | yes |
| `Australia/Perth` | yes |
| `Australia/Sydney` | yes |
| `Australia/Melbourne` | yes |
| `Pacific/Auckland` | yes |

### `personalization_config.tone_profile`

| Value |
|-------|
| `empathetic_professional` |
| `friendly_casual` |
| `formal_business` |
| `concise_direct` |

### `personalization_config.formality`

| Value |
|-------|
| `casual` |
| `balanced` |
| `formal` |

## Shared configuration shape

Create, update, get, and published version snapshots all use the same nested structure for
brand, personalization, rules, scenarios, and attachments.

### `brand_config`

| Field | Type | Required | Limits / notes |
|-------|------|----------|----------------|
| `company_name` | string | no | max 255; default `""` |
| `languages` | string[] | yes | Must be `["english"]` for now |
| `prompt` | string | no | max 2000; free-form brand identity and tone instructions; default `""` |
| `identity_name` | string | no | max 255; customer-facing name the agent uses for itself; default `""` (falls back to agent `name`) |
| `timezone` | string | no | Supported IANA timezone from catalog below; default `UTC`; live date/time context in orchestrator + scenario routing prompts |

### `personalization_config`

| Field | Type | Required | Limits / notes |
|-------|------|----------|----------------|
| `tone_profile` | string | no | Default `empathetic_professional` |
| `voice_identity` | string \| null | voice only | max 255; e.g. `allison_us_female_neural`; ignored for `chat` |
| `pacing` | number | no | 0.5–2.0; default `1.0` |
| `formality` | string | no | Default `balanced` |
| `custom_greeting` | string | no | max 5000 |
| `custom_sign_off` | string | no | max 5000 |
| `enable_sentiment_analysis` | boolean | no | default `false` |

### `rules[]`

| Field | Create | Update | Limits |
|-------|--------|--------|--------|
| `id` | — | optional UUID | Omit or `null` to create a new rule; include existing id to update in place |
| `title` | required | required | 1–255 chars |
| `description` | optional | optional | max 10000; default `""` |

On update, rules **not** included in the payload are deleted.

### `scenarios[]`

| Field | Create | Update | Limits |
|-------|--------|--------|--------|
| `id` | — | optional UUID | Same sync semantics as rules |
| `title` | required | required | 1–255 chars |
| `short_description` | optional | optional | max 500; default `""` |
| `prompt` | optional | optional | max 4000; default `""` |

On update, scenarios **not** included in the payload are deleted.

### Attachments

| Field | Type | Notes |
|-------|------|-------|
| `knowledge_base_ids` | UUID[] | Each ID must belong to the caller's organization; use `[]` when none linked |
| `api_tool_ids` | UUID[] | Same validation as knowledge bases |

Invalid attachment IDs return **422**. Link tools via `api_tool_ids` using IDs from [../api_tools/README.md](../api_tools/README.md).

### Full configuration example (`data` on create / get / update)

```json
{
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
  "updated_at": "2026-06-04T12:00:00Z"
}
```

## Typical wizard flow

1. **List** existing agents → [list-agents.md](list-agents.md)
2. **Create** draft (`inactive`) → [create-agent.md](create-agent.md)
3. **Edit** draft via full replace → [update-agent.md](update-agent.md)
4. **Publish** draft → new immutable version (not live) → [publish-agent.md](publish-agent.md)
5. **Deploy** that version → go live → [deploy-version.md](deploy-version.md)
6. **Audit** version history (live row flagged via `is_deployed`) → [list-versions.md](list-versions.md)
7. **Restore** (optional) → load a past version → [get-version.md](get-version.md) → save into draft → [update-agent.md](update-agent.md)
8. **Rollback** (optional) → deploy an older version → [deploy-version.md](deploy-version.md)

Example: publish v1 → deploy v1 (live) → edit draft → publish v2 → deploy v2 (live) → deploy v1 (live again, v2 still in history) → edit draft → publish v3 → deploy v3 (live).

**Related:** [../auth/login.md](../auth/login.md) · [../organizations/README.md](../organizations/README.md)
