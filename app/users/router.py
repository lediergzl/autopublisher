from fastapi import APIRouter, Depends
from app.core.deps import get_current_user
from app.users.models import User
from app.users.schemas import UserOut

router = APIRouter(tags=["users"])


@router.get("/me", response_model=UserOut)
async def get_me(user: User = Depends(get_current_user)):
    return user
