PR:  – Initial Migration & Shared DB Alembic Setup
@Abdulhameed
Summary
This PR adds the initial backend database migration and configures Alembic for a shared database setup between the Backend and Admin services.
Changes

Configured async Alembic environment.
Added dedicated alembic_version_backend table to prevent migration conflicts with the Admin service's alembic_version table when both services share the same PostgreSQL instance.
Configured include_object to exclude Admin tables from Backend migration autogeneration.
Added initial migration revision: fb34dc650e06.
Generated the initial migration for the core application schema.
Updated User model default status to INVITED.
Validation

:white_check_mark: Linting checks passed
:white_check_mark: All tests passed