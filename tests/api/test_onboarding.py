import json
import pytest
from app.api.onboarding import onboarding_bp, WEBSITE_PURPOSE_OPTIONS, DESIGN_STYLE_OPTIONS
from flask import Flask


@pytest.fixture
def client():
    app = Flask(__name__)
    app.register_blueprint(onboarding_bp)
    app.config["TESTING"] = True

    # Mock authentication decorator to pass for tests
    def fake_auth(f):
        def wrapper(*args, **kwargs):
            return f(*args, **kwargs)

        wrapper.__name__ = f.__name__
        return wrapper

    onboarding_bp.before_request_funcs = {None: [fake_auth]}

    with app.test_client() as client:
        yield client


valid_payload = {
    "fullName": "Anne-Marie O’Neill",
    "email": "user+tag@example.co.uk",
    "websitePurpose": "Portfolio",
    "designStyle": "Modern",
    "additionalNotes": "Looking forward to building my site.",
}


def test_onboard_success(client):
    resp = client.post("/onboard", json=valid_payload)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["message"] == "Onboarding data accepted"


@pytest.mark.parametrize(
    "payload, expected_status, expected_error_fields",
    [
        ({}, 400, {"fullName", "email", "websitePurpose", "designStyle"}),
        (
            {
                "fullName": "1234",
                "email": "bademail",
                "websitePurpose": "InvalidPurpose",
                "designStyle": "InvalidStyle",
                "additionalNotes": "a" * 501,
            },
            400,
            {"fullName", "email", "websitePurpose", "designStyle", "additionalNotes"},
        ),
        ({"fullName": "Valid Name", "email": "valid@example.com"}, 400, {"websitePurpose", "designStyle"}),
        ({"fullName": "Valid Name", "email": "valid@example.com", "websitePurpose": "Portfolio", "designStyle": "Modern", "additionalNotes": "a"*501}, 400, {"additionalNotes"}),
    ],
)
def test_onboard_validation_errors(client, payload, expected_status, expected_error_fields):
    resp = client.post("/onboard", json=payload)
    assert resp.status_code == expected_status
    data = resp.get_json()
    assert "error" in data and data["error"] == "ValidationError"
    assert set(data["details"].keys()) == expected_error_fields


def test_onboard_non_json_payload(client):
    resp = client.post("/onboard", data="plain text", content_type="text/plain")
    assert resp.status_code == 400
    data = resp.get_json()
    assert data["error"] == "InvalidRequest"


def test_onboard_extra_fields_ignored(client):
    payload = dict(valid_payload)
    payload["unexpectedField"] = "unexpected"
    resp = client.post("/onboard", json=payload)
    # Pydantic will ignore extra fields by default, so success expected
    assert resp.status_code == 200


def test_onboard_missing_auth(client):
    # Since we mocked auth to pass, simulate auth failure by patching decorator
    from app.api.onboarding import before_request

    def fail_auth():
        from flask import abort

        abort(401)

    onboarding_bp.before_request_funcs = {None: [fail_auth]}

    resp = client.post("/onboard", json=valid_payload)
    assert resp.status_code == 401


def test_onboard_unexpected_exception(monkeypatch, client):
    def raise_exc(*args, **kwargs):
        raise RuntimeError("Unexpected failure")

    monkeypatch.setattr("app.api.onboarding.OnboardingPayload", raise_exc)
    resp = client.post("/onboard", json=valid_payload)
    assert resp.status_code == 500
    data = resp.get_json()
    assert data["error"] == "InternalServerError"
