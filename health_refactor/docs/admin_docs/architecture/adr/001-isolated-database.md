# ADR 001 — Admin Panel Uses an Isolated Database

**Status:** Accepted | **Date:** 2025-01

## Decision
The Admin Panel backend has its own Postgres database (`admin_panel`).
It owns only admin-specific tables (admin_users, admin_sessions,
admin_invitations). All product data is fetched from the backend via
internal API calls.

## Consequences
+ Full isolation — a backend schema change never breaks the admin service.
+ Admin credentials never touch the product user table.
- Admin must proxy reads through the backend for org/user/agent data.
