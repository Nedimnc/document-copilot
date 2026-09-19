from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.auth.dependencies import get_current_user
from app.auth.user import CurrentUser

router = APIRouter(prefix="/auth", tags=["auth"])


class MeResponse(BaseModel):
    id: UUID
    email: str


@router.get("/me")
async def me(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> MeResponse:
    return MeResponse(id=current_user.id, email=current_user.email)
