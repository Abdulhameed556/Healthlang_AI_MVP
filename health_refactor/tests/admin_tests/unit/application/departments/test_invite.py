"""Unit tests: invite-product-user use-case + DI provider."""
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

from admin.src.application.departments.dependencies import (
    get_invite_product_user_use_case,
)
from admin.src.application.departments.use_cases.invite_product_user import (
    InviteProductUserUseCase,
)
from backend.src.application.users.results.admin import CreateInvitedUserFromAdminResult

_ARGS = dict(
    email="u@x.com",
    department_name="Emergency Department",
    first_name="Ada",
    last_name="Lovelace",
    description="desc",
)

_DEPT_ID = UUID("00000000-0000-0000-0000-000000000001")
_USER_ID = UUID("00000000-0000-0000-0000-000000000002")
_INV_ID = UUID("00000000-0000-0000-0000-000000000003")

_RESULT = CreateInvitedUserFromAdminResult(
    department_id=_DEPT_ID,
    user_id=_USER_ID,
    invitation_id=_INV_ID,
    invitation_token="tok",
    invitation_link=(
        "https://app.example.com/invite?org=Acme+Corp"
        "&user_email=u%40x.com&token=tok"
    ),
)


class TestInviteProductUserUseCase:
    async def test_delegates_to_create_invited_user_use_case(self):
        mock_create = MagicMock()
        mock_create.execute = AsyncMock(return_value=_RESULT)

        use_case = InviteProductUserUseCase(create_invited_user=mock_create)
        result = await use_case.execute(**_ARGS)

        assert result.invitation_token == "tok"
        assert result.invitation_link == (
            "https://app.example.com/invite?org=Acme+Corp"
            "&user_email=u%40x.com&token=tok"
        )
        mock_create.execute.assert_awaited_once()

    async def test_passes_correct_command_fields(self):
        mock_create = MagicMock()
        mock_create.execute = AsyncMock(return_value=_RESULT)

        use_case = InviteProductUserUseCase(create_invited_user=mock_create)
        await use_case.execute(**_ARGS)

        command = mock_create.execute.call_args[0][0]
        assert command.email == "u@x.com"
        assert command.department_name == "Emergency Department"
        assert command.first_name == "Ada"
        assert command.last_name == "Lovelace"
        assert command.description == "desc"


class TestProvider:
    def test_provider_builds_use_case(self):
        mock_create = MagicMock()
        use_case = get_invite_product_user_use_case(create_invited_user=mock_create)
        assert isinstance(use_case, InviteProductUserUseCase)
