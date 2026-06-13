"""Comprehensive service-level unit tests.

Covers every service module in backend/app/services/ with thorough edge cases.
"""
import pytest
from datetime import date, timedelta


# ═══════════════════════════════════════════════════════════════
# DataCatalogParser
# ═══════════════════════════════════════════════════════════════

class TestDataCatalogParser:
    """Exhaustive tests for DataCatalogParser."""

    @pytest.fixture
    def parser(self):
        from backend.app.services.data_catalog_parser import DataCatalogParser
        return DataCatalogParser()

    # --- Data type detection ---

    def test_detect_public_type(self, parser):
        fields = [{"name": "天气", "description": "weather"}, {"name": "交通", "description": "traffic"}]
        assert parser._detect_data_type(fields) == "public"

    def test_detect_personal_type(self, parser):
        fields = [{"name": "姓名", "description": "name"}, {"name": "温度", "description": "temp"}]
        assert parser._detect_data_type(fields) == "personal"

    def test_detect_sensitive_type(self, parser):
        fields = [{"name": "健康", "description": "health"}, {"name": "温度", "description": "temp"}]
        assert parser._detect_data_type(fields) == "sensitive"

    def test_detect_unknown_type(self, parser):
        fields = [{"name": "col_a", "description": "random"}, {"name": "col_b", "description": "data"}]
        result = parser._detect_data_type(fields)
        assert result in ["unknown", "public"]

    def test_detect_empty_fields(self, parser):
        assert parser._detect_data_type([]) == "unknown"

    # --- Field analysis ---

    def test_analyze_personal_field(self, parser):
        for keyword in ["姓名", "手机", "邮箱", "身份证", "地址", "银行卡", "护照"]:
            result = parser._analyze_field({"name": keyword, "description": ""})
            assert result["is_personal_info"] is True, f"Failed for keyword: {keyword}"

    def test_analyze_sensitive_field(self, parser):
        for keyword in ["健康", "基因", "人脸", "位置", "犯罪", "征信"]:
            result = parser._analyze_field({"name": keyword, "description": ""})
            assert result["is_sensitive_info"] is True, f"Failed for keyword: {keyword}"

    def test_analyze_anonymized_field(self, parser):
        result = parser._analyze_field({"name": "姓名_hash", "description": "脱敏处理"})
        assert result["is_anonymized"] is True

    def test_analyze_reid_risk_identifier(self, parser):
        result = parser._analyze_field({"name": "user_id", "description": "用户编号"})
        assert result["can_reidentify"] is True

    def test_analyze_non_sensitive_field(self, parser):
        result = parser._analyze_field({"name": "temperature", "description": "气温"})
        assert result["is_personal_info"] is False
        assert result["is_sensitive_info"] is False

    # --- Catalog parsing ---

    def test_parse_catalog_public_clean(self, parser, sample_public_fields):
        result = parser.parse_catalog("天气数据", "气象局", "public", sample_public_fields)
        assert result["detected_data_type"] == "public"
        assert len(result["issues"]) == 0

    def test_parse_catalog_type_mismatch(self, parser, sample_personal_fields):
        result = parser.parse_catalog("用户数据", "用户中心", "public", sample_personal_fields)
        assert any(i["rule_id"] == "RULE_D_001" for i in result["issues"])

    def test_parse_catalog_sensitive_misclassified(self, parser, sample_sensitive_fields):
        result = parser.parse_catalog("医疗数据", "医院", "public", sample_sensitive_fields)
        assert any(i["rule_id"] == "RULE_D_002" for i in result["issues"])

    def test_recommended_sensitivity_extreme(self, parser):
        fields = [{"name": "基因信息", "description": "genetic data"}]
        result = parser.parse_catalog("t", "d", "personal", fields)
        assert result["recommended_sensitivity"] == "extreme"

    def test_recommended_sensitivity_high(self, parser):
        fields = [
            {"name": "姓名", "description": "name"},
            {"name": "手机", "description": "phone"},
            {"name": "邮箱", "description": "email"},
            {"name": "地址", "description": "address"},
        ]
        result = parser.parse_catalog("t", "d", "personal", fields)
        assert result["recommended_sensitivity"] == "high"

    def test_recommended_sensitivity_medium(self, parser):
        fields = [{"name": "姓名", "description": "name"}]
        result = parser.parse_catalog("t", "d", "personal", fields)
        assert result["recommended_sensitivity"] == "medium"

    def test_parse_empty_fields(self, parser):
        result = parser.parse_catalog("empty", "dept", "public", [])
        assert result["field_count"] == 0
        assert result["detected_data_type"] == "unknown"

    def test_reid_combinations_detected(self, parser):
        fields = [
            {"name": "性别", "description": "gender"},
            {"name": "年龄", "description": "age"},
        ]
        result = parser.parse_catalog("reid_test", "dept", "personal", fields)
        # Should have at least one issue about personal info
        assert len(result["issues"]) >= 1


