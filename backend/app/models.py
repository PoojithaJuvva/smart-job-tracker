import uuid
from datetime import datetime, date
from app.extensions import db, bcrypt


def gen_uuid():
    return str(uuid.uuid4())


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    applications = db.relationship(
        "Application", backref="owner", lazy="dynamic", cascade="all, delete-orphan"
    )

    def set_password(self, raw_password):
        self.password_hash = bcrypt.generate_password_hash(raw_password).decode("utf-8")

    def check_password(self, raw_password):
        return bcrypt.check_password_hash(self.password_hash, raw_password)

    def to_dict(self):
        return {"id": self.id, "name": self.name, "email": self.email}


VALID_STATUSES = [
    "Wishlist",
    "Applied",
    "OA_Scheduled",
    "Interview",
    "Offer",
    "Rejected",
    "Withdrawn",
]


class Application(db.Model):
    __tablename__ = "applications"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, index=True)

    company = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(150), nullable=False)
    status = db.Column(db.String(30), nullable=False, default="Applied", index=True)
    job_link = db.Column(db.String(500))
    location = db.Column(db.String(150))
    salary_range = db.Column(db.String(100))
    applied_date = db.Column(db.Date, default=date.today)
    interview_date = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    history = db.relationship(
        "StatusHistory",
        backref="application",
        lazy="dynamic",
        cascade="all, delete-orphan",
        order_by="StatusHistory.changed_at",
    )

    def to_dict(self, include_history=False):
        data = {
            "id": self.id,
            "company": self.company,
            "role": self.role,
            "status": self.status,
            "job_link": self.job_link,
            "location": self.location,
            "salary_range": self.salary_range,
            "applied_date": self.applied_date.isoformat() if self.applied_date else None,
            "interview_date": self.interview_date.isoformat() if self.interview_date else None,
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
        if include_history:
            data["history"] = [h.to_dict() for h in self.history]
        return data


class StatusHistory(db.Model):
    __tablename__ = "status_history"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    application_id = db.Column(db.String(36), db.ForeignKey("applications.id"), nullable=False)
    from_status = db.Column(db.String(30))
    to_status = db.Column(db.String(30), nullable=False)
    changed_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "from_status": self.from_status,
            "to_status": self.to_status,
            "changed_at": self.changed_at.isoformat(),
        }
