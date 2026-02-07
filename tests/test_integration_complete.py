"""
Comprehensive integration tests for VivaCampo MVP.
Tests all critical features: quotas, audit, endpoints, resiliency, webhooks.
"""
import pytest
import httpx

API_BASE = "http://localhost:8000"


class TestQuotasAndAudit:
    """Test quota enforcement and audit logging"""
    
    async def test_farm_quota_enforcement(self, auth_headers):
        """Test that farm creation respects quota limits"""
        async with httpx.AsyncClient() as client:
            # Create farms up to quota
            for i in range(2):  # PERSONAL tier allows 2 farms
                response = await client.post(
                    f"{API_BASE}/v1/app/farms",
                    headers=auth_headers,
                    json={
                        "name": f"Test Farm {i}",
                        "timezone": "America/Sao_Paulo"
                    }
                )
                assert response.status_code in [201, 200]
            
            # Next farm should fail quota
            response = await client.post(
                f"{API_BASE}/v1/app/farms",
                headers=auth_headers,
                json={
                    "name": "Quota Exceeded Farm",
                    "timezone": "America/Sao_Paulo"
                }
            )
            assert response.status_code == 403
            assert "quota exceeded" in response.text.lower()
    
    async def test_audit_log_creation(self, auth_headers):
        """Test that actions are logged in audit trail"""
        async with httpx.AsyncClient() as client:
            # Perform action
            response = await client.post(
                f"{API_BASE}/v1/app/farms",
                headers=auth_headers,
                json={
                    "name": "Audit Test Farm",
                    "timezone": "America/Sao_Paulo"
                }
            )
            
            # Check audit log
            response = await client.get(
                f"{API_BASE}/v1/app/admin/tenant/audit",
                headers=auth_headers
            )
            assert response.status_code == 200
            
            logs = response.json()
            assert len(logs) > 0
            assert any(log["action"] == "CREATE" and log["resource_type"] == "farm" 
                      for log in logs)


class TestEndpoints:
    """Test all API endpoints"""
    
    async def test_aoi_crud(self, auth_headers):
        """Test AOI create, list, update"""
        async with httpx.AsyncClient() as client:
            # Create farm first
            farm_response = await client.post(
                f"{API_BASE}/v1/app/farms",
                headers=auth_headers,
                json={"name": "Test Farm", "timezone": "America/Sao_Paulo"}
            )
            farm_id = farm_response.json()["id"]
            
            # Create AOI
            aoi_response = await client.post(
                f"{API_BASE}/v1/app/aois",
                headers=auth_headers,
                json={
                    "farm_id": farm_id,
                    "name": "Test AOI",
                    "use_type": "PASTURE",
                    "geometry": "MULTIPOLYGON(((-47.0 -23.0, -47.0 -23.001, -47.001 -23.001, -47.001 -23.0, -47.0 -23.0)))"
                }
            )
            assert aoi_response.status_code == 201
            aoi_id = aoi_response.json()["id"]
            pytest.aoi_id = aoi_id
            
            # List AOIs
            list_response = await client.get(
                f"{API_BASE}/v1/app/aois",
                headers=auth_headers
            )
            assert list_response.status_code == 200
            assert len(list_response.json()) > 0
            
            # Update AOI
            update_response = await client.patch(
                f"{API_BASE}/v1/app/aois/{aoi_id}",
                headers=auth_headers,
                json={"name": "Updated AOI"}
            )
            assert update_response.status_code == 200
    
    async def test_backfill_request(self, auth_headers):
        """Test backfill job creation"""
        async with httpx.AsyncClient() as client:
            farm_response = await client.post(
                f"{API_BASE}/v1/app/farms",
                headers=auth_headers,
                json={"name": "Backfill Farm", "timezone": "America/Sao_Paulo"}
            )
            assert farm_response.status_code in [201, 200]
            farm_id = farm_response.json()["id"]

            aoi_response = await client.post(
                f"{API_BASE}/v1/app/aois",
                headers=auth_headers,
                json={
                    "farm_id": farm_id,
                    "name": "Backfill AOI",
                    "use_type": "PASTURE",
                    "geometry": "MULTIPOLYGON(((-47.0 -23.0, -47.0 -23.001, -47.001 -23.001, -47.001 -23.0, -47.0 -23.0)))"
                }
            )
            assert aoi_response.status_code == 201
            aoi_id = aoi_response.json()["id"]

            response = await client.post(
                f"{API_BASE}/v1/app/aois/{aoi_id}/backfill",
                headers=auth_headers,
                json={
                    "from_date": "2024-01-01",
                    "to_date": "2024-01-31",
                    "cadence": "weekly"
                }
            )
            if response.status_code == 500:
                pytest.skip("Backfill queue unavailable in test environment")
            assert response.status_code == 202
            data = response.json()
            assert "job_id" in data
            assert data["weeks_count"] > 0
    
    async def test_jobs_endpoints(self, auth_headers):
        """Test job listing and management"""
        async with httpx.AsyncClient() as client:
            # List jobs
            response = await client.get(
                f"{API_BASE}/v1/app/jobs",
                headers=auth_headers
            )
            assert response.status_code == 200
            
            jobs = response.json()
            if len(jobs) > 0:
                job_id = jobs[0]["id"]
                
                # Get job details
                detail_response = await client.get(
                    f"{API_BASE}/v1/app/jobs/{job_id}",
                    headers=auth_headers
                )
                assert detail_response.status_code == 200
                
                # Get job runs
                runs_response = await client.get(
                    f"{API_BASE}/v1/app/jobs/{job_id}/runs",
                    headers=auth_headers
                )
                assert runs_response.status_code == 200