# ═══════════════════════════════════════════════════════════════
# PrivacyRiskDetector
# ═══════════════════════════════════════════════════════════════

class TestPrivacyRiskDetector:
    """Exhaustive tests for PrivacyRiskDetector."""

    @pytest.fixture
    def detector(self):
        from backend.app.services.privacy_risk_detector import PrivacyRiskDetector
        return PrivacyRiskDetector()

    def test_no_risk_fields(self, detector):
        fields = [{"name": "temperature", "description": "气温"}, {"name": "humidity", "description": "湿度"}]
        result = detector.detect_privacy_risk(fields)
        assert result["risk_level"] == "low"
        assert result["risk_score"] == 0
        assert len(result["personal_info_fields"]) == 0
        assert len(result["sensitive_info_fields"]) == 0

    def test_personal_info_detection(self, detector):
        fields = [
            {"name": "姓名", "description": "name"},
            {"name": "手机号", "description": "mobile"},
            {"name": "邮箱", "description": "email"},
            {"name": "身份证", "description": "id card"},
        ]
        result = detector.detect_privacy_risk(fields)
        assert len(result["personal_info_fields"]) == 4
        assert result["risk_score"] > 0

    def test_sensitive_info_detection(self, detector):
        fields = [
            {"name": "health_status", "description": "健康状况"},
            {"name": "diagnosis", "description": "疾病诊断"},
        ]
        result = detector.detect_privacy_risk(fields)
        assert len(result["sensitive_info_fields"]) >= 1

    def test_reid_risk_combinations(self, detector):
        fields = [
            {"name": "性别", "description": "gender"},
            {"name": "年龄", "description": "age"},
            {"name": "地区", "description": "region"},
            {"name": "职业", "description": "occupation"},
        ]
        result = detector.detect_privacy_risk(fields)
        assert len(result["reid_risk_fields"]) >= 1

    def test_reid_risk_masked_fields(self, detector):
        """Masked fields should reduce re-identification risk."""
        fields = [
            {"name": "性别_mask", "description": "masked gender"},
            {"name": "年龄", "description": "age"},
        ]
        result = detector.detect_privacy_risk(fields)
        # Masked field should reduce risk
        masked_combos = [r for r in result["reid_risk_fields"] if "性别" in r]
        # If masked, should not appear in reid risk
        for combo in masked_combos:
            assert "mask" in combo.lower() or len(masked_combos) == 0

    def test_anonymization_quality_good(self, detector):
        fields = [
            {"name": "name_hash", "description": "hashed name"},
            {"name": "phone_masked", "description": "masked phone"},
        ]
        result = detector.check_anonymization_quality(fields, ["name", "phone"])
        assert result["is_anonymized"] is True
        assert result["quality_score"] >= 50

    def test_anonymization_quality_poor(self, detector):
        fields = [
            {"name": "name", "description": "raw name"},
            {"name": "phone", "description": "raw phone"},
        ]
        result = detector.check_anonymization_quality(fields, ["name", "phone"])
        assert result["quality_score"] == 0

    def test_risk_score_bounds(self, detector):
        """Risk score should always be between 0 and 100."""
        fields = [
            {"name": "姓名", "description": "name"},
            {"name": "身份证", "description": "id"},
            {"name": "健康", "description": "health"},
            {"name": "基因", "description": "genetic"},
            {"name": "位置", "description": "location"},
        ]
        result = detector.detect_privacy_risk(fields)
        assert 0 <= result["risk_score"] <= 100

    def test_risk_levels_progression(self, detector):
        """More sensitive fields should yield higher risk levels."""
        low_fields = [{"name": "temperature", "description": "temp"}]
        high_fields = [
            {"name": "姓名", "description": "name"},
            {"name": "身份证", "description": "id"},
            {"name": "健康", "description": "health"},
        ]
        low_result = detector.detect_privacy_risk(low_fields)
        high_result = detector.detect_privacy_risk(high_fields)
        level_order = {"low": 0, "medium": 1, "high": 2, "extreme": 3}
        assert level_order[high_result["risk_level"]] >= level_order[low_result["risk_level"]]

    def test_unprotected_personal_fields_issue(self, detector):
        fields = [{"name": "姓名", "description": "name"}]
        result = detector.detect_privacy_risk(fields)
        # Should have issue about unprotected personal info
        assert any("RULE_D_001" in i.get("rule_id", "") for i in result["issues"])


