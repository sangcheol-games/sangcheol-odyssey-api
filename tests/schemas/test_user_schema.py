import uuid
from datetime import datetime, timezone
from app.schemas.user import UserCreate, UserUpdate, UserOut


def test_user_create_schema():
    user = UserCreate(uid="user1", nickname="nick")
    assert user.uid == "user1"
    assert user.nickname == "nick"


def test_user_update_schema():
    user = UserUpdate(nickname="new")
    assert user.nickname == "new"


def test_user_out_schema():
    data = {
        "id": uuid.uuid4(),
        "uid": "user1",
        "nickname": None,
        "created_at": datetime.now(timezone.utc),
        "updated_at": None,
        "last_login_at": None,
    }
    user = UserOut(**data)
    assert user.id == data["id"]
    assert user.created_at == data["created_at"]
    assert user.nickname is None
