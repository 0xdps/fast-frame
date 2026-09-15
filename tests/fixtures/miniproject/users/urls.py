from fastapi import APIRouter

from users.models import User

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/{user_id}")
def get_user(user_id: int) -> dict[str, object]:
    """Get user by ID. DoesNotExist is auto-converted to 404 by framework."""
    user = User.objects.get(id=user_id)
    return {"id": user.id, "email": user.email, "is_active": user.is_active}
