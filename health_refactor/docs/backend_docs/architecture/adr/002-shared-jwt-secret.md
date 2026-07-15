# ADR 002 — Shared JWT Secret Between Backend and AI Service

**Status:** Accepted  
**Date:** 2025-01

## Context
The AI service must authenticate requests without calling the backend
on every inference hop.

## Decision
Both services read `JWT_SECRET_KEY` from their respective `.env` files.
The backend mints tokens; the AI service only verifies them.
The secret is rotated via coordinated deploy.

## Consequences
+ Zero-latency auth on the AI side.
- Secret rotation requires simultaneous deploy of both services.
