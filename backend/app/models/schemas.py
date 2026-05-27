"""
Pydantic 数据模型 - API 请求/响应结构
公共数据授权运营合规审查与数据风险熵评估系统
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class DataType(str, Enum):
    PUBLIC = "public"          # 公共数据
    SENSITIVE = "sensitive"    # 敏感数据
    PERSONAL = "personal"      # 个人信息

class SensitivityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"

class AuthorizationStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"

# ============ 请求模型 ============

class FieldInfo(BaseModel):
    """字段信息"""
    name: str
    description: Optional[str] = ""
    data_type: Optional[str] = ""
    sensitivity: str = "low"
    is_personal_info: bool = False
    is_sensitive_info: bool = False
    can_reidentify: bool = False

class DataCatalogRegisterRequest(BaseModel):
    """数据目录注册请求"""
    name: str = Field(..., description="数据目录名称")
    department: str = Field(..., description="所属部门")
    data_type: str = Field(..., description="数据类型: public/sensitive/personal")
    fields: List[FieldInfo] = Field(..., description="字段列表")
    source_info: Optional[str] = Field(default="", description="数据来源信息")
    auth_scope: Optional[str] = Field(default="", description="授权范围")
    sensitivity_level: str = Field(default="low", description="敏感等级")

class AuthorizationCreateRequest(BaseModel):
    """授权记录创建请求"""
    catalog_id: int = Field(..., description="数据目录ID")
    authorized_party: str = Field(..., description="授权对象")
    usage_scope: str = Field(..., description="使用范围")
    valid_from: str = Field(..., description="授权起始日期 YYYY-MM-DD")
    valid_to: str = Field(..., description="授权截止日期 YYYY-MM-DD")

class DataProductUploadRequest(BaseModel):
    """数据产品上传请求"""
    catalog_id: int = Field(..., description="关联的数据目录ID")
    product_name: str = Field(..., description="数据产品名称")
    product_description: str = Field(..., description="产品描述")
    fields: List[FieldInfo] = Field(..., description="产品包含的字段")
    process_description: Optional[str] = Field(default="", description="数据加工说明")

class AuthorizationCheckRequest(BaseModel):
    """授权范围检查请求"""
    catalog_id: int = Field(..., description="数据目录ID")
    requester: str = Field(..., description="请求方")
    intended_use: str = Field(..., description="预期用途")
    requested_fields: List[str] = Field(..., description="请求的字段列表")

class PrivacyRiskAnalyzeRequest(BaseModel):
    """隐私风险分析请求"""
    catalog_id: Optional[int] = Field(default=None, description="数据目录ID")
    fields: List[FieldInfo] = Field(..., description="待分析的字段列表")

# ============ 响应模型 ============

class DataCatalogResponse(BaseModel):
    """数据目录响应"""
    id: int
    name: str
    department: str
    data_type: str
    fields_count: int
    sensitivity_level: str
    source_info: str
    auth_scope: str
    created_at: str

class AuthorizationResponse(BaseModel):
    """授权记录响应"""
    id: int
    catalog_id: int
    authorized_party: str
    usage_scope: str
    valid_from: str
    valid_to: str
    status: str
    created_at: str

class RiskScoreResponse(BaseModel):
    """风险评分响应"""
    catalog_id: int
    total_score: float
    risk_level: str
    open_risk: float
    auth_risk: float
    privacy_risk: float
    reid_risk: float
    details: List[Dict[str, Any]]
    suggestions: List[str]
    created_at: str

class LineageNode(BaseModel):
    """血缘节点"""
    id: str
    name: str
    node_type: str
    department: Optional[str] = None

class LineageEdge(BaseModel):
    """血缘边"""
    source: str
    target: str
    process_type: str

class LineageResponse(BaseModel):
    """数据血缘响应"""
    catalog_id: int
    nodes: List[LineageNode]
    edges: List[LineageEdge]
    is_complete: bool

class AuditLogEntry(BaseModel):
    """审计日志条目"""
    id: int
    action: str
    target_type: Optional[str]
    target_id: Optional[int]
    details: Optional[str]
    created_at: str

class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    service: str
    version: str

class AuthorizationCheckResponse(BaseModel):
    """授权检查响应"""
    is_authorized: bool
    catalog_id: int
    requester: str
    authorized_fields: List[str]
    unauthorized_fields: List[str]
    issues: List[str]
    suggestions: List[str]

class PrivacyRiskResponse(BaseModel):
    """隐私风险分析响应"""
    catalog_id: Optional[int]
    personal_info_count: int
    sensitive_info_count: int
    reid_risk_count: int
    risk_level: str
    risk_score: float
    anonymization_issues: List[str]
    suggestions: List[str]

class ReportResponse(BaseModel):
    """合规报告响应"""
    catalog_id: int
    catalog_name: str
    department: str
    risk_level: str
    total_score: float
    open_risk: float
    auth_risk: float
    privacy_risk: float
    reid_risk: float
    issues: List[Dict[str, Any]]
    suggestions: List[str]
    review_opinions: List[str]
    rectification_suggestions: List[str]
    generated_at: str