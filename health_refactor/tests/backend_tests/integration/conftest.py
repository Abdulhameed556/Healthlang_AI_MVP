"""Integration tests require a real database — skipped in default CI/local test runs."""
import pytest

pytestmark = pytest.mark.skip(reason="Requires test database — use make test-integration when ready")
