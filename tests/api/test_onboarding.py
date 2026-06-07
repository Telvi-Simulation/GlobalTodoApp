import json
import threading
import time
import pytest
from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token
from uuid import uuid4
from app.api.onboarding import bp as onboarding_bp
from app.db.session import db_session
from app.models.onboarding import UserOnboardingData
from app.audit import AuditLogger

@pytest.fixture
def app():
    app = Flask(__name__)
    app.register_blueprint(onboarding_bp)
    app.config["TESTING"] = True
    app.config["JWT_SECRET_KEY"] = "test-secret"
    JWTManager(app)
    yield app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def auth_headers(app):
    user_id = str(uuid4())
    token = create_access_token(identity=user_id)
    return {"Authorization": f"Bearer {token}"}, user_id

@pytest.fixture(autouse=True)
def clean_db():
    # Cleanup onboarding data before each test
    with db_session() as session:
        session.query(UserOnboardingData).delete()
        session.commit()
    yield

@pytest.fixture
def audit_log_mock(mocker):
    # Patch audit logger to capture events
    mock = mocker.patch.object(AuditLogger, "log_event", autospec=True)
    yield mock

def test_onboard_success_persists_data(client, auth_headers, audit_log_mock):
    headers, user_id = auth_headers
    tenant_id = str(uuid4())
    payload = {
        "user_id": user_id,
        "tenant_id": tenant_id,
        "full_name": "Test User",
        "email": "user@example.com",
        "initial_site_name": "Palette Site",
        "consent_marketing": True,
        "consent_terms": True,
    }
    res = client.post("/api/onboard", json=payload, headers=headers)
    assert res.status_code == 201
    data = res.get_json()
    assert "onboarding_id" in data
    assert data["message"] == "Onboarding data saved successfully"

    with db_session() as session:
        record = session.query(UserOnboardingData).filter_by(user_id=user_id).one_or_none()
        assert record is not None
        assert record.email == "user@example.com"
        assert record.consent_terms is True

    audit_log_mock.assert_called()
    call_args = audit_log_mock.call_args[0][1]
    assert call_args["action"] == "user_onboard"
    assert "consent_terms" in call_args["metadata"]
    # Confirm no PII in audit metadata
    assert "email" not in call_args["metadata"]

def test_onboard_missing_required_field_returns_400(client, auth_headers):
    headers, user_id = auth_headers
    tenant_id = str(uuid4())
    payload = {
        # missing full_name
        "user_id": user_id,
        "tenant_id": tenant_id,
        "email": "test@example.com",
        "initial_site_name": "Site",
        "consent_terms": True,
    }
    res = client.post("/api/onboard", json=payload, headers=headers)
    assert res.status_code == 400
    assert "Validation failed" in res.get_data(as_text=True)

def test_onboard_invalid_email_returns_400(client, auth_headers):
    headers, user_id = auth_headers
    tenant_id = str(uuid4())
    payload = {
        "user_id": user_id,
        "tenant_id": tenant_id,
        "full_name": "User",
        "email": "invalid-email",
        "initial_site_name": "Site",
        "consent_terms": True,
    }
    res = client.post("/api/onboard", json=payload, headers=headers)
    assert res.status_code == 400
    assert "Validation failed" in res.get_data(as_text=True)

def test_onboard_unauthorized_user_id_returns_403(client, auth_headers):
    headers, _ = auth_headers
    tenant_id = str(uuid4())
    payload = {
        "user_id": str(uuid4()),  # different user
        "tenant_id": tenant_id,
        "full_name": "User",
        "email": "test@example.com",
        "initial_site_name": "Site",
        "consent_terms": True,
    }
    res = client.post("/api/onboard", json=payload, headers=headers)
    assert res.status_code == 403
    assert "Unauthorized user_id" in res.get_data(as_text=True)

def test_onboard_user_no_tenant_access_returns_403(client, auth_headers, mocker):
    headers, user_id = auth_headers
    tenant_id = str(uuid4())
    # Patch tenant access check to return False
    mocker.patch("app.api.permissions.verify_user_tenant_access", return_value=False)
    payload = {
        "user_id": user_id,
        "tenant_id": tenant_id,
        "full_name": "User",
        "email": "test@example.com",
        "initial_site_name": "Site",
        "consent_terms": True,
    }
    res = client.post("/api/onboard", json=payload, headers=headers)
    assert res.status_code == 403
    assert "User not authorized for tenant" in res.get_data(as_text=True)

def test_onboard_malformed_json_returns_400(client, auth_headers):
    headers, _ = auth_headers
    res = client.post("/api/onboard", data="not-json", headers=headers)
    assert res.status_code == 400
    assert "Malformed JSON" in res.get_data(as_text=True)

def test_onboard_concurrent_requests(client, auth_headers):
    headers, user_id = auth_headers
    tenant_id = str(uuid4())
    payload1 = {
        "user_id": user_id,
        "tenant_id": tenant_id,
        "full_name": "User One",
        "email": "one@example.com",
        "initial_site_name": "Site One",
        "consent_terms": True,
    }
    payload2 = {
        "user_id": user_id,
        "tenant_id": tenant_id,
        "full_name": "User Two",
        "email": "two@example.com",
        "initial_site_name": "Site Two",
        "consent_terms": True,
    }
    results = []

    def post_payload(payload):
        res = client.post("/api/onboard", json=payload, headers=headers)
        results.append(res.status_code)

    threads = [
        threading.Thread(target=post_payload, args=(payload1,)),
        threading.Thread(target=post_payload, args=(payload2,)),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert all(r == 201 for r in results)
    with db_session() as session:
        record = session.query(UserOnboardingData).filter_by(user_id=user_id).one_or_none()
        assert record is not None
        # The last write wins, check full_name is one of the two
        assert record.full_name in ["User One", "User Two"]

def test_onboard_rejects_extra_fields(client, auth_headers):
    headers, user_id = auth_headers
    tenant_id = str(uuid4())
    payload = {
        "user_id": user_id,
        "tenant_id": tenant_id,
        "full_name": "User",
        "email": "user@example.com",
        "initial_site_name": "Site",
        "consent_terms": True,
        "unexpected_field": "should fail",
    }
    res = client.post("/api/onboard", json=payload, headers=headers)
    assert res.status_code == 400
    assert "extra fields" in res.get_data(as_text=True).lower()

def test_onboard_rejects_false_consent_terms(client, auth_headers):
    headers, user_id = auth_headers
    tenant_id = str(uuid4())
    payload = {
        "user_id": user_id,
        "tenant_id": tenant_id,
        "full_name": "User",
        "email": "user@example.com",
        "initial_site_name": "Site",
        "consent_terms": False,
    }
    res = client.post("/api/onboard", json=payload, headers=headers)
    assert res.status_code == 400
    assert "consent_terms must be true" in res.get_data(as_text=True)

def test_unauthenticated_request_returns_401(client):
    payload = {
        "user_id": str(uuid4()),
        "tenant_id": str(uuid4()),
        "full_name": "User",
        "email": "user@example.com",
        "initial_site_name": "Site",
        "consent_terms": True,
    }
    res = client.post("/api/onboard", json=payload)
    assert res.status_code == 401
    assert "Missing Authorization Header" in res.get_data(as_text=True)
