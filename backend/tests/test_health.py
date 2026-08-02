def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_all_module_status_routes_respond(client):
    modules = [
        "rag",
        "data-analyst",
        "research",
        "forecasting",
        "recommendations",
        "coding",
        "vision",
        "speech",
        "browser-agent",
        "finetune",
        "mlops",
        "image-gen",
        "video-gen",
        "distributed",
    ]
    for module in modules:
        response = client.get(f"/api/{module}/status")
        # Modules that got real routers no longer expose /status (404 is
        # fine); modules still on the stub router return 200.
        assert response.status_code in (200, 404), f"{module} returned {response.status_code}"
