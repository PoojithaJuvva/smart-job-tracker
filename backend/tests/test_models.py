from app.models import User, Application


def test_password_is_hashed_not_stored_plain():
    user = User(name="Test", email="test@example.com")
    user.set_password("SecurePass123")
    assert user.password_hash != "SecurePass123"
    assert user.check_password("SecurePass123") is True
    assert user.check_password("WrongPassword") is False


def test_user_to_dict_excludes_password():
    user = User(name="Test", email="test@example.com")
    user.set_password("SecurePass123")
    data = user.to_dict()
    assert "password" not in data
    assert "password_hash" not in data


def test_application_to_dict_shape(app):
    from app.extensions import db as _db

    application = Application(
        user_id="u1", company="Amazon", role="SDE", status="Applied"
    )
    _db.session.add(application)
    _db.session.commit()

    data = application.to_dict()
    assert data["company"] == "Amazon"
    assert data["role"] == "SDE"
    assert "history" not in data