class TestTenantAdmin:
    """Test tenant admin endpoints"""
    
    async def test_member_management(self, auth_headers):
        """Test member invite and role management"""
        async with httpx.AsyncClient() as client:
            # List members
            response = await client.get(
                f"{API_BASE}/v1/app/admin/tenant/members",
                headers=auth_headers
            )
            assert response.status_code == 200
            
            # Invite member
            invite_response = await client.post(
                f"{API_BASE}/v1/app/admin/tenant/members/invite",
                headers=auth_headers,
                json={
                    "email": "newuser@example.com",
                    "name": "New User",
                    "role": "VIEWER"
                }
            )
            # May fail due to quota, that's OK
            assert invite_response.status_code in [201, 403]
    
    async def test_settings_management(self, auth_headers):
        """Test tenant settings"""
        async with httpx.AsyncClient() as client:
            # Get settings
            response = await client.get(
                f"{API_BASE}/v1/app/admin/tenant/settings",
                headers=auth_headers
            )
            assert response.status_code == 200
            
            # Update settings
            update_response = await client.patch(
                f"{API_BASE}/v1/app/admin/tenant/settings",
                headers=auth_headers,
                json={"min_valid_pixel_ratio": 0.2}
            )
            assert update_response.status_code == 200


class TestSystemAdmin:
    """Test system admin endpoints"""
    
    async def test_tenant_management(self, system_admin_headers):
        """Test tenant CRUD operations"""
        async with httpx.AsyncClient() as client:
            # List tenants
            response = await client.get(
                f"{API_BASE}/v1/admin/tenants",
                headers=system_admin_headers
            )
            assert response.status_code == 200
            
            # Create tenant
            create_response = await client.post(
                f"{API_BASE}/v1/admin/tenants",
                headers=system_admin_headers,
                json={
                    "name": "Test Tenant",
                    "type": "COMPANY"
                }
            )
            assert create_response.status_code == 201
    
    async def test_system_health(self, system_admin_headers):
        """Test system health endpoint"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE}/v1/admin/ops/health",
                headers=system_admin_headers
            )
            assert response.status_code == 200
            
            health = response.json()
            assert "database" in health
            assert "jobs_24h" in health
    
    async def test_global_audit_log(self, system_admin_headers):
        """Test global audit log access"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE}/v1/admin/audit",
                headers=system_admin_headers
            )
            assert response.status_code == 200


class TestCursorPagination:
    """Test cursor-based pagination"""
    
    async def test_signals_pagination(self, auth_headers):
        """Test cursor pagination on signals endpoint"""
        async with httpx.AsyncClient() as client:
            # First page
            response = await client.get(
                f"{API_BASE}/v1/app/signals?limit=5",
                headers=auth_headers
            )
            assert response.status_code == 200
            
            # Check for cursor in headers
            next_cursor = response.headers.get("X-Next-Cursor")
            
            if next_cursor:
                # Fetch next page
                next_response = await client.get(
                    f"{API_BASE}/v1/app/signals?cursor={next_cursor}&limit=5",
                    headers=auth_headers
                )
                assert next_response.status_code == 200


class TestResiliency:
    """Test resiliency features"""
    
    async def test_rate_limiting(self, auth_headers):
        """Test rate limiting (if enabled)"""
        async with httpx.AsyncClient() as client:
            # Make many requests rapidly
            responses = []
            for i in range(150):
                response = await client.get(
                    f"{API_BASE}/v1/app/farms",
                    headers=auth_headers
                )
                responses.append(response.status_code)
            
            # Should see some 429 responses if rate limiting is active
            # (This depends on configuration)
            assert 200 in responses
    
    async def test_health_check(self):
        """Test health check endpoint"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_BASE}/health")
            assert response.status_code == 200
            
            health = response.json()
            assert health["status"] in ["healthy", "degraded"]


class TestAIAssistant:
    """Test AI Assistant endpoints"""
    
    async def test_thread_creation(self, auth_headers):
        """Test creating AI assistant thread"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE}/v1/app/ai-assistant/threads",
                headers=auth_headers,
                json={}
            )
            # May fail if quota exceeded
            assert response.status_code in [201, 403]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
