"""Smoke tests for public-data-compliance system.

Tests cover:
- Core module imports
- DataCatalogParser: field analysis, data type detection, sensitivity assessment
- PrivacyRiskDetector: personal info detection, re-identification risk
- AuthorizationChecker: scope checking, purpose validation
- DataLineageTracker: node/edge management, lineage paths
- RiskEntropyScorer: multi-dimensional risk scoring, coupling, fuse
- ReportGenerator: report generation, markdown export
- Pydantic schemas: model validation
"""
import pytest
from datetime import date, timedelta


# ─── Module Import Tests ───────────────────────────────────────────

class TestImports:
    """Verify all core modules can be imported."""

    def test_import_data_catalog_parser(self):
        from backend.app.services.data_catalog_parser import DataCatalogParser, parse_data_catalog
        assert DataCatalogParser is not None
        assert callable(parse_data_catalog)

    def test_import_privacy_risk_detector(self):
        from backend.app.services.privacy_risk_detector import PrivacyRiskDetector, detect_privacy_risk
        assert PrivacyRiskDetector is not None
        assert callable(detect_privacy_risk)

    def test_import_authorization_checker(self):
        from backend.app.services.authorization_checker import AuthorizationChecker, AuthorizationScope
        assert AuthorizationChecker is not None
        assert AuthorizationScope is not None

    def test_import_data_lineage_tracker(self):
        from backend.app.services.data_lineage_tracker import DataLineageTracker, LineageNode, LineageEdge
        assert DataLineageTracker is not None
        assert LineageNode is not None
        assert LineageEdge is not None

    def test_import_risk_scorer(self):
        from backend.app.services.data_risk_scorer import RiskEntropyScorer
        assert RiskEntropyScorer is not None

    def test_import_report_generator(self):
        from backend.app.services.report_generator import ReportGenerator
        assert ReportGenerator is not None

    def test_import_schemas(self):
        from backend.app.models.schemas import (
            DataCatalogRegisterRequest, AuthorizationCreateRequest,
            PrivacyRiskResponse, RiskScoreResponse, HealthResponse
        )
        assert all(cls is not None for cls in [
            DataCatalogRegisterRequest, AuthorizationCreateRequest,
            PrivacyRiskResponse, RiskScoreResponse, HealthResponse
        ])


# ─── DataCatalogParser Tests ───────────────────────────────────────

class TestDataCatalogParser:
    """Test data catalog parsing and field analysis."""

    @pytest.fixture
    def parser(self):
        from backend.app.services.data_catalog_parser import DataCatalogParser
        return DataCatalogParser()

    def test_parse_public_data(self, parser):
        fields = [
            {"name": "weather_data", "description": "天气统计数据"},
            {"name": "traffic_flow", "description": "交通流量数据"}
        ]
        result = parser.parse_catalog("test_catalog", "统计局", "public", fields)
        assert result["catalog_name"] == "test_catalog"
        assert result["field_count"] == 2
        assert result["detected_data_type"] == "public"

    def test_parse_personal_data(self, parser):
        fields = [
            {"name": "姓名", "description": "用户姓名"},
            {"name": "手机号", "description": "联系电话"}
        ]
        result = parser.parse_catalog("user_data", "用户中心", "public", fields)
        assert result["detected_data_type"] == "personal"
        # Should flag mismatch: declared public but contains personal info
        assert any(i["rule_id"] == "RULE_D_001" for i in result["issues"])

    def test_parse_sensitive_data(self, parser):
        fields = [
            {"name": "health_record", "description": "健康医疗记录"},
            {"name": "diagnosis", "description": "疾病诊断信息"}
        ]
        result = parser.parse_catalog("medical_data", "医院", "personal", fields)
        assert result["detected_data_type"] == "sensitive"

    def test_analyze_field_personal(self, parser):
        field = {"name": "身份证号", "description": "居民身份证号码"}
        result = parser._analyze_field(field)
        assert result["is_personal_info"] is True

    def test_analyze_field_sensitive(self, parser):
        field = {"name": "基因信息", "description": "基因检测数据"}
        result = parser._analyze_field(field)
        assert result["is_sensitive_info"] is True

    def test_analyze_field_anonymized(self, parser):
        field = {"name": "姓名_hash", "description": "脱敏后的姓名哈希值"}
        result = parser._analyze_field(field)
        assert result["is_anonymized"] is True

    def test_recommended_sensitivity_extreme(self, parser):
        fields = [{"name": "健康", "description": "health data"}]
        result = parser.parse_catalog("test", "dept", "personal", fields)
        assert result["recommended_sensitivity"] == "extreme"

    def test_recommended_sensitivity_medium(self, parser):
        fields = [{"name": "姓名", "description": "name"}]
        result = parser.parse_catalog("test", "dept", "personal", fields)
        assert result["recommended_sensitivity"] == "medium"