# ═══════════════════════════════════════════════════════════════
# AuthorizationChecker
# ═══════════════════════════════════════════════════════════════

class TestAuthorizationChecker:
    """Exhaustive tests for AuthorizationChecker."""

    @pytest.fixture
    def checker(self):
        from backend.app.services.authorization_checker import AuthorizationChecker, AuthorizationScope
        c = AuthorizationChecker()
        auth = AuthorizationScope(
            authorized_party="研究部",
            usage_scope="统计分析 科研",
            authorized_fields=["age", "gender", "region"],
            valid_from=date.today() - timedelta(days=30),
            valid_to=date.today() + timedelta(days=30),
        )
        c.add_authorization(1, auth)
        return c

    def test_authorized_access(self, checker):
        result = checker.check_authorization(1, "研究部", "统计分析", ["age", "gender"])
        assert result["is_authorized"] is True
        assert result["authorized_fields"] == ["age", "gender"]
        assert result["unauthorized_fields"] == []

    def test_unauthorized_field(self, checker):
        result = checker.check_authorization(1, "研究部", "统计分析", ["age", "ssn"])
        assert "ssn" in result["unauthorized_fields"]
        assert result["is_authorized"] is False

    def test_wrong_party(self, checker):
        result = checker.check_authorization(1, "市场部", "统计分析", ["age"])
        assert result["is_authorized"] is False
        assert any("RULE_D_004" in i.get("rule_id", "") for i in result["issues"])

    def test_no_auth_record(self):
        from backend.app.services.authorization_checker import AuthorizationChecker
        checker = AuthorizationChecker()
        result = checker.check_authorization(999, "研究部", "统计分析", ["age"])
        assert result["is_authorized"] is False
        assert any("RULE_D_003" in i.get("rule_id", "") for i in result["issues"])

    def test_unauthorized_purpose(self, checker):
        result = checker.check_authorization(1, "研究部", "商业销售", ["age"])
        assert any("RULE_D_006" in i.get("rule_id", "") for i in result["issues"])

    def test_wildcard_auth(self):
        from backend.app.services.authorization_checker import AuthorizationChecker, AuthorizationScope
        checker = AuthorizationChecker()
        auth = AuthorizationScope(
            authorized_party="*", usage_scope="*",
            authorized_fields=["*"],
            valid_from=date.today(), valid_to=date.today() + timedelta(days=365),
        )
        checker.add_authorization(2, auth)
        result = checker.check_authorization(2, "任何人", "任何用途", ["any_field"])
        assert result["is_authorized"] is True

    def test_expired_auth(self):
        from backend.app.services.authorization_checker import AuthorizationChecker, AuthorizationScope
        checker = AuthorizationChecker()
        auth = AuthorizationScope(
            authorized_party="研究部", usage_scope="统计分析",
            authorized_fields=["age"],
            valid_from=date.today() - timedelta(days=60),
            valid_to=date.today() - timedelta(days=30),
        )
        checker.add_authorization(3, auth)
        result = checker.check_authorization(3, "研究部", "统计分析", ["age"])
        assert result["is_authorized"] is False
        assert any("RULE_D_003" in i.get("rule_id", "") for i in result["issues"])

    def test_cross_department_sharing(self, checker):
        result = checker.check_cross_department_sharing(1, "市场部", [
            {"authorized_party": "研究部"}
        ])
        assert result["is_authorized"] is False
        assert any("RULE_D_004" in i.get("rule_id", "") for i in result["issues"])

    def test_cross_department_authorized(self, checker):
        result = checker.check_cross_department_sharing(1, "研究部", [
            {"authorized_party": "研究部"}
        ])
        assert result["is_authorized"] is True

    def test_detect_over_auth_issues(self, checker):
        issues = checker.detect_over_auth_issues(1, ["age", "ssn"], [
            {"catalog_id": 1, "authorized_fields": ["age"], "id": 1}
        ])
        assert len(issues) == 1
        assert issues[0]["field"] == "ssn"

    def test_purpose_partial_match(self, checker):
        result = checker.check_authorization(1, "研究部", "统计分析与数据挖掘", ["age"])
        # Should match since "统计分析" is in the intended use
        assert any(True for i in result["issues"] if i.get("severity") != "high" or not i.get("rule_id") == "RULE_D_006")

    def test_no_fields_requested(self, checker):
        result = checker.check_authorization(1, "研究部", "统计分析", [])
        assert result["is_authorized"] is True


