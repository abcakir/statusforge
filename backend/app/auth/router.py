from fastapi import APIRouter, Depends

from app.auth.dependencies import get_current_user
from app.users.schemas import UserRead

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me", response_model=UserRead)
async def get_me(user=Depends(get_current_user)):
    return user
