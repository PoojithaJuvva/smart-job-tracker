from marshmallow import Schema, fields, validate, validates, ValidationError
from app.models import VALID_STATUSES


class RegisterSchema(Schema):
    name = fields.String(required=True, validate=validate.Length(min=1, max=120))
    email = fields.Email(required=True)
    password = fields.String(required=True, validate=validate.Length(min=6, max=128))


class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.String(required=True)


class ApplicationSchema(Schema):
    company = fields.String(required=True, validate=validate.Length(min=1, max=150))
    role = fields.String(required=True, validate=validate.Length(min=1, max=150))
    status = fields.String(validate=validate.OneOf(VALID_STATUSES), load_default="Applied")
    job_link = fields.String(required=False, allow_none=True, validate=validate.Length(max=500))
    location = fields.String(required=False, allow_none=True, validate=validate.Length(max=150))
    salary_range = fields.String(required=False, allow_none=True, validate=validate.Length(max=100))
    applied_date = fields.Date(required=False, allow_none=True)
    interview_date = fields.DateTime(required=False, allow_none=True)
    notes = fields.String(required=False, allow_none=True)


class ApplicationUpdateSchema(ApplicationSchema):
    company = fields.String(required=False, validate=validate.Length(min=1, max=150))
    role = fields.String(required=False, validate=validate.Length(min=1, max=150))
