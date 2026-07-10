def test_health_check(client) -> None:
    """
    Ensures the health status endpoint responds correctly.
    """
    response = client.get("/api/v1/system/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "version" in data
    assert "environment" in data
    assert "uptime" in data
    assert "database_connectivity" in data
    assert "gemini_configuration" in data
    assert "supabase_connectivity" in data
    assert "timestamp" in data


def test_version_info(client) -> None:
    """
    Ensures version details are fetched correctly matching configuration constants.
    """
    response = client.get("/api/v1/system/version")
    assert response.status_code == 200
    data = response.json()
    assert "version" in data
    assert data["environment"] == "development"


def test_system_status(client) -> None:
    """
    Ensures dependencies connection indicator reports operational status in test environments.
    """
    response = client.get("/api/v1/system/status")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "services" in data
    assert "supabase" in data["services"]
    assert "gemini_api" in data["services"]


def test_performance_metrics(client) -> None:
    """
    Ensures performance endpoint aggregates runtimes and counts.
    """
    response = client.get("/api/v1/system/performance")
    assert response.status_code == 200
    data = response.json()
    assert "average_execution_time" in data
    assert "average_report_generation_time" in data
    assert "tool_execution_count" in data
    assert "agent_execution_count" in data
    assert "cache_hit_ratio" in data
    assert "average_confidence" in data
    assert "reports_generated" in data
    assert "content_generated" in data
    assert "research_sessions" in data
    assert "export_count" in data
