"""Endpoint: decline a pending invitation."""
from fastapi import APIRouter, Depends, status

from backend.src.application.invitations.commands.decline import DeclineInvitationCommand
from backend.src.application.invitations.dependencies import get_decline_invitation
from backend.src.application.invitations.use_cases.decline_invitation import DeclineInvitation
from backend.src.presentation.api.v1.invitations.schemas import DeclineInvitationResponse
from backend.src.presentation.openapi import envelope_responses
from backend.src.presentation.schemas.api_response import ApiResponse, success

router = APIRouter()


@router.post(
    "/{token}/decline",
    summary="Decline invitation",
    description="Marks the invitation and invited user as declined; idempotent if already declined.",
    response_model=ApiResponse[DeclineInvitationResponse],
    status_code=status.HTTP_200_OK,
    responses=envelope_responses(
        DeclineInvitationResponse,
        success_message="Invitation declined",
        errors=(),
    ),
)
async def decline_invitation(
    token: str,
    use_case: DeclineInvitation = Depends(get_decline_invitation),
) -> ApiResponse[DeclineInvitationResponse]:
    result = await use_case.execute(DeclineInvitationCommand(invitation_token=token))
    return success(
        DeclineInvitationResponse.model_validate(result),
        message="Invitation declined",
        status_code=status.HTTP_200_OK,
    )
