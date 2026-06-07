import json
import pytest
from app.models.onboarding import UserOnboardingData
from app.db.session import db_session
from app.api.onboarding import bp as onboarding_bp
from flask import Flask
from uuid import uuid4

@pytest.fixture
def app():
    app = Flask(__name__)
    app.register_blueprint(onboarding_bp)
    app.config["TESTING"] = True
    app.config["JWT_SECRET_KEY"] = "test-secret"
    from flask_jwt_extended import JWTManager
    JWTManager(app)
    yield app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def auth_headers(app):
    # Create JWT token for user_id
    from flask_jwt_extended import create_access_token
    user_id = str(uuid4())
    token = create_access_token(identity=user_id)
    return {"Authorization": f"Bearer {token}"}, user_id

def test_post_onboard_success(client, auth_headers):
    headers, user_id = auth_headers
    tenant_id = str(uuid4())
    payload = {
        "user_id": user_id,
        "tenant_id": tenant_id,
        "full_name": "Test User",
        "email": "test@example.com",
        "initial_site_name": "My Palette Site",
        "consent_marketing": True,
        "consent_terms": True
    }
    response = client.post("/api/onboard", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.get_json()
    assert "onboarding_id" in data
    assert data["message"] == "Onboarding data saved successfully"
    # Verify DB record
    with db_session() as session:
        record = session.query(UserOnboardingData).filter_by(user_id=user_id).one_or_none()
        assert record is not None
        assert record.full_name == "Test User"
        assert record.email == "test@example.com"
        assert record.initial_site_name == "My Palette Site"
        assert record.consent_marketing is True
        assert record.consent_terms is True

def test_post_onboard_missing_required_field(client, auth_headers):
    headers, user_id = auth_headers
    tenant_id = str(uuid4())
    payload = {
        "user_id": user_id,
        "tenant_id": tenant_id,
        "email": "test@example.com",
        "initial_site_name": "Site",
        "consent_terms": True
    }
    # Missing full_name
    response = client.post("/api/onboard", json=payload, headers=headers)
    assert response.status_code == 400
    assert "Validation failed" in response.get_data(as_text=True)

def test_post_onboard_invalid_email(client, auth_headers):
    headers, user_id = auth_headers
    tenant_id = str(uuid4())
    payload = {
        "user_id": user_id,
        "tenant_id": tenant_id,
        "full_name": "User",
        "email": "not-an-email",
        "initial_site_name": "Site",
        "consent_terms": True
    }
    response = client.post("/api/onboard", json=payload, headers=headers)
    assert response.status_code == 400

def test_post_onboard_unauthorized_user(client, auth_headers):
    headers, user_id = auth_headers
    tenant_id = str(uuid4())
    payload = {
        "user_id": str(uuid4()),  # different user id
        "tenant_id": tenant_id,
        "full_name": "User",
        "email": "test@example.com",
        "initial_site_name": "Site",
        "consent_terms": True
    }
    response = client.post("/api/onboard", json=payload, headers=headers)
    assert response.status_code == 403

def test_post_onboard_malformed_json(client, auth_headers):
    headers, _ = auth_headers
    response = client.post("/api/onboard", data="not-json", headers=headers)
    assert response.status_code == 400
    assert "Malformed JSON" in response.get_data(as_text=True)