# ─── PrivacyRiskDetector Tests ─────────────────────────────────────

class TestPrivacyRiskDetector:
    """Test privacy risk detection."""

    @pytest.fixture
    def detector(self):
        from backend.app.services.privacy_risk_detector import PrivacyRiskDetector
        return PrivacyRiskDetector()

    def test_detect_no_risk(self, detector):
        fields = [
            {"name": "temperature", "description": "气温数据"},
            {"name": "humidity", "description": "湿度数据"}
        ]
        result = detector.detect_privacy_risk(fields)
        assert result["risk_level"] == "low"
        assert len(result["personal_info_fields"]) == 0

    def test_detect_personal_info(self, detector):
        fields = [
            {"name": "姓名", "description": "用户姓名"},
            {"name": "手机号", "description": "联系电话"}
        ]
        result = detector.detect_privacy_risk(fields)
        assert len(result["personal_info_fields"]) == 2
        assert result["risk_level"] in ["medium", "high", "extreme"]

    def test_detect_sensitive_info(self, detector):
        fields = [
            {"name": "health_status", "description": "健康状况"},
            {"name": "disease", "description": "疾病诊断"}
        ]
        result = detector.detect_privacy_risk(fields)
        assert len(result["sensitive_info_fields"]) >= 1

    def test_detect_reid_risk(self, detector):
        fields = [
            {"name": "性别", "description": "gender"},
            {"name": "年龄", "description": "age"},
            {"name": "地区", "description": "region"},
            {"name": "职业", "description": "occupation"}
        ]
        result = detector.detect_privacy_risk(fields)
        assert len(result["reid_risk_fields"]) >= 1

    def test_check_anonymization_quality(self, detector):
        fields = [
            {"name": "name_hash", "description": "hashed name"},
            {"name": "phone_masked", "description": "masked phone"}
        ]
        result = detector.check_anonymization_quality(fields, ["name", "phone"])
        assert result["is_anonymized"] is True

    def test_risk_score_calculation(self, detector):
        fields = [
            {"name": "姓名", "description": "name"},
            {"name": "身份证", "description": "id card"},
            {"name": "健康状况", "description": "health"},
        ]
        result = detector.detect_privacy_risk(fields)
        assert result["risk_score"] > 0
        assert result["risk_score"] <= 100


# ─── AuthorizationChecker Tests ────────────────────────────────────

class TestAuthorizationChecker:
    """Test authorization scope checking."""

    @pytest.fixture
    def checker(self):
        from backend.app.services.authorization_checker import AuthorizationChecker, AuthorizationScope
        checker = AuthorizationChecker()
        # Add a test authorization
        auth = AuthorizationScope(
            authorized_party="研究部",
            usage_scope="统计分析 科研",
            authorized_fields=["age", "gender", "region"],
            valid_from=date.today() - timedelta(days=30),
            valid_to=date.today() + timedelta(days=30)
        )
        checker.add_authorization(1, auth)
        return checker

    def test_check_authorized(self, checker):
        result = checker.check_authorization(1, "研究部", "统计分析", ["age", "gender"])
        assert result["is_authorized"] is True
        assert len(result["authorized_fields"]) == 2

    def test_check_unauthorized_field(self, checker):
        result = checker.check_authorization(1, "研究部", "统计分析", ["age", "ssn"])
        assert "ssn" in result["unauthorized_fields"]
        assert result["is_authorized"] is False

    def test_check_wrong_party(self, checker):
        result = checker.check_authorization(1, "市场部", "统计分析", ["age"])
        assert result["is_authorized"] is False
        assert any(i["rule_id"] == "RULE_D_004" for i in result["issues"])

    def test_check_no_auth_record(self):
        from backend.app.services.authorization_checker import AuthorizationChecker
        checker = AuthorizationChecker()
        result = checker.check_authorization(999, "研究部", "统计分析", ["age"])
        assert result["is_authorized"] is False
        assert any(i["rule_id"] == "RULE_D_003" for i in result["issues"])

    def test_check_unauthorized_purpose(self, checker):
        result = checker.check_authorization(1, "研究部", "商业销售", ["age"])
        assert any(i["rule_id"] == "RULE_D_006" for i in result["issues"])

    def test_wildcard_field_auth(self):
        from backend.app.services.authorization_checker import AuthorizationChecker, AuthorizationScope
        checker = AuthorizationChecker()
        auth = AuthorizationScope(
            authorized_party="*", usage_scope="*",
            authorized_fields=["*"],
            valid_from=date.today(), valid_to=date.today() + timedelta(days=365)
        )
        checker.add_authorization(2, auth)
        result = checker.check_authorization(2, "任何人", "任何用途", ["any_field"])
        assert result["is_authorized"] is True


