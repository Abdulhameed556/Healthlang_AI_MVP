# API Endpoint Reference

All routes are prefixed `/api/v1`. Full URL: **`<base>/api/v1/...`** (see [README.md](README.md#base-url)).

All JSON responses use the standard envelope (`message`, `status_code`, `error`, `data`).

**JWT** in the Auth column means `Authorization: Bearer <access_token>`. On any JWT
route, you may also send optional `X-Organization-Id: <uuid>` to scope the request to
another org the user belongs to — see
[v1/auth/organization-context.md](v1/auth/organization-context.md).

**Implemented** routes link to frontend docs under `v1/<module>/`. Routes marked *stub* are not wired yet.

| Method | Path | Full URL (local example) | Auth | Doc | Description |
|---|---|---|---|---|---|
| GET | /health | `http://localhost:8000/api/v1/health` | — | — | API health check |
| GET | /internal/admin/health | `http://localhost:8000/api/v1/internal/admin/health` | Admin API key | — | Internal admin health |
| POST | /internal/admin/users | `http://localhost:8000/api/v1/internal/admin/users` | Admin API key | [create-invited-user](v1/internal/admin/create-invited-user.md) | Provision org + invited super-admin |
| POST | /auth/login | `http://localhost:8000/api/v1/auth/login` | — | [login](v1/auth/login.md) | Email/password login or invite activation |
| GET | /auth/google/url | `http://localhost:8000/api/v1/auth/google/url` | — | [google-url](v1/auth/google-url.md) | Google OAuth authorization URL |
| POST | /auth/google | `http://localhost:8000/api/v1/auth/google` | — | [google-login](v1/auth/google-login.md) | Google OAuth login or invite activation |
| POST | /invitations/{token}/decline | `http://localhost:8000/api/v1/invitations/{token}/decline` | — | [decline](v1/invitations/decline.md) | Decline pending invitation |
| POST | /auth/register | — | — | *stub* | Not implemented |
| POST | /auth/logout | `http://localhost:8000/api/v1/auth/logout` | JWT | [logout](v1/auth/logout.md) | Invalidate current session |
| POST | /auth/refresh | `http://localhost:8000/api/v1/auth/refresh` | — | [refresh](v1/auth/refresh.md) | Exchange refresh token for new access token |
| POST | /auth/password-reset/request | `http://localhost:8000/api/v1/auth/password-reset/request` | — | [password-reset-request](v1/auth/password-reset-request.md) | Request reset email (email/password users) |
| POST | /auth/password-reset/complete | `http://localhost:8000/api/v1/auth/password-reset/complete` | — | [password-reset-complete](v1/auth/password-reset-complete.md) | Set new password with reset token |
| GET | /users/me | `http://localhost:8000/api/v1/users/me` | JWT | [me](v1/users/me.md) | Current user profile |
| GET | /users/me/organizations | `http://localhost:8000/api/v1/users/me/organizations` | JWT | [list-organizations](v1/users/list-organizations.md) | Active org memberships for org switcher |
| GET | /organizations/me | `http://localhost:8000/api/v1/organizations/me` | JWT | [me](v1/organizations/me.md) | Current organization profile |
| PATCH | /organizations/me | `http://localhost:8000/api/v1/organizations/me` | JWT (`super_admin` / `admin`) | [update-profile](v1/organizations/update-profile.md) | Update org name, industry, description |
| GET | /organizations/users | `http://localhost:8000/api/v1/organizations/users` | JWT (`super_admin` / `admin`) | [users](v1/organizations/users.md) | List org members (email, role) |
| DELETE | /organizations/users/{user_id} | `http://localhost:8000/api/v1/organizations/users/{user_id}` | JWT (`super_admin` / `admin`) | [remove-member](v1/organizations/remove-member.md) | Remove member from org |
| PATCH | /organizations/users/{user_id}/role | `http://localhost:8000/api/v1/organizations/users/{user_id}/role` | JWT (`super_admin` / `admin`) | [update-member-role](v1/organizations/update-member-role.md) | Change member role |
| POST | /organizations/users/invite | `http://localhost:8000/api/v1/organizations/users/invite` | JWT (`super_admin` / `admin`) | [invite-user](v1/organizations/invite-user.md) | Invite teammate to org |
| POST | /invitations/{token}/accept | — | — | — | Use `/auth/login` or `/auth/google` with `is_new: true` |
| GET | /agents/ | `http://localhost:8000/api/v1/agents/` | JWT | [list-agents](v1/agents/list-agents.md) | Paginated agent summaries |
| POST | /agents/ | `http://localhost:8000/api/v1/agents/` | JWT (`super_admin` / `admin`) | [create-agent](v1/agents/create-agent.md) | Create agent configuration |
| GET | /agents/{agent_id} | `http://localhost:8000/api/v1/agents/{agent_id}` | JWT | [get-agent](v1/agents/get-agent.md) | Full agent configuration |
| PUT | /agents/{agent_id} | `http://localhost:8000/api/v1/agents/{agent_id}` | JWT (`super_admin` / `admin`) | [update-agent](v1/agents/update-agent.md) | Replace agent configuration |
| DELETE | /agents/{agent_id} | `http://localhost:8000/api/v1/agents/{agent_id}` | JWT (`super_admin` / `admin`) | [delete-agent](v1/agents/delete-agent.md) | Delete agent |
| POST | /agents/{agent_id}/publish | `http://localhost:8000/api/v1/agents/{agent_id}/publish` | JWT (`super_admin` / `admin`) | [publish-agent](v1/agents/publish-agent.md) | Freeze draft as new immutable version (not live) |
| POST | /agents/{agent_id}/versions/{version_id}/deploy | `http://localhost:8000/api/v1/agents/{agent_id}/versions/{version_id}/deploy` | JWT (`super_admin` / `admin`) | [deploy-version](v1/agents/deploy-version.md) | Go live with / roll back to an existing version |
| GET | /agents/{agent_id}/versions | `http://localhost:8000/api/v1/agents/{agent_id}/versions` | JWT | [list-versions](v1/agents/list-versions.md) | Paginated version history (`is_deployed` flag) |
| GET | /agents/{agent_id}/versions/{version_id} | `http://localhost:8000/api/v1/agents/{agent_id}/versions/{version_id}` | JWT | [get-version](v1/agents/get-version.md) | Single version snapshot |
| GET | /agents/{agent_id}/deployed-version | `http://localhost:8000/api/v1/agents/{agent_id}/deployed-version` | JWT | [deployed-version](v1/agents/deployed-version.md) | Currently live version snapshot |
| GET | /tickets/ | `http://localhost:8000/api/v1/tickets/` | JWT | [list-tickets](v1/tickets/list-tickets.md) | Paginated tickets with filters + search |
| POST | /tickets/ | `http://localhost:8000/api/v1/tickets/` | JWT | [create-ticket](v1/tickets/create-ticket.md) | Manually create a ticket |
| GET | /tickets/{ticket_id} | `http://localhost:8000/api/v1/tickets/{ticket_id}` | JWT | [get-ticket](v1/tickets/get-ticket.md) | Ticket detail, summary, session history |
| GET | /dashboard/metrics | `http://localhost:8000/api/v1/dashboard/metrics` | JWT | [get-ticket-metrics](v1/dashboard/get-ticket-metrics.md) | Ticket summary + weekday chart for dashboard |
| GET | /numbers | — | JWT | *stub* | Not implemented |
| POST | /numbers | — | JWT admin | *stub* | Not implemented |
| GET | /widgets | — | JWT | *stub* | Not implemented |
| POST | /widgets | — | JWT | *stub* | Not implemented |
| POST | /knowledge-base/ | `http://localhost:8000/api/v1/knowledge-base/` | JWT (`super_admin` / `admin`) | [create-knowledge-base](v1/knowledge_bases/create-knowledge-base.md) | Create an empty knowledge base container |
| DELETE | /knowledge-base/{kb_id} | `http://localhost:8000/api/v1/knowledge-base/{kb_id}` | JWT (`super_admin` / `admin`) | [delete-knowledge-base](v1/knowledge_bases/delete-knowledge-base.md) | Hard-delete KB, all entries, S3 files, and vectors |
| POST | /knowledge-base/{kb_id}/entries/upload-url | `http://localhost:8000/api/v1/knowledge-base/{kb_id}/entries/upload-url` | JWT | [generate-upload-url](v1/knowledge_bases/generate-upload-url.md) | Create DB entry + return presigned S3 PUT URL |
| POST | /knowledge-base/{kb_id}/entries/{entry_id}/confirm-upload | `http://localhost:8000/api/v1/knowledge-base/{kb_id}/entries/{entry_id}/confirm-upload` | JWT | [confirm-upload](v1/knowledge_bases/confirm-upload.md) | Verify S3 upload and queue indexing |
| POST | /knowledge-base/{kb_id}/entries/text | `http://localhost:8000/api/v1/knowledge-base/{kb_id}/entries/text` | JWT (`super_admin` / `admin`) | [create-text-entry](v1/knowledge_bases/create-text-entry.md) | Create and index a plain-text entry (no S3 step) |
| GET | /knowledge-base/{kb_id}/entries | `http://localhost:8000/api/v1/knowledge-base/{kb_id}/entries` | JWT | [list-entries](v1/knowledge_bases/list-entries.md) | Paginated entry list with search, status, and archived filters |
| PATCH | /knowledge-base/{kb_id}/entries/{entry_id} | `http://localhost:8000/api/v1/knowledge-base/{kb_id}/entries/{entry_id}` | JWT (`super_admin` / `admin`) | [update-entry](v1/knowledge_bases/update-entry.md) | Rename, archive, unarchive, or retry indexing |
| DELETE | /knowledge-base/{kb_id}/entries/{entry_id} | `http://localhost:8000/api/v1/knowledge-base/{kb_id}/entries/{entry_id}` | JWT (`super_admin` / `admin`) | [delete-entry](v1/knowledge_bases/delete-entry.md) | Hard-delete entry (DB + S3 file + vectors) |
| POST | /knowledge-base/{kb_id}/agents/{agent_id} | `http://localhost:8000/api/v1/knowledge-base/{kb_id}/agents/{agent_id}` | JWT (`super_admin` / `admin`) | [attach-agent](v1/knowledge_bases/attach-agent.md) | Link an agent to this KB for retrieval |
| DELETE | /knowledge-base/{kb_id}/agents/{agent_id} | `http://localhost:8000/api/v1/knowledge-base/{kb_id}/agents/{agent_id}` | JWT (`super_admin` / `admin`) | [detach-agent](v1/knowledge_bases/detach-agent.md) | Unlink an agent from this KB |
| GET | /api-tools/ | `http://localhost:8000/api/v1/api-tools/` | JWT | [list-api-tools](v1/api_tools/list-api-tools.md) | Paginated API tools |
| POST | /api-tools/ | `http://localhost:8000/api/v1/api-tools/` | JWT (`super_admin` / `admin`) | [create-api-tool](v1/api_tools/create-api-tool.md) | Create HTTP GET tool |
| GET | /api-tools/{api_tool_id} | `http://localhost:8000/api/v1/api-tools/{api_tool_id}` | JWT | [get-api-tool](v1/api_tools/get-api-tool.md) | Get tool by id |
| PUT | /api-tools/{api_tool_id} | `http://localhost:8000/api/v1/api-tools/{api_tool_id}` | JWT (`super_admin` / `admin`) | [update-api-tool](v1/api_tools/update-api-tool.md) | Replace tool configuration |
| DELETE | /api-tools/{api_tool_id} | `http://localhost:8000/api/v1/api-tools/{api_tool_id}` | JWT (`super_admin` / `admin`) | [delete-api-tool](v1/api_tools/delete-api-tool.md) | Delete tool (409 if attached) |
| POST | /api-tools/test | `http://localhost:8000/api/v1/api-tools/test` | JWT (`super_admin` / `admin`) | [test-api-tool-draft](v1/api_tools/test-api-tool-draft.md) | Test unsaved tool config |
| POST | /api-tools/{api_tool_id}/test | `http://localhost:8000/api/v1/api-tools/{api_tool_id}/test` | JWT (`super_admin` / `admin`) | [test-api-tool](v1/api_tools/test-api-tool.md) | Test saved tool |
| GET | /tags/ | `http://localhost:8000/api/v1/tags/` | JWT | [list-tags](v1/tags/list-tags.md) | Paginated tag catalog with search |
| POST | /tags/ | `http://localhost:8000/api/v1/tags/` | JWT (`super_admin` / `admin`) | [create-tag](v1/tags/create-tag.md) | Create classification tag |
| GET | /tags/{tag_id} | `http://localhost:8000/api/v1/tags/{tag_id}` | JWT | [get-tag](v1/tags/get-tag.md) | Get tag by id |
| PUT | /tags/{tag_id} | `http://localhost:8000/api/v1/tags/{tag_id}` | JWT (`super_admin` / `admin`) | [update-tag](v1/tags/update-tag.md) | Replace tag value/description |
| DELETE | /tags/{tag_id} | `http://localhost:8000/api/v1/tags/{tag_id}` | JWT (`super_admin` / `admin`) | [delete-tag](v1/tags/delete-tag.md) | Delete tag |
| POST | /integrations/freshchat/resources | `http://localhost:8000/api/v1/integrations/freshchat/resources` | JWT (`super_admin` / `admin`) | [resources](v1/integrations/freshchat/resources.md) | List Freshchat channels, groups, agents for the connect form |
| POST | /integrations/freshchat/connect | `http://localhost:8000/api/v1/integrations/freshchat/connect` | JWT (`super_admin` / `admin`) | [connect](v1/integrations/freshchat/connect.md) | Connect/reconnect Freshchat with per-channel routing |
| GET | /integrations/freshchat/settings | `http://localhost:8000/api/v1/integrations/freshchat/settings` | JWT | [get-settings](v1/integrations/freshchat/get-settings.md) | Saved Freshchat config with resolved names |
| PATCH | /integrations/freshchat/settings | `http://localhost:8000/api/v1/integrations/freshchat/settings` | JWT (`super_admin` / `admin`) | [update-settings](v1/integrations/freshchat/update-settings.md) | Update agent/routing/handoff/key (no credentials) |
| DELETE | /integrations/{integration_id} | `http://localhost:8000/api/v1/integrations/{integration_id}` | JWT (`super_admin` / `admin`) | [delete-integration](v1/integrations/delete-integration.md) | Delete integration, agent links, linked chat sessions (tickets kept), and Freshchat Redis cache |
| POST | /integrations/freshchat/webhook/{webhook_secret} | `http://localhost:8000/api/v1/integrations/freshchat/webhook/{webhook_secret}` | Public (Freshchat) | [webhook](v1/integrations/freshchat/webhook.md) | Receive Freshchat events (secret + RSA signature) |
| GET | /evaluations | — | JWT | *stub* | Not implemented |
| POST | /evaluations | — | JWT | *stub* | Not implemented |

See also:

- [v1/auth/README.md](v1/auth/README.md) — login, Google OAuth, password reset, logout, refresh
- [v1/auth/organization-context.md](v1/auth/organization-context.md) — optional `X-Organization-Id` on JWT routes
- [v1/users/README.md](v1/users/README.md) — current user profile, org memberships
- [v1/organizations/README.md](v1/organizations/README.md) — org profile, members, invite
- [v1/agents/README.md](v1/agents/README.md) — agent draft vs live, deploy, activate, versions
- [v1/tickets/README.md](v1/tickets/README.md) — list/search, detail, manual create; ticket categorical fields
- [v1/dashboard/README.md](v1/dashboard/README.md) — ticket metrics for dashboard KPIs and weekday chart
- [v1/integrations/README.md](v1/integrations/README.md) — delete integration; see [Freshchat](v1/integrations/freshchat/README.md) for connect/settings/webhook
- [v1/api_tools/README.md](v1/api_tools/README.md) — HTTP GET tools for agents, test endpoints
- [v1/tags/README.md](v1/tags/README.md) — org tag catalog for AI ticket classification + filtering
- [v1/knowledge_bases/README.md](v1/knowledge_bases/README.md) — file upload flow, indexing status, supported types
- [v1/integrations/freshchat/README.md](v1/integrations/freshchat/README.md) — connect Freshchat, per-channel routing, webhook; see also [architecture/freshchat-integration.md](../architecture/freshchat-integration.md)
