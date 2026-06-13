"""Tests for FastAPI endpoints.

Covers all routes defined in backend/app/api/routes.py and backend/app/main.py.
Uses httpx.AsyncClient with ASGITransport for synchronous-style testing.
"""
import pytest
from httpx import AsyncClient, ASGITransport


@pytest.fixture
def client(tmp_db):
    """Create a test client with a temporary database."""
    # Re-init DB for this test session
    import backend.app.core.database as db_mod
    db_mod.init_db()

    from backend.app.main import app
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


# ─── Health & Root ─────────────────────────────────────────────

class TestHealthEndpoints:
    """Test health check and root endpoints."""

    @pytest.mark.asyncio
    async def test_health(self, client):
        async with client as c:
            resp = await c.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["service"] == "public-data-compliance"

    @pytest.mark.asyncio
    async def test_root(self, client):
        async with client as c:
            resp = await c.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["version"] == "1.0.0"
        assert data["port"] == 8013


# ─── Catalog Registration ──────────────────────────────────────

class TestCatalogRegistration:
    """Test POST /api/v1/register_catalog."""

    @pytest.mark.asyncio
    async def test_register_public_catalog(self, client):
        async with client as c:
            resp = await c.post("/api/v1/register_catalog", json={
                "name": "天气数据集",
                "department": "气象局",
                "data_type": "public",
                "fields": [
                    {"name": "temperature", "description": "气温"},
                    {"name": "humidity", "description": "湿度"},
                ],
                "source_info": "气象站",
                "auth_scope": "公开",
                "sensitivity_level": "low",
            })
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "天气数据集"
        assert data["department"] == "气象局"
        assert data["fields_count"] == 2
        assert "id" in data

    @pytest.mark.asyncio
    async def test_register_personal_catalog(self, client):
        async with client as c:
            resp = await c.post("/api/v1/register_catalog", json={
                "name": "用户数据",
                "department": "用户中心",
                "data_type": "public",
                "fields": [
                    {"name": "姓名", "description": "用户姓名"},
                    {"name": "手机号", "description": "联系电话"},
                ],
            })
        assert resp.status_code == 200
        data = resp.json()
        # Should detect personal data type
        assert data["data_type"] == "personal"

    @pytest.mark.asyncio
    async def test_register_catalog_missing_required_fields(self, client):
        async with client as c:
            resp = await c.post("/api/v1/register_catalog", json={
                "name": "test",
            })
        assert resp.status_code == 422


# ─── Authorization ─────────────────────────────────────────────

class TestAuthorizationEndpoints:
    """Test authorization creation and checking."""

    @pytest.mark.asyncio
    async def test_create_authorization(self, client):
        async with client as c:
            # First register a catalog
            cat_resp = await c.post("/api/v1/register_catalog", json={
                "name": "test_cat", "department": "dept", "data_type": "public",
                "fields": [{"name": "f1", "description": "d1"}],
            })
            cat_id = cat_resp.json()["id"]

            # Create authorization
            resp = await c.post("/api/v1/create_authorization", json={
                "catalog_id": cat_id,
                "authorized_party": "研究部",
                "usage_scope": "统计分析 科研",
                "valid_from": "2025-01-01",
                "valid_to": "2025-12-31",
            })
        assert resp.status_code == 200
        data = resp.json()
        assert data["authorized_party"] == "研究部"
        assert data["status"] == "active"

    @pytest.mark.asyncio
    async def test_create_authorization_invalid_catalog(self, client):
        async with client as c:
            resp = await c.post("/api/v1/create_authorization", json={
                "catalog_id": 9999,
                "authorized_party": "研究部",
                "usage_scope": "统计分析",
                "valid_from": "2025-01-01",
                "valid_to": "2025-12-31",
            })
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_check_authorization(self, client):
        async with client as c:
            # Register catalog
            cat_resp = await c.post("/api/v1/register_catalog", json={
                "name": "auth_test", "department": "dept", "data_type": "public",
                "fields": [{"name": "age", "description": "年龄"}],
            })
            cat_id = cat_resp.json()["id"]

            # Create authorization
            await c.post("/api/v1/create_authorization", json={
                "catalog_id": cat_id,
                "authorized_party": "研究部",
                "usage_scope": "统计分析",
                "valid_from": "2025-01-01",
                "valid_to": "2025-12-31",
            })

            # Check authorization
            resp = await c.post("/api/v1/check_authorization", json={
                "catalog_id": cat_id,
                "requester": "研究部",
                "intended_use": "统计分析",
                "requested_fields": ["age"],
            })
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_authorized"] is True


