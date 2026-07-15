"""OpenAPI tag catalog — groups endpoints in Swagger UI."""

OPENAPI_TAGS: list[dict[str, str]] = [
    {
        "name": "health",
        "description": "Liveness and readiness checks (no auth).",
    },
    {
        "name": "auth",
        "description": "Registration, login, OAuth, password reset, and session management.",
    },
    {
        "name": "users",
        "description": "Current user profile and account settings.",
    },
    {
        "name": "departments",
        "description": "Department settings and member invitations.",
    },
    {
        "name": "patients",
        "description": "Patient demographics.",
    },
    {
        "name": "encounters",
        "description": "Check-in, the visit state machine, and the department queue.",
    },
    {
        "name": "triage",
        "description": "ESI-level vitals triage and nurse override.",
    },
    {
        "name": "clinical-notes",
        "description": "Doctor diagnosis and consultation notes.",
    },
    {
        "name": "lab-orders",
        "description": "Lab test orders and results.",
    },
    {
        "name": "prescriptions",
        "description": "Medication orders and dispensing.",
    },
    {
        "name": "inventory",
        "description": "Department drug stock.",
    },
    {
        "name": "audit-log",
        "description": "Who did what, when, from where, and with what outcome.",
    },
    {
        "name": "break-glass",
        "description": "Emergency access outside a clinician's normal assignment.",
    },
    {
        "name": "dashboard",
        "description": "Aggregate, anonymized department stats.",
    },
    {
        "name": "internal-admin",
        "description": (
            "Admin Portal → Backend (server-to-server). Requires `X-Admin-Api-Key`. "
            "Not for the product SPA."
        ),
    },
]
