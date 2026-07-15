# ADR 002 — Admin Panel Has Its Own JWT Secret

**Status:** Accepted | **Date:** 2025-01

## Decision
The admin service uses a completely separate JWT_SECRET_KEY.
Admin Panel sessions cannot be replayed against the backend or AI service,
and backend tokens cannot be used to authenticate to the Admin Panel.

## Consequences
+ Zero cross-service session bleed.
- Three secrets to manage (backend, AI, admin). Use a secrets manager.
