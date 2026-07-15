# ADR 001 — Adopt Clean Architecture

**Status:** Accepted  
**Date:** 2025-01

## Context
We need a structure that scales across teams, is easy to unit-test,
and supports replacing infrastructure (DB, storage) without touching
business logic.

## Decision
Use Clean / Hexagonal Architecture with four strict layers.
Dependency arrows always point inward toward the domain.

## Consequences
+ Business logic is 100 % pure Python — no framework, no DB imports.
+ Infrastructure can be swapped or mocked trivially.
- More files / indirection than a simple CRUD approach.
