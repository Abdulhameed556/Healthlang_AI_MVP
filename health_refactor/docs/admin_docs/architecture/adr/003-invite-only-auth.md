# ADR 003 — Invite-Only Authentication, Seeded Initial Admin

**Status:** Accepted | **Date:** 2025-01

## Decision
No self-registration endpoint exists. The initial admin account is
created by `scripts/seed_initial_admin.py` at deploy time.
All subsequent accounts are created through the invite flow.

## Consequences
+ No attack surface for unauthorised account creation.
- Ops must run the seed script exactly once per environment.
