from flask import Blueprint, request, jsonify
from marshmallow import ValidationError
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
)

from app.extensions import db, limiter
from app.models import User
from app.schemas import RegisterSchema, LoginSchema

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

register_schema = RegisterSchema()
login_schema = LoginSchema()


@auth_bp.post("/register")
@limiter.limit("10 per minute")
def register():
    payload = request.get_json(silent=True) or {}
    try:
        data = register_schema.load(payload)
    except ValidationError as err:
        return jsonify({"errors": err.messages}), 422

    if User.query.filter_by(email=data["email"].lower()).first():
        return jsonify({"error": "An account with this email already exists."}), 409

    user = User(name=data["name"], email=data["email"].lower())
    user.set_password(data["password"])
    db.session.add(user)
    db.session.commit()

    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)
    return (
        jsonify(
            {
                "user": user.to_dict(),
                "access_token": access_token,
                "refresh_token": refresh_token,
            }
        ),
        201,
    )


@auth_bp.post("/login")
@limiter.limit("15 per minute")
def login():
    payload = request.get_json(silent=True) or {}
    try:
        data = login_schema.load(payload)
    except ValidationError as err:
        return jsonify({"errors": err.messages}), 422

    user = User.query.filter_by(email=data["email"].lower()).first()
    if not user or not user.check_password(data["password"]):
        return jsonify({"error": "Invalid email or password."}), 401

    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)
    return jsonify(
        {
            "user": user.to_dict(),
            "access_token": access_token,
            "refresh_token": refresh_token,
        }
    )


@auth_bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    return jsonify({"access_token": create_access_token(identity=identity)})


@auth_bp.get("/me")
@jwt_required()
def me():
    user = User.query.get_or_404(get_jwt_identity())
    return jsonify(user.to_dict())
