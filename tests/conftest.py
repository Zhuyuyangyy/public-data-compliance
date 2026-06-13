"""Shared fixtures for the public-data-compliance test suite."""
import os
import sys
import tempfile
import pytest
from datetime import date, timedelta

# Ensure project root is on sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


@pytest.fixture
def tmp_db(tmp_path):
    """Provide a temporary SQLite database path and patch database module to use it."""
    db_path = str(tmp_path / "test_compliance.db")
    import backend.app.core.database as db_mod
    original_path = db_mod.DB_PATH
    db_mod.DB_PATH = db_path
    db_mod.init_db()
    yield db_path
    db_mod.DB_PATH = original_path


@pytest.fixture
def sample_public_fields():
    """Sample fields representing public (non-personal) data."""
    return [
        {"name": "weather_data", "description": "天气统计数据", "data_type": "float", "sensitivity": "low"},
        {"name": "traffic_flow", "description": "交通流量数据", "data_type": "int", "sensitivity": "low"},
        {"name": "air_quality", "description": "空气质量指数", "data_type": "float", "sensitivity": "low"},
    ]


@pytest.fixture
def sample_personal_fields():
    """Sample fields containing personal information."""
    return [
        {"name": "姓名", "description": "用户姓名", "data_type": "string", "sensitivity": "medium"},
        {"name": "手机号", "description": "联系电话", "data_type": "string", "sensitivity": "medium"},
        {"name": "邮箱", "description": "电子邮箱", "data_type": "string", "sensitivity": "medium"},
        {"name": "身份证号", "description": "居民身份证号码", "data_type": "string", "sensitivity": "high"},
    ]


@pytest.fixture
def sample_sensitive_fields():
    """Sample fields containing sensitive personal information."""
    return [
        {"name": "健康状况", "description": "个人健康医疗记录", "data_type": "string", "sensitivity": "extreme"},
        {"name": "基因信息", "description": "基因检测数据", "data_type": "string", "sensitivity": "extreme"},
        {"name": "人脸特征", "description": "人脸识别特征值", "data_type": "bytes", "sensitivity": "extreme"},
        {"name": "位置轨迹", "description": "GPS位置轨迹数据", "data_type": "json", "sensitivity": "high"},
    ]


@pytest.fixture
def sample_mixed_fields():
    """Sample fields with mixed types including re-identification risks."""
    return [
        {"name": "姓名", "description": "用户姓名", "data_type": "string", "sensitivity": "medium"},
        {"name": "性别", "description": "gender", "data_type": "string", "sensitivity": "low"},
        {"name": "年龄", "description": "age", "data_type": "int", "sensitivity": "low"},
        {"name": "地区", "description": "所在地区", "data_type": "string", "sensitivity": "low"},
        {"name": "职业", "description": "occupation", "data_type": "string", "sensitivity": "low"},
        {"name": "健康状况", "description": "health status", "data_type": "string", "sensitivity": "extreme"},
    ]


@pytest.fixture
def sample_catalog_data():
    """Sample catalog database row data."""
    return {
        "id": 1,
        "name": "人口统计数据",
        "department": "统计局",
        "data_type": "personal",
        "fields_json": '[{"name":"姓名","description":"用户姓名"},{"name":"年龄","description":"age"}]',
        "sensitivity_level": "medium",
        "source_info": "政务数据平台",
        "auth_scope": "统计分析",
    }


@pytest.fixture
def sample_low_risk_catalog():
    """Low risk catalog data for scoring tests."""
    return {
        "id": 10,
        "name": "天气数据",
        "data_type": "public",
        "sensitivity_level": "low",
        "auth_scope": "全面开放",
    }


@pytest.fixture
def sample_high_risk_catalog():
    """High risk catalog data for scoring tests."""
    return {
        "id": 20,
        "name": "个人医疗档案",
        "data_type": "personal",
        "sensitivity_level": "extreme",
        "auth_scope": "",
    }