# ─── DataLineageTracker Tests ──────────────────────────────────────

class TestDataLineageTracker:
    """Test data lineage tracking."""

    @pytest.fixture
    def tracker(self):
        from backend.app.services.data_lineage_tracker import DataLineageTracker
        return DataLineageTracker()

    def test_add_catalog_node(self, tracker):
        node = tracker.add_catalog_node(1, "人口数据", "统计局")
        assert node.id == "catalog_1"
        assert node.name == "人口数据"
        assert "catalog_1" in tracker.nodes

    def test_add_product_node(self, tracker):
        tracker.add_catalog_node(1, "人口数据", "统计局")
        node = tracker.add_product_node(1, "p1", "人口统计报告")
        assert node.id == "product_p1"
        assert "product_p1" in tracker.catalog_products[1]

    def test_add_lineage_edge(self, tracker):
        tracker.add_catalog_node(1, "人口数据", "统计局")
        tracker.add_product_node(1, "p1", "人口统计报告")
        edge = tracker.add_lineage_edge("catalog_1", "product_p1", "processing")
        assert edge.source_id == "catalog_1"
        assert edge.target_id == "product_p1"
        assert len(tracker.edges) == 1

    def test_get_lineage_path(self, tracker):
        tracker.add_catalog_node(1, "人口数据", "统计局")
        tracker.add_product_node(1, "p1", "人口统计报告")
        tracker.add_lineage_edge("catalog_1", "product_p1", "processing")
        result = tracker.get_lineage_path(1)
        assert len(result["nodes"]) >= 2
        assert len(result["edges"]) >= 1

    def test_lineage_incomplete(self, tracker):
        tracker.add_catalog_node(1, "人口数据", "统计局")
        result = tracker.get_lineage_path(1)
        assert result["is_complete"] is False
        assert any(i["rule_id"] == "RULE_D_009" for i in result["issues"])

    def test_export_lineage_graph(self, tracker):
        tracker.add_catalog_node(1, "人口数据", "统计局")
        tracker.add_product_node(1, "p1", "人口统计报告")
        tracker.add_lineage_edge("catalog_1", "product_p1", "processing")
        graph = tracker.export_lineage_graph(1)
        assert "nodes" in graph
        assert "edges" in graph
        assert graph["stats"]["total_nodes"] >= 2

    def test_detect_lineage_issues_unknown_source(self, tracker):
        tracker.add_catalog_node(1, "test", "dept")
        fields = [{"name": "field1", "source_unknown": True}]
        issues = tracker.detect_lineage_issues(1, fields)
        assert any(i["rule_id"] == "RULE_D_009" for i in issues)


# ─── RiskEntropyScorer Tests ───────────────────────────────────────