# ─── Data Product ──────────────────────────────────────────────

class TestDataProductEndpoints:
    """Test data product upload."""

    @pytest.mark.asyncio
    async def test_upload_data_product(self, client):
        async with client as c:
            cat_resp = await c.post("/api/v1/register_catalog", json={
                "name": "product_test", "department": "dept", "data_type": "public",
                "fields": [{"name": "f1", "description": "d1"}],
            })
            cat_id = cat_resp.json()["id"]

            resp = await c.post("/api/v1/upload_data_product", json={
                "catalog_id": cat_id,
                "product_name": "统计报告",
                "product_description": "月度统计报告",
                "fields": [{"name": "统计值", "description": "统计数据"}],
                "process_description": "数据聚合",
            })
        assert resp.status_code == 200
        data = resp.json()
        assert data["message"] == "数据产品上传成功"
        assert "product_id" in data


# ─── Privacy Risk Analysis ─────────────────────────────────────

class TestPrivacyRiskEndpoint:
    """Test POST /api/v1/analyze_privacy_risk."""

    @pytest.mark.asyncio
    async def test_analyze_privacy_risk_with_catalog(self, client):
        async with client as c:
            cat_resp = await c.post("/api/v1/register_catalog", json={
                "name": "privacy_test", "department": "dept", "data_type": "personal",
                "fields": [
                    {"name": "姓名", "description": "name"},
                    {"name": "手机号", "description": "phone"},
                ],
            })
            cat_id = cat_resp.json()["id"]

            resp = await c.post("/api/v1/analyze_privacy_risk", json={
                "catalog_id": cat_id,
                "fields": [],
            })
        assert resp.status_code == 200
        data = resp.json()
        assert data["personal_info_count"] >= 2
        assert data["risk_level"] in ["low", "medium", "high", "extreme"]

    @pytest.mark.asyncio
    async def test_analyze_privacy_risk_inline_fields(self, client):
        async with client as c:
            resp = await c.post("/api/v1/analyze_privacy_risk", json={
                "fields": [
                    {"name": "温度", "description": "气温数据"},
                    {"name": "湿度", "description": "湿度数据"},
                ],
            })
        assert resp.status_code == 200
        data = resp.json()
        assert data["personal_info_count"] == 0
        assert data["risk_level"] == "low"


# ─── Risk Report ───────────────────────────────────────────────

