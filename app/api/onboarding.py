import json
import logging
import time
import uuid
from typing import Optional

from flask import Blueprint, request, jsonify, g
from pydantic import BaseModel, ValidationError, constr, EmailStr, validator

from app.utils.logger import get_logger
from app.auth import require_authentication

onboarding_bp = Blueprint("onboarding", __name__)

# Allowed enums matching frontend options
WEBSITE_PURPOSE_OPTIONS = {"Portfolio", "E-commerce", "Blog", "Other"}
DESIGN_STYLE_OPTIONS = {"Modern", "Minimalist", "Professional"}

# Regex for fullName: letters (incl accented), spaces, hyphens, apostrophes, 1-50 chars
FULLNAME_REGEX = r"^[A-Za-zÀ-ÖØ-öø-ÿ \-']{1,50}$"


class OnboardingPayload(BaseModel):
    fullName: constr(min_length=1, max_length=50, regex=FULLNAME_REGEX)
    email: EmailStr
    websitePurpose: constr(strict=True)
    designStyle: constr(strict=True)
    additionalNotes: Optional[constr(max_length=500)] = ""

    @validator("websitePurpose")
    def website_purpose_must_be_valid(cls, v):
        if v not in WEBSITE_PURPOSE_OPTIONS:
            raise ValueError("Invalid website purpose selected.")
        return v

    @validator("designStyle")
    def design_style_must_be_valid(cls, v):
        if v not in DESIGN_STYLE_OPTIONS:
            raise ValueError("Invalid design style selected.")
        return v


logger = get_logger("onboarding")


@onboarding_bp.before_request
@require_authentication
def before_request():
    # Extract or generate request ID for trace correlation
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    g.request_id = request_id


@onboarding_bp.route("/onboard", methods=["POST"])
def onboard():
    start_time = time.time()
    request_id = getattr(g, "request_id", str(uuid.uuid4()))
    try:
        if not request.is_json:
            msg = "Request payload must be JSON."
            logger.warning(
                json.dumps(
                    {
                        "level": "WARN",
                        "requestId": request_id,
                        "message": msg,
                        "context": {},
                    }
                )
            )
            return (
                jsonify(error="InvalidRequest", details=msg),
                400,
                {"Content-Type": "application/json"},
            )

        payload_raw = request.get_json()
        try:
            payload = OnboardingPayload(**payload_raw)
        except ValidationError as ve:
            errors = {}
            for err in ve.errors():
                loc = ".".join(str(l) for l in err["loc"])
                errors[loc] = err["msg"]

            logger.warning(
                json.dumps(
                    {
                        "level": "WARN",
                        "requestId": request_id,
                        "message": "Validation failed for onboarding payload",
                        "context": {"fieldErrors": errors},
                    }
                )
            )
            return jsonify(error="ValidationError", details=errors), 400

        # At this point, payload is validated and sanitized by pydantic
        # Here you would typically process or store the onboarding data,
        # e.g. enqueue for AI-driven site generation, persist metadata, etc.
        # For this task, we simulate success response.

        duration_ms = int((time.time() - start_time) * 1000)
        logger.info(
            json.dumps(
                {
                    "level": "INFO",
                    "requestId": request_id,
                    "message": "Onboarding payload accepted",
                    "context": {
                        "websitePurpose": payload.websitePurpose,
                        "designStyle": payload.designStyle,
                        "additionalNotesLength": len(payload.additionalNotes or ""),
                        "processingTimeMs": duration_ms,
                    },
                }
            )
        )
        return jsonify(message="Onboarding data accepted"), 200

    except Exception as exc:
        logger.error(
            json.dumps(
                {
                    "level": "ERROR",
                    "requestId": request_id,
                    "message": "Unexpected error in onboarding endpoint",
                    "context": {"exception": str(exc)},
                }
            ),
            exc_info=True,
        )
        return (
            jsonify(error="InternalServerError", details="An unexpected error occurred."),
            500,
            {"Content-Type": "application/json"},
        )