class TestRiskEntropyScorer:
    """Test multi-dimensional risk entropy scoring."""

    @pytest.fixture
    def scorer(self):
        from backend.app.services.data_risk_scorer import RiskEntropyScorer
        return RiskEntropyScorer()

    @pytest.fixture
    def low_risk_inputs(self):
        catalog = {"id": 1, "name": "test", "data_type": "public", "sensitivity_level": "low", "auth_scope": "full"}
        privacy = {"personal_info_fields": [], "sensitive_info_fields": [], "reid_risk_fields": [], "issues": [], "anonymized_fields": []}
        auth = {"is_authorized": True, "unauthorized_fields": [], "issues": []}
        lineage = {"is_complete": True, "nodes": [], "edges": []}
        return catalog, privacy, auth, lineage

    @pytest.fixture
    def high_risk_inputs(self):
        catalog = {"id": 2, "name": "sensitive", "data_type": "personal", "sensitivity_level": "extreme", "auth_scope": ""}
        privacy = {
            "personal_info_fields": [{"field_name": "name"}, {"field_name": "phone"}],
            "sensitive_info_fields": [{"field_name": "health"}],
            "reid_risk_fields": ["gender+age"],
            "issues": [{"rule_id": "RULE_D_001"}, {"rule_id": "RULE_D_002"}],
            "anonymized_fields": []
        }
        auth = {"is_authorized": False, "unauthorized_fields": ["name", "phone"], "issues": [{"rule_id": "RULE_D_006"}]}
        lineage = {"is_complete": False, "nodes": [], "edges": [], "issues": [{"rule_id": "RULE_D_009"}]}
        return catalog, privacy, auth, lineage

    def test_low_risk_score(self, scorer, low_risk_inputs):
        result = scorer.score(*low_risk_inputs)
        assert result["risk_level"] == "low"
        assert result["total_entropy_score"] < 40

    def test_high_risk_score(self, scorer, high_risk_inputs):
        result = scorer.score(*high_risk_inputs)
        assert result["risk_level"] in ["high", "extreme"]
        assert result["total_entropy_score"] > 40

    def test_fuse_trigger(self, scorer, high_risk_inputs):
        result = scorer.score(*high_risk_inputs)
        # With extreme sensitivity and no auth, fuse should trigger
        assert result["fuse_triggered"] is True or result["total_entropy_score"] > 60

    def test_coupling_detection(self, scorer, high_risk_inputs):
        result = scorer.score(*high_risk_inputs)
        assert result["is_coupled"] is True

    def test_dimensions_present(self, scorer, low_risk_inputs):
        result = scorer.score(*low_risk_inputs)
        dims = result["dimensions"]
        assert "open_risk" in dims
        assert "auth_risk" in dims
        assert "privacy_risk" in dims
        assert "reid_risk" in dims

    def test_suggestions_generated(self, scorer, high_risk_inputs):
        result = scorer.score(*high_risk_inputs)
        assert len(result["suggestions"]) > 0

    def test_score_capped_at_100(self, scorer, high_risk_inputs):
        result = scorer.score(*high_risk_inputs)
        assert result["total_entropy_score"] <= 100


# ─── ReportGenerator Tests ─────────────────────────────────────────

class TestReportGenerator:
    """Test compliance report generation."""

    @pytest.fixture
    def generator(self):
        from backend.app.services.report_generator import ReportGenerator
        return ReportGenerator()

    def test_generate_report(self, generator):
        catalog = {"id": 1, "name": "test", "department": "dept"}
        risk = {"total_entropy_score": 30, "risk_level": "low", "dimensions": {}, "is_coupled": False, "coupling_penalty": 0, "fuse_triggered": False}
        privacy = {"personal_info_fields": [], "sensitive_info_fields": [], "reid_risk_fields": [], "issues": [], "anonymized_fields": []}
        auth = {"is_authorized": True, "authorized_fields": [], "unauthorized_fields": [], "issues": []}
        lineage = {"is_complete": True, "nodes": [], "edges": [], "issues": []}

        report = generator.generate_report(catalog, risk, privacy, auth, lineage)
        assert "report_info" in report
        assert "risk_assessment" in report
        assert "review_opinions" in report
        assert "rectification_suggestions" in report

    def test_format_markdown(self, generator):
        catalog = {"id": 1, "name": "test", "department": "dept"}
        risk = {"total_entropy_score": 50, "risk_level": "medium", "dimensions": {"open_risk": 10, "auth_risk": 20, "privacy_risk": 15, "reid_risk": 5}, "is_coupled": False, "coupling_penalty": 0, "fuse_triggered": False}
        privacy = {"personal_info_fields": [{"field_name": "name"}], "sensitive_info_fields": [], "reid_risk_fields": [], "issues": [], "anonymized_fields": []}
        auth = {"is_authorized": True, "authorized_fields": [], "unauthorized_fields": [], "issues": []}
        lineage = {"is_complete": True, "nodes": [], "edges": [], "issues": []}

        report = generator.generate_report(catalog, risk, privacy, auth, lineage)
        md = generator.format_report_markdown(report)
        assert "公共数据资源授权运营合规审查报告" in md
        assert "风险评估结果" in md


# ─── Schema Validation Tests ───────────────────────────────────────

class TestSchemas:
    """Test Pydantic model validation."""

    def test_data_catalog_register_request(self):
        from backend.app.models.schemas import DataCatalogRegisterRequest, FieldInfo
        req = DataCatalogRegisterRequest(
            name="test", department="dept", data_type="public",
            fields=[FieldInfo(name="field1")]
        )
        assert req.name == "test"
        assert len(req.fields) == 1

    def test_health_response(self):
        from backend.app.models.schemas import HealthResponse
        resp = HealthResponse(status="ok", service="test", version="1.0")
        assert resp.status == "ok"

    def test_authorization_create_request(self):
        from backend.app.models.schemas import AuthorizationCreateRequest
        req = AuthorizationCreateRequest(
            catalog_id=1, authorized_party="研究部",
            usage_scope="统计分析", valid_from="2025-01-01", valid_to="2025-12-31"
        )
        assert req.catalog_id == 1