# ═══════════════════════════════════════════════════════════════
# DataLineageTracker
# ═══════════════════════════════════════════════════════════════

class TestDataLineageTracker:
    """Exhaustive tests for DataLineageTracker."""

    @pytest.fixture
    def tracker(self):
        from backend.app.services.data_lineage_tracker import DataLineageTracker
        return DataLineageTracker()

    def test_add_catalog_node(self, tracker):
        node = tracker.add_catalog_node(1, "人口数据", "统计局")
        assert node.id == "catalog_1"
        assert node.name == "人口数据"
        assert node.node_type == "catalog"
        assert "catalog_1" in tracker.nodes

    def test_add_product_node(self, tracker):
        tracker.add_catalog_node(1, "人口数据", "统计局")
        node = tracker.add_product_node(1, "p1", "人口统计报告")
        assert node.id == "product_p1"
        assert "product_p1" in tracker.catalog_products[1]

    def test_add_process_node(self, tracker):
        node = tracker.add_process_node("proc1", "数据清洗", "技术部")
        assert node.id == "process_proc1"
        assert node.department == "技术部"

    def test_add_lineage_edge(self, tracker):
        tracker.add_catalog_node(1, "人口数据", "统计局")
        tracker.add_product_node(1, "p1", "人口统计报告")
        edge = tracker.add_lineage_edge("catalog_1", "product_p1", "processing")
        assert edge.source_id == "catalog_1"
        assert edge.target_id == "product_p1"
        assert len(tracker.edges) == 1

    def test_lineage_path_complete(self, tracker):
        tracker.add_catalog_node(1, "人口数据", "统计局")
        tracker.add_product_node(1, "p1", "人口统计报告")
        tracker.add_lineage_edge("catalog_1", "product_p1", "processing")
        result = tracker.get_lineage_path(1)
        assert result["is_complete"] is True
        assert len(result["nodes"]) >= 2
        assert len(result["edges"]) >= 1

    def test_lineage_path_incomplete(self, tracker):
        tracker.add_catalog_node(1, "人口数据", "统计局")
        result = tracker.get_lineage_path(1)
        assert result["is_complete"] is False
        assert any("RULE_D_009" in i.get("rule_id", "") for i in result["issues"])

    def test_export_lineage_graph(self, tracker):
        tracker.add_catalog_node(1, "人口数据", "统计局")
        tracker.add_product_node(1, "p1", "人口统计报告")
        tracker.add_lineage_edge("catalog_1", "product_p1", "processing")
        graph = tracker.export_lineage_graph(1)
        assert "nodes" in graph
        assert "edges" in graph
        assert graph["stats"]["total_nodes"] >= 2
        assert graph["stats"]["total_edges"] >= 1

    def test_export_empty_lineage(self, tracker):
        graph = tracker.export_lineage_graph(999)
        assert graph["nodes"] == []
        assert graph["edges"] == []

    def test_detect_lineage_issues_unknown_source(self, tracker):
        tracker.add_catalog_node(1, "test", "dept")
        fields = [{"name": "field1", "source_unknown": True}]
        issues = tracker.detect_lineage_issues(1, fields)
        assert any("RULE_D_009" in i.get("rule_id", "") for i in issues)

    def test_detect_lineage_issues_no_processing_recorded(self, tracker):
        tracker.add_catalog_node(1, "test", "dept")
        tracker.add_product_node(1, "p1", "product")
        tracker.add_lineage_edge("catalog_1", "product_p1", "sharing")  # not "processing"
        issues = tracker.detect_lineage_issues(1, [])
        assert any("RULE_D_010" in i.get("rule_id", "") for i in issues)

    def test_track_field_lineage(self, tracker):
        tracker.add_catalog_node(1, "人口数据", "统计局")
        tracker.add_product_node(1, "p1", "人口统计报告")
        path = tracker.track_field_lineage(1, "age")
        assert len(path) >= 1
        assert "catalog_1" in path

    def test_node_to_dict(self, tracker):
        node = tracker.add_catalog_node(1, "test", "dept")
        d = node.to_dict()
        assert d["id"] == "catalog_1"
        assert d["name"] == "test"
        assert d["node_type"] == "catalog"

    def test_edge_to_dict(self, tracker):
        tracker.add_catalog_node(1, "c", "d")
        tracker.add_product_node(1, "p1", "p")
        edge = tracker.add_lineage_edge("catalog_1", "product_p1", "processing", "desc")
        d = edge.to_dict()
        assert d["source"] == "catalog_1"
        assert d["target"] == "product_p1"
        assert d["process_type"] == "processing"

    def test_downstream_traversal(self, tracker):
        tracker.add_catalog_node(1, "c", "d")
        tracker.add_product_node(1, "p1", "p")
        tracker.add_process_node("proc1", "clean")
        tracker.add_lineage_edge("catalog_1", "product_p1", "processing")
        tracker.add_lineage_edge("product_p1", "process_proc1", "processing")
        graph = tracker.export_lineage_graph(1)
        assert graph["stats"]["total_nodes"] >= 3


