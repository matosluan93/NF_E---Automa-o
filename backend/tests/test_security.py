import base64

from app import create_app


def test_invoice_api_is_local_and_rejects_cross_origin(client):
    assert client.get("/api/notas").status_code == 200
    assert client.get("/api/notas?limit=-1&offset=bad").status_code == 200
    assert client.get("/api/nao-existe").status_code == 404
    assert client.get("/../requirements.txt").status_code == 404
    assert client.get("/api/notas", environ_overrides={"REMOTE_ADDR": "192.0.2.10"}).status_code == 403
    assert client.get("/api/notas", headers={"Host": "example.invalid"}).status_code == 403
    response = client.post("/api/notas", headers={"Origin": "https://example.invalid"}, json={})
    assert response.status_code == 403
    assert "Access-Control-Allow-Origin" not in response.headers
    assert response.headers["Cache-Control"] == "no-store"
    assert client.get("/api/health", environ_overrides={"REMOTE_ADDR": "192.0.2.10"}).status_code == 200


def test_remote_api_requires_configured_credentials(tmp_path):
    password = "synthetic-test-secret-only"
    application = create_app({
        "DB_PATH": str(tmp_path / "nfe.db"),
        "NFE_ACCESS_PASSWORD": password,
        "NFE_PUBLIC_ORIGIN": "https://nfe.example.invalid",
    })
    client = application.test_client()
    options = {"base_url": "https://nfe.example.invalid",
               "environ_overrides": {"REMOTE_ADDR": "192.0.2.10"}}
    rejected = client.get("/api/notas", **options)
    assert rejected.status_code == 401
    assert rejected.headers["WWW-Authenticate"].startswith("Basic ")
    credentials = base64.b64encode(f"nfe:{password}".encode()).decode()
    response = client.get("/api/notas", headers={"Authorization": f"Basic {credentials}"}, **options)
    assert response.status_code == 200
