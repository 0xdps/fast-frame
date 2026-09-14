from fastapi import APIRouter, HTTPException

from fastframe.models.exceptions import DoesNotExist
from users.models import User

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/{user_id}")
def get_user(user_id: int) -> dict[str, object]:
    try:
        user = User.objects.get(id=user_id)
    except DoesNotExist as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"id": user.id, "email": user.email, "is_active": user.is_active}