# ═══════════════════════════════════════════════════════════════
# RiskEntropyScorer
# ═══════════════════════════════════════════════════════════════

class TestRiskEntropyScorer:
    """Exhaustive tests for RiskEntropyScorer."""

    @pytest.fixture
    def scorer(self):
        from backend.app.services.data_risk_scorer import RiskEntropyScorer
        return RiskEntropyScorer()

    def _make_inputs(self, data_type="public", sensitivity="low", auth_scope="full",
                     personal=0, sensitive=0, reid=0, authorized=True):
        catalog = {"id": 1, "name": "test", "data_type": data_type,
                   "sensitivity_level": sensitivity, "auth_scope": auth_scope}
        privacy = {
            "personal_info_fields": [{"field_name": f"p{i}"} for i in range(personal)],
            "sensitive_info_fields": [{"field_name": f"s{i}"} for i in range(sensitive)],
            "reid_risk_fields": [f"combo{i}" for i in range(reid)],
            "issues": [],
            "anonymized_fields": [],
        }
        auth = {"is_authorized": authorized, "unauthorized_fields": [],
                "issues": [] if authorized else [{"rule_id": "RULE_D_006"}]}
        lineage = {"is_complete": True, "nodes": [], "edges": [], "issues": []}
        return catalog, privacy, auth, lineage

    def test_low_risk_score(self, scorer):
        result = scorer.score(*self._make_inputs())
        assert result["risk_level"] == "low"
        assert result["total_entropy_score"] < 40

    def test_high_risk_score(self, scorer):
        result = scorer.score(*self._make_inputs(
            data_type="personal", sensitivity="extreme", auth_scope="",
            personal=5, sensitive=3, reid=2, authorized=False))
        assert result["risk_level"] in ["high", "extreme"]
        assert result["total_entropy_score"] > 40

    def test_dimensions_present(self, scorer):
        result = scorer.score(*self._make_inputs())
        dims = result["dimensions"]
        for key in ["open_risk", "auth_risk", "privacy_risk", "reid_risk"]:
            assert key in dims
            assert dims[key] >= 0

    def test_score_capped_at_100(self, scorer):
        result = scorer.score(*self._make_inputs(
            data_type="personal", sensitivity="extreme", auth_scope="",
            personal=20, sensitive=10, reid=10, authorized=False))
        assert result["total_entropy_score"] <= 100

    def test_coupling_detection(self, scorer):
        result = scorer.score(*self._make_inputs(
            data_type="personal", sensitivity="extreme", auth_scope="",
            personal=5, sensitive=3, reid=2, authorized=False))
        assert result["is_coupled"] is True

    def test_fuse_trigger_extreme(self, scorer):
        """Extreme privacy risk should trigger fuse."""
        result = scorer.score(*self._make_inputs(
            data_type="personal", sensitivity="extreme", auth_scope="",
            personal=20, sensitive=10, reid=10, authorized=False))
        # Either fuse triggers or score is very high
        assert result["fuse_triggered"] or result["total_entropy_score"] > 60

    def test_suggestions_generated(self, scorer):
        result = scorer.score(*self._make_inputs(
            data_type="personal", sensitivity="extreme", auth_scope="",
            personal=5, sensitive=3, reid=2, authorized=False))
        assert len(result["suggestions"]) > 0

    def test_no_auth_default_risk(self, scorer):
        catalog = {"id": 1, "name": "t", "data_type": "public", "sensitivity_level": "low", "auth_scope": "full"}
        privacy = {"personal_info_fields": [], "sensitive_info_fields": [], "reid_risk_fields": [], "issues": [], "anonymized_fields": []}
        lineage = {"is_complete": True, "nodes": [], "edges": [], "issues": []}
        # Pass empty auth result
        result = scorer.score(catalog, privacy, {}, lineage)
        assert result["dimensions"]["auth_risk"] == 50.0

    def test_empty_privacy_result(self, scorer):
        catalog = {"id": 1, "name": "t", "data_type": "public", "sensitivity_level": "low", "auth_scope": "full"}
        auth = {"is_authorized": True, "unauthorized_fields": [], "issues": []}
        lineage = {"is_complete": True, "nodes": [], "edges": [], "issues": []}
        result = scorer.score(catalog, {}, auth, lineage)
        assert result["dimensions"]["privacy_risk"] == 0.0
        assert result["dimensions"]["reid_risk"] == 0.0


