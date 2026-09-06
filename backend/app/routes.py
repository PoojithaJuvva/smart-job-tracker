import csv
import io
from datetime import datetime

from flask import Blueprint, request, jsonify, Response, current_app
from marshmallow import ValidationError
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.extensions import db
from app.models import Application, StatusHistory, VALID_STATUSES
from app.schemas import ApplicationSchema, ApplicationUpdateSchema

apps_bp = Blueprint("applications", __name__, url_prefix="/api/applications")

create_schema = ApplicationSchema()
update_schema = ApplicationUpdateSchema()


def _owned_query():
    user_id = get_jwt_identity()
    return Application.query.filter_by(user_id=user_id)


@apps_bp.get("")
@jwt_required()
def list_applications():
    """List applications for the current user with search, filter, sort, pagination."""
    query = _owned_query()

    status = request.args.get("status")
    if status:
        if status not in VALID_STATUSES:
            return jsonify({"error": f"Invalid status filter '{status}'."}), 400
        query = query.filter(Application.status == status)

    search = request.args.get("q")
    if search:
        like = f"%{search}%"
        query = query.filter(
            db.or_(Application.company.ilike(like), Application.role.ilike(like))
        )

    sort = request.args.get("sort", "-created_at")
    sort_column_name = sort.lstrip("-")
    sort_column = getattr(Application, sort_column_name, Application.created_at)
    query = query.order_by(sort_column.desc() if sort.startswith("-") else sort_column.asc())

    page = max(request.args.get("page", 1, type=int), 1)
    per_page = min(
        request.args.get("per_page", current_app.config["PAGE_SIZE_DEFAULT"], type=int),
        current_app.config["PAGE_SIZE_MAX"],
    )

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify(
        {
            "items": [a.to_dict() for a in pagination.items],
            "page": pagination.page,
            "per_page": per_page,
            "total": pagination.total,
            "total_pages": pagination.pages,
        }
    )


@apps_bp.post("")
@jwt_required()
def create_application():
    payload = request.get_json(silent=True) or {}
    try:
        data = create_schema.load(payload)
    except ValidationError as err:
        return jsonify({"errors": err.messages}), 422

    application = Application(user_id=get_jwt_identity(), **data)
    db.session.add(application)
    db.session.flush()

    db.session.add(
        StatusHistory(application_id=application.id, from_status=None, to_status=application.status)
    )
    db.session.commit()
    return jsonify(application.to_dict()), 201


@apps_bp.get("/<string:application_id>")
@jwt_required()
def get_application(application_id):
    application = _owned_query().filter_by(id=application_id).first()
    if not application:
        return jsonify({"error": "Application not found."}), 404
    return jsonify(application.to_dict(include_history=True))


@apps_bp.put("/<string:application_id>")
@jwt_required()
def update_application(application_id):
    application = _owned_query().filter_by(id=application_id).first()
    if not application:
        return jsonify({"error": "Application not found."}), 404

    payload = request.get_json(silent=True) or {}
    try:
        data = update_schema.load(payload, partial=True)
    except ValidationError as err:
        return jsonify({"errors": err.messages}), 422

    old_status = application.status
    for field, value in data.items():
        setattr(application, field, value)

    if "status" in data and data["status"] != old_status:
        db.session.add(
            StatusHistory(
                application_id=application.id, from_status=old_status, to_status=data["status"]
            )
        )

    db.session.commit()
    return jsonify(application.to_dict())


@apps_bp.delete("/<string:application_id>")
@jwt_required()
def delete_application(application_id):
    application = _owned_query().filter_by(id=application_id).first()
    if not application:
        return jsonify({"error": "Application not found."}), 404

    db.session.delete(application)
    db.session.commit()
    return "", 204


@apps_bp.get("/analytics/summary")
@jwt_required()
def analytics_summary():
    applications = _owned_query().all()
    total = len(applications)
    by_status = {status: 0 for status in VALID_STATUSES}
    for a in applications:
        by_status[a.status] = by_status.get(a.status, 0) + 1

    interviewed_or_beyond = sum(
        by_status.get(s, 0) for s in ["Interview", "Offer", "Rejected", "OA_Scheduled"]
    )
    response_rate = round((interviewed_or_beyond / total) * 100, 1) if total else 0.0
    offer_rate = round((by_status.get("Offer", 0) / total) * 100, 1) if total else 0.0

    upcoming = sorted(
        [
            a
            for a in applications
            if a.interview_date and a.interview_date >= datetime.utcnow()
        ],
        key=lambda a: a.interview_date,
    )[:5]

    return jsonify(
        {
            "total_applications": total,
            "by_status": by_status,
            "response_rate_percent": response_rate,
            "offer_rate_percent": offer_rate,
            "upcoming_interviews": [a.to_dict() for a in upcoming],
        }
    )


@apps_bp.get("/export/csv")
@jwt_required()
def export_csv():
    applications = _owned_query().order_by(Application.created_at.desc()).all()

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        ["Company", "Role", "Status", "Applied Date", "Interview Date", "Location", "Salary Range", "Job Link", "Notes"]
    )
    for a in applications:
        writer.writerow(
            [
                a.company,
                a.role,
                a.status,
                a.applied_date.isoformat() if a.applied_date else "",
                a.interview_date.isoformat() if a.interview_date else "",
                a.location or "",
                a.salary_range or "",
                a.job_link or "",
                (a.notes or "").replace("\n", " "),
            ]
        )

    return Response(
        buffer.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=job_applications.csv"},
    )
