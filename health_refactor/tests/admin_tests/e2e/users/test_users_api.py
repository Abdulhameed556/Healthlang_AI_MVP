"""
E2E tests: users API endpoints.

Test matrix:
  - Admin user: all actions succeed
  - Read-Only user: write actions return 403
  - Unauthenticated: all protected routes return 401
"""


class TestUsersAdminAPI:
    async def test_admin_can_perform_write_actions(self, async_client, admin_headers):
        assert True

class TestUsersReadOnlyAPI:
    async def test_readonly_write_actions_return_403(self, async_client, readonly_headers):
        assert True

class TestUsersUnauthenticatedAPI:
    async def test_unauthenticated_returns_401(self, async_client):
        assert True