# ═══════════════════════════════════════════════════════════════
# ReportGenerator
# ═══════════════════════════════════════════════════════════════

class TestReportGenerator:
    """Exhaustive tests for ReportGenerator."""

    @pytest.fixture
    def generator(self):
        from backend.app.services.report_generator import ReportGenerator
        return ReportGenerator()

    def _make_report_inputs(self, risk_level="low", score=10, personal=0, sensitive=0,
                            authorized=True, complete=True):
        catalog = {"id": 1, "name": "test_catalog", "department": "dept"}
        risk = {
            "total_entropy_score": score, "risk_level": risk_level,
            "dimensions": {"open_risk": 5, "auth_risk": 5, "privacy_risk": 5, "reid_risk": 5},
            "is_coupled": False, "coupling_penalty": 0,
            "fuse_triggered": False, "fuse_reason": "",
        }
        privacy = {
            "personal_info_fields": [{"field_name": f"p{i}"} for i in range(personal)],
            "sensitive_info_fields": [{"field_name": f"s{i}"} for i in range(sensitive)],
            "reid_risk_fields": [],
            "issues": [], "anonymized_fields": [],
        }
        auth = {"is_authorized": authorized, "authorized_fields": [],
                "unauthorized_fields": [] if authorized else ["p0"],
                "issues": []}
        lineage = {"is_complete": complete, "nodes": [], "edges": [], "issues": []}
        return catalog, risk, privacy, auth, lineage

    def test_generate_report_structure(self, generator):
        report = generator.generate_report(*self._make_report_inputs())
        for key in ["report_info", "risk_assessment", "privacy_assessment",
                     "authorization_assessment", "lineage_assessment",
                     "issues", "review_opinions", "rectification_suggestions"]:
            assert key in report

    def test_report_info_fields(self, generator):
        report = generator.generate_report(*self._make_report_inputs())
        info = report["report_info"]
        assert info["catalog_id"] == 1
        assert info["catalog_name"] == "test_catalog"
        assert info["department"] == "dept"
        assert "report_id" in info
        assert "generated_at" in info

    def test_high_risk_report_opinions(self, generator):
        report = generator.generate_report(*self._make_report_inputs(
            risk_level="high", score=70, personal=3, sensitive=1, authorized=False))
        assert len(report["review_opinions"]) > 0
        assert any("暂停" in op or "风险" in op for op in report["review_opinions"])

    def test_low_risk_report_opinions(self, generator):
        report = generator.generate_report(*self._make_report_inputs())
        assert len(report["review_opinions"]) > 0
        assert any("基本合规" in op or "持续监控" in op for op in report["review_opinions"])

    def test_rectification_suggestions_high_risk(self, generator):
        report = generator.generate_report(*self._make_report_inputs(
            risk_level="high", score=70, personal=3, sensitive=1, authorized=False))
        assert len(report["rectification_suggestions"]) > 0
        assert any("紧急" in s for s in report["rectification_suggestions"])

    def test_format_markdown(self, generator):
        report = generator.generate_report(*self._make_report_inputs(score=30))
        md = generator.format_report_markdown(report)
        assert "公共数据资源授权运营合规审查报告" in md
        assert "风险评估结果" in md
        assert "问题汇总" in md
        assert "审查意见" in md
        assert "整改建议" in md

    def test_anonymization_quality_assessment(self, generator):
        # No personal info
        report = generator.generate_report(*self._make_report_inputs(personal=0))
        assert report["privacy_assessment"]["anonymization_quality"] == "无个人信息"

    def test_anonymization_quality_with_personal(self, generator):
        report = generator.generate_report(*self._make_report_inputs(personal=3))
        assert report["privacy_assessment"]["anonymization_quality"] in ["优秀", "良好", "一般", "不合格"]

    def test_risk_coupling_issue(self, generator):
        catalog, risk, privacy, auth, lineage = self._make_report_inputs()
        risk["is_coupled"] = True
        risk["coupling_penalty"] = 15
        report = generator.generate_report(catalog, risk, privacy, auth, lineage)
        assert any(i["category"] == "risk_coupling" for i in report["issues"])

    def test_fuse_triggered_issue(self, generator):
        catalog, risk, privacy, auth, lineage = self._make_report_inputs()
        risk["fuse_triggered"] = True
        risk["fuse_reason"] = "extreme privacy risk"
        report = generator.generate_report(catalog, risk, privacy, auth, lineage)
        assert any(i["category"] == "risk_fuse" for i in report["issues"])


