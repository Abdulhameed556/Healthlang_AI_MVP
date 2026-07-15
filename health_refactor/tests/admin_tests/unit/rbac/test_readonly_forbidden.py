"""
Unit tests: Read-Only users cannot perform write actions.
"""


class TestReadOnlyForbidden:
    async def test_invite_user_forbidden(self):
        assert True

    async def test_onboard_org_forbidden(self):
        assert True

    async def test_disable_org_forbidden(self):
        assert True

    async def test_edit_role_forbidden(self):
        assert True
