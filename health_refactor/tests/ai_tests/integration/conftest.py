"""Integration tests require external services — skipped in default CI/local test runs."""
import pytest

pytestmark = pytest.mark.skip(reason="Requires external services — use make test-integration when ready")