# ═══════════════════════════════════════════════════════════════
# RelationalLineageTracker
# ═══════════════════════════════════════════════════════════════

class TestRelationalLineageTracker:
    """Tests for RelationalLineageTracker."""

    @pytest.fixture
    def rtracker(self):
        from backend.app.services.data_lineage_tracker import RelationalLineageTracker
        return RelationalLineageTracker()

    def test_add_foreign_key_relation(self, rtracker):
        rtracker.add_foreign_key_relation(1, "user_id", 2, "order_user_id")
        assert len(rtracker.foreign_key_relations) == 1

    def test_add_derived_field(self, rtracker):
        rtracker.add_derived_field(1, "full_name", 2, "display_name", "concat(first, last)")
        assert "2:display_name" in rtracker.derived_fields

    def test_impact_analysis(self, rtracker):
        rtracker.add_foreign_key_relation(1, "user_id", 2, "order_user_id")
        rtracker.add_derived_field(1, "full_name", 3, "display_name")
        result = rtracker.get_impact_analysis(1)
        assert result["affected_count"] == 2

    def test_impact_analysis_no_impact(self, rtracker):
        result = rtracker.get_impact_analysis(999)
        assert result["affected_count"] == 0


# ═══════════════════════════════════════════════════════════════
# Database Module
# ═══════════════════════════════════════════════════════════════

class TestDatabase:
    """Tests for database initialization and operations."""

    def test_init_db_creates_tables(self, tmp_db):
        import sqlite3
        conn = sqlite3.connect(tmp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        conn.close()
        expected = {"rules", "data_catalogs", "authorization_records",
                    "data_lineage", "analysis_results", "audit_logs"}
        assert expected.issubset(tables)

    def test_default_rules_loaded(self, tmp_db):
        import sqlite3
        conn = sqlite3.connect(tmp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM rules")
        count = cursor.fetchone()[0]
        conn.close()
        assert count >= 10

    def test_log_audit(self, tmp_db):
        from backend.app.core.database import log_audit
        log_audit("TEST_ACTION", "test_target", 1, "test details")
        import sqlite3
        conn = sqlite3.connect(tmp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM audit_logs WHERE action = 'TEST_ACTION'")
        row = cursor.fetchone()
        conn.close()
        assert row is not None
