# ADR 004 — RBAC Enforced Server-Side, Always

**Status:** Accepted | **Date:** 2025-01

## Decision
Every write endpoint uses `Depends(require_admin)`. The UI hiding
buttons for Read-Only users is purely cosmetic. A Read-Only user
hitting a write endpoint directly always receives 403.

## Consequences
+ Security cannot be bypassed by UI manipulation.
- Every new write endpoint must explicitly declare the dependency.
