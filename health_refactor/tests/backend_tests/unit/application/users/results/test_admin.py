"""Unit tests: application/users/results/admin.py"""
from uuid import uuid4

from backend.src.application.users.results.admin import CreateInvitedUserFromAdminResult


def test_create_invited_user_result_holds_ids_and_links() -> None:
    dept_id = uuid4()
    user_id = uuid4()
    invitation_id = uuid4()

    result = CreateInvitedUserFromAdminResult(
        department_id=dept_id,
        user_id=user_id,
        invitation_id=invitation_id,
        invitation_token="tok",
        invitation_link=(
            "http://localhost:3000/invite?dept=Acme+Corp"
            "&user_email=admin%40example.com&token=tok"
        ),
    )

    assert result.department_id == dept_id
    assert result.invitation_token == "tok"
    assert "/invite?" in result.invitation_link
    assert "dept=Acme+Corp" in result.invitation_link
    assert "token=tok" in result.invitation_link
