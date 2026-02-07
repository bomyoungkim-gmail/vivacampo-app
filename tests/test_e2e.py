import pytest
import requests
import time

API_BASE = "http://localhost:8000"
SESSION = requests.Session()

class TestE2EFlow:
    """End-to-end test for complete user flow"""
    
    def test_01_health_check(self):
        """Test API health check"""
        response = SESSION.get(f"{API_BASE}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_02_oidc_login(self, oidc_id_token):
        """Test OIDC login flow"""
        response = SESSION.post(
            f"{API_BASE}/v1/auth/oidc/login",
            json={
                "provider": "local",
                "id_token": oidc_id_token
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "identity" in data
        assert "workspaces" in data
        
        # Store for next tests
        pytest.identity = data["identity"]
        pytest.workspaces = data["workspaces"]
        pytest.access_token = data.get("access_token")
    
    def test_03_workspace_switch(self):
        """Test workspace switch"""
        if not getattr(pytest, "workspaces", None):
            pytest.skip("No workspaces available")
        if not getattr(pytest, "access_token", None):
            pytest.skip("No access token from OIDC login")
        
        workspace = pytest.workspaces[0]
        response = SESSION.post(
            f"{API_BASE}/v1/auth/workspaces/switch",
            headers={"Authorization": f"Bearer {pytest.access_token}"},
            json={"tenant_id": workspace["tenant_id"]}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        
        pytest.access_token = data["access_token"]
        pytest.tenant_id = workspace["tenant_id"]
    
    def test_04_create_farm(self):
        """Test farm creation"""
        if not hasattr(pytest, "access_token"):
            pytest.skip("No access token")
        
        response = SESSION.post(
            f"{API_BASE}/v1/app/farms",
            headers={"Authorization": f"Bearer {pytest.access_token}"},
            json={
                "name": "Fazenda Teste E2E",
                "timezone": "America/Sao_Paulo"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Fazenda Teste E2E"
        
        pytest.farm_id = data["id"]
    
    def test_05_list_farms(self):
        """Test listing farms"""
        if not hasattr(pytest, "access_token"):
            pytest.skip("No access token")
        
        response = SESSION.get(
            f"{API_BASE}/v1/app/farms",
            headers={"Authorization": f"Bearer {pytest.access_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_06_list_signals(self):
        """Test listing signals"""
        if not hasattr(pytest, "access_token"):
            pytest.skip("No access token")
        
        response = SESSION.get(
            f"{API_BASE}/v1/app/signals",
            headers={"Authorization": f"Bearer {pytest.access_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_07_create_ai_thread(self):
        """Test AI assistant thread creation"""
        if not hasattr(pytest, "access_token"):
            pytest.skip("No access token")
        
        response = SESSION.post(
            f"{API_BASE}/v1/app/ai-assistant/threads",
            headers={"Authorization": f"Bearer {pytest.access_token}"},
            json={"provider": "openai"}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["provider"] == "openai"
        
        pytest.thread_id = data["id"]
    
    def test_08_list_ai_threads(self):
        """Test listing AI threads"""
        if not hasattr(pytest, "access_token"):
            pytest.skip("No access token")
        
        response = SESSION.get(
            f"{API_BASE}/v1/app/ai-assistant/threads",
            headers={"Authorization": f"Bearer {pytest.access_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestIntegration:
    """Integration tests for API endpoints"""
    
    def test_metrics_endpoint(self):
        """Test Prometheus metrics"""
        response = SESSION.get(f"{API_BASE}/metrics")
        assert response.status_code == 200
        assert "vivacampo" in response.text
    
    def test_docs_endpoint(self):
        """Test OpenAPI docs"""
        response = SESSION.get(f"{API_BASE}/docs")
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
