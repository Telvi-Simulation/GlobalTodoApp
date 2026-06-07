from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import IntegrityError
from app.db.session import db_session
from app.models.onboarding import UserOnboardingData
from app.schemas.onboarding import OnboardRequest
from app.api.permissions import verify_user_tenant_access
from app.audit import log_audit_event
import uuid

bp = Blueprint("onboarding", __name__, url_prefix="/api")

@bp.route("/onboard", methods=["POST"])
@jwt_required()
def post_onboard():
    current_user_id = get_jwt_identity()
    try:
        json_data = request.get_json(force=True)
    except Exception:
        return jsonify({"error": "Malformed JSON"}), 400

    # Validate input schema
    try:
        payload = OnboardRequest.parse_obj(json_data)
    except Exception as e:
        return jsonify({"error": "Validation failed", "details": str(e)}), 400

    # Security check: user can only onboard self and within their tenant
    if str(payload.user_id) != current_user_id:
        return jsonify({"error": "Unauthorized user_id"}), 403
    if not verify_user_tenant_access(current_user_id, str(payload.tenant_id)):
        return jsonify({"error": "User not authorized for tenant"}), 403

    # Check user active and role (assumed implemented in verify_user_tenant_access)
    # Upsert onboarding data
    try:
        with db_session() as session:
            existing = session.query(UserOnboardingData).filter_by(user_id=payload.user_id).one_or_none()
            if existing:
                existing.full_name = payload.full_name
                existing.email = payload.email
                existing.initial_site_name = payload.initial_site_name
                existing.consent_marketing = payload.consent_marketing
                existing.consent_terms = payload.consent_terms
            else:
                record = UserOnboardingData(
                    user_id=payload.user_id,
                    tenant_id=payload.tenant_id,
                    full_name=payload.full_name,
                    email=payload.email,
                    initial_site_name=payload.initial_site_name,
                    consent_marketing=payload.consent_marketing,
                    consent_terms=payload.consent_terms,
                )
                session.add(record)
            session.flush()
            onboarding_id = existing.id if existing else record.id
            session.commit()
    except IntegrityError:
        return jsonify({"error": "Foreign key constraint failure or duplicate"}), 400
    except Exception:
        return jsonify({"error": "Internal server error"}), 500

    # Audit log without PII
    log_audit_event(
        user_id=current_user_id,
        tenant_id=str(payload.tenant_id),
        action="user_onboard",
        resource_id=str(onboarding_id),
        metadata={
            "consent_terms": payload.consent_terms,
            "consent_marketing": payload.consent_marketing,
        },
    )

    return (
        jsonify(
            {
                "onboarding_id": str(onboarding_id),
                "message": "Onboarding data saved successfully",
            }
        ),
        201,
    )