class TestRiskReportEndpoint:
    """Test GET /api/v1/get_risk_report/{catalog_id}."""

    @pytest.mark.asyncio
    async def test_get_risk_report(self, client):
        async with client as c:
            cat_resp = await c.post("/api/v1/register_catalog", json={
                "name": "report_test", "department": "dept", "data_type": "public",
                "fields": [{"name": "temperature", "description": "气温"}],
            })
            cat_id = cat_resp.json()["id"]

            resp = await c.get(f"/api/v1/get_risk_report/{cat_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_score" in data
        assert "risk_level" in data
        assert "issues" in data
        assert "review_opinions" in data

    @pytest.mark.asyncio
    async def test_get_risk_report_nonexistent(self, client):
        async with client as c:
            resp = await c.get("/api/v1/get_risk_report/9999")
        assert resp.status_code == 404


# ─── Lineage ───────────────────────────────────────────────────

class TestLineageEndpoint:
    """Test GET /api/v1/get_lineage/{catalog_id}."""

    @pytest.mark.asyncio
    async def test_get_lineage(self, client):
        async with client as c:
            cat_resp = await c.post("/api/v1/register_catalog", json={
                "name": "lineage_test", "department": "dept", "data_type": "public",
                "fields": [{"name": "f1", "description": "d1"}],
            })
            cat_id = cat_resp.json()["id"]

            resp = await c.get(f"/api/v1/get_lineage/{cat_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert "nodes" in data
        assert "edges" in data


# ─── Audit Logs ────────────────────────────────────────────────

class TestAuditLogEndpoint:
    """Test GET /api/v1/audit_logs."""

    @pytest.mark.asyncio
    async def test_audit_logs(self, client):
        async with client as c:
            # Trigger some audit logs
            await c.post("/api/v1/register_catalog", json={
                "name": "audit_test", "department": "dept", "data_type": "public",
                "fields": [{"name": "f1", "description": "d1"}],
            })

            resp = await c.get("/api/v1/audit_logs")
        assert resp.status_code == 200
        data = resp.json()
        assert "logs" in data
        assert data["total"] >= 1


# ─── Main.py Extra Endpoints ───────────────────────────────────

class TestMainEndpoints:
    """Test endpoints defined in main.py (map_sensitivity, assess_breach_risk, etc.)."""

    @pytest.mark.asyncio
    async def test_map_sensitivity(self, client):
        async with client as c:
            resp = await c.post("/api/v1/map_sensitivity", json={
                "data_items": [
                    {"name": "指纹", "category": "个人生物信息", "collection_scope": "全量收集", "retention_period": "永久"},
                    {"name": "天气", "category": "公开数据", "collection_scope": "必要范围内", "retention_period": "临时"},
                ]
            })
        assert resp.status_code == 200
        data = resp.json()
        assert data["data_item_count"] == 2
        assert data["critical_count"] >= 1
        assert data["average_sensitivity"] > 0

    @pytest.mark.asyncio
    async def test_assess_breach_risk(self, client):
        async with client as c:
            resp = await c.post("/api/v1/assess_breach_risk", json={
                "data_category": "位置轨迹",
                "collection_scale": "mass_surveillance",
                "authorization_status": "none",
                "third_party_sharing": True,
                "security_measures": [],
            })
        assert resp.status_code == 200
        data = resp.json()
        assert data["risk_score"] > 0
        assert data["risk_level"] in ["low", "medium", "high", "critical"]
        assert "breach_probability" in data

    @pytest.mark.asyncio
    async def test_assess_breach_risk_with_security(self, client):
        async with client as c:
            resp = await c.post("/api/v1/assess_breach_risk", json={
                "data_category": "金融账户",
                "collection_scale": "individual",
                "authorization_status": "authorized",
                "third_party_sharing": False,
                "security_measures": ["加密", "访问控制", "审计日志"],
            })
        assert resp.status_code == 200
        data = resp.json()
        assert data["risk_level"] in ["low", "medium"]

    @pytest.mark.asyncio
    async def test_authorize_data_use(self, client):
        async with client as c:
            resp = await c.post("/api/v1/authorize_data_use", json={
                "applicant_id": "org-001",
                "data_category": "医疗健康",
                "intended_use": "临床研究",
                "authorization_level": "full",
            })
        assert resp.status_code == 200
        data = resp.json()
        assert data["decision"] in ["approved", "denied"]
        assert data["data_category"] == "医疗健康"
        assert "conditions" in data

    @pytest.mark.asyncio
    async def test_check_compliance(self, client):
        import json
        ops = json.dumps([
            {"operation": "数据查询", "data_category": "公开数据", "authorized": True},
            {"operation": "数据导出", "data_category": "位置轨迹", "authorized": False},
        ])
        async with client as c:
            resp = await c.get(f"/api/v1/check_compliance?organization_id=org-001&data_operations={ops}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["compliance_rate"] == 50.0
        assert data["compliance_status"] == "non_compliant"
        assert len(data["unauthorized_operations"]) == 1

    @pytest.mark.asyncio
    async def test_check_compliance_invalid_json(self, client):
        async with client as c:
            resp = await c.get("/api/v1/check_compliance?organization_id=org-001&data_operations=not-json")
        assert resp.status_code == 400
