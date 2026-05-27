"""
API路由 - 公共数据授权运营合规审查系统
对应专利：
1. 一种基于数据血缘图谱的公共数据授权范围校验方法
2. 一种面向公共数据运营的敏感字段风险熵评估方法
3. 一种基于语义闭环的数据产品合规审查方法
4. 一种公共数据授权运营全过程审计追踪系统
"""
import json
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    DataCatalogRegisterRequest, DataCatalogResponse,
    AuthorizationCreateRequest, AuthorizationResponse,
    DataProductUploadRequest,
    AuthorizationCheckRequest, AuthorizationCheckResponse,
    PrivacyRiskAnalyzeRequest, PrivacyRiskResponse,
    RiskScoreResponse, LineageResponse, LineageNode, LineageEdge,
    AuditLogEntry, HealthResponse, ReportResponse
)
from app.core.database import get_conn, log_audit
from app.services.data_catalog_parser import parse_data_catalog
from app.services.data_lineage_tracker import get_lineage_tracker
from app.services.authorization_checker import AuthorizationScope, get_authorization_checker
from app.services.privacy_risk_detector import detect_privacy_risk
from app.services.data_risk_scorer import score_data_risk
from app.services.report_generator import generate_compliance_report

router = APIRouter(prefix="/api/v1", tags=["公共数据合规审查"])


# ============ 工具函数 ============

def save_catalog(name: str, department: str, data_type: str,
                 fields: List[Dict], source_info: str,
                 auth_scope: str, sensitivity_level: str) -> int:
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO data_catalogs (name, department, data_type, fields_json, source_info, auth_scope, sensitivity_level)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (name, department, data_type, json.dumps(fields, ensure_ascii=False),
          source_info, auth_scope, sensitivity_level))
    catalog_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return catalog_id

def get_catalog(catalog_id: int) -> Optional[Dict]:
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM data_catalogs WHERE id = ?", (catalog_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def save_authorization(catalog_id: int, authorized_party: str, usage_scope: str,
                      valid_from: str, valid_to: str) -> int:
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO authorization_records (catalog_id, authorized_party, usage_scope, valid_from, valid_to)
        VALUES (?, ?, ?, ?, ?)
    """, (catalog_id, authorized_party, usage_scope, valid_from, valid_to))
    auth_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    # 同步到授权检查器
    checker = get_authorization_checker()
    auth = AuthorizationScope(
        authorized_party=authorized_party,
        usage_scope=usage_scope,
        authorized_fields=["*"],  # 默认全部授权
        valid_from=datetime.strptime(valid_from, "%Y-%m-%d").date(),
        valid_to=datetime.strptime(valid_to, "%Y-%m-%d").date()
    )
    checker.add_authorization(catalog_id, auth)
    
    return auth_id

def get_authorizations(catalog_id: int) -> List[Dict]:
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM authorization_records WHERE catalog_id = ?", (catalog_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def save_analysis_result(catalog_id: int, risk_result: Dict):
    conn = get_conn()
    cursor = conn.cursor()
    
    dims = risk_result.get("dimensions", {})
    
    cursor.execute("""
        INSERT INTO analysis_results 
        (catalog_id, risk_score, risk_level, open_risk, auth_risk, privacy_risk, reid_risk, details_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        catalog_id,
        risk_result.get("total_entropy_score", 0),
        risk_result.get("risk_level", "low"),
        dims.get("open_risk", 0),
        dims.get("auth_risk", 0),
        dims.get("privacy_risk", 0),
        dims.get("reid_risk", 0),
        json.dumps(risk_result, ensure_ascii=False)
    ))
    result_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return result_id

def get_analysis_result(catalog_id: int) -> Optional[Dict]:
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM analysis_results WHERE catalog_id = ? ORDER BY id DESC LIMIT 1", (catalog_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


# ============ API 接口 ============

@router.post("/register_catalog", response_model=DataCatalogResponse)
async def register_catalog(req: DataCatalogRegisterRequest):
    """
    S1: 数据目录注册
    对应专利1 S1: 数据目录解析与敏感等级识别
    """
    # 解析数据目录
    parse_result = parse_data_catalog(
        name=req.name,
        department=req.department,
        data_type=req.data_type,
        fields=[f.dict() for f in req.fields],
        source_info=req.source_info,
        auth_scope=req.auth_scope,
        sensitivity_level=req.sensitivity_level
    )
    
    # 保存到数据库
    catalog_id = save_catalog(
        name=req.name,
        department=req.department,
        data_type=parse_result.get("detected_data_type", req.data_type),
        fields=[f.dict() for f in req.fields],
        source_info=req.source_info,
        auth_scope=req.auth_scope,
        sensitivity_level=parse_result.get("recommended_sensitivity", req.sensitivity_level)
    )
    
    # 添加血缘节点
    tracker = get_lineage_tracker()
    tracker.add_catalog_node(catalog_id, req.name, req.department)
    
    # 审计日志
    log_audit("REGISTER_CATALOG", "data_catalog", catalog_id, 
              f"注册数据目录: {req.name}, 检测到{len(parse_result.get('issues', []))}个问题")
    
    return DataCatalogResponse(
        id=catalog_id,
        name=req.name,
        department=req.department,
        data_type=parse_result.get("detected_data_type", req.data_type),
        fields_count=len(req.fields),
        sensitivity_level=parse_result.get("recommended_sensitivity", req.sensitivity_level),
        source_info=req.source_info,
        auth_scope=req.auth_scope,
        created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )


@router.post("/create_authorization", response_model=AuthorizationResponse)
async def create_authorization(req: AuthorizationCreateRequest):
    """
    S2: 创建授权记录
    对应专利1 S2: 授权范围定义与校验
    """
    catalog = get_catalog(req.catalog_id)
    if not catalog:
        raise HTTPException(status_code=404, detail="数据目录不存在")
    
    auth_id = save_authorization(
        catalog_id=req.catalog_id,
        authorized_party=req.authorized_party,
        usage_scope=req.usage_scope,
        valid_from=req.valid_from,
        valid_to=req.valid_to
    )
    
    log_audit("CREATE_AUTHORIZATION", "authorization", auth_id,
              f"创建授权记录: {req.authorized_party}")
    
    return AuthorizationResponse(
        id=auth_id,
        catalog_id=req.catalog_id,
        authorized_party=req.authorized_party,
        usage_scope=req.usage_scope,
        valid_from=req.valid_from,
        valid_to=req.valid_to,
        status="active",
        created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )


@router.post("/upload_data_product")
async def upload_data_product(req: DataProductUploadRequest):
    """
    S3: 上传数据产品
    对应专利3 S2: 数据产品语义闭环审查
    """
    catalog = get_catalog(req.catalog_id)
    if not catalog:
        raise HTTPException(status_code=404, detail="数据目录不存在")
    
    # 添加产品节点到血缘图谱
    tracker = get_lineage_tracker()
    product_id = f"{req.catalog_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    tracker.add_product_node(req.catalog_id, product_id, req.product_name)
    tracker.add_lineage_edge(
        source_id=f"catalog_{req.catalog_id}",
        target_id=f"product_{product_id}",
        process_type="product_creation",
        process_desc=req.process_description or "数据产品创建"
    )
    
    # 解析产品字段
    parse_result = parse_data_catalog(
        name=req.product_name,
        department=catalog["department"],
        data_type=catalog["data_type"],
        fields=[f.dict() for f in req.fields],
        source_info=catalog["source_info"],
        auth_scope=catalog["auth_scope"],
        sensitivity_level=catalog["sensitivity_level"]
    )
    
    log_audit("UPLOAD_DATA_PRODUCT", "data_product", None,
              f"上传数据产品: {req.product_name}, 目录ID: {req.catalog_id}")
    
    return {
        "message": "数据产品上传成功",
        "product_id": product_id,
        "catalog_id": req.catalog_id,
        "catalog_name": catalog["name"],
        "parse_result": parse_result,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }


@router.post("/check_authorization", response_model=AuthorizationCheckResponse)
async def check_authorization(req: AuthorizationCheckRequest):
    """
    S4: 检查授权范围
    对应专利1 S3: 基于血缘图谱的授权范围校验
    """
    catalog = get_catalog(req.catalog_id)
    if not catalog:
        raise HTTPException(status_code=404, detail="数据目录不存在")
    
    # 获取授权记录
    auth_list = get_authorizations(req.catalog_id)
    
    # 调用授权检查器
    checker = get_authorization_checker()
    
    # 同步授权记录到检查器
    for auth in auth_list:
        scope = AuthorizationScope(
            authorized_party=auth["authorized_party"],
            usage_scope=auth["usage_scope"],
            authorized_fields=["*"],
            valid_from=datetime.strptime(auth["valid_from"], "%Y-%m-%d").date(),
            valid_to=datetime.strptime(auth["valid_to"], "%Y-%m-%d").date()
        )
        checker.add_authorization(req.catalog_id, scope)
    
    # 执行检查
    result = checker.check_authorization(
        catalog_id=req.catalog_id,
        requester=req.requester,
        intended_use=req.intended_use,
        requested_fields=req.requested_fields
    )
    
    log_audit("CHECK_AUTHORIZATION", "authorization", req.catalog_id,
              f"授权检查: {req.requester}, 用途: {req.intended_use}")
    
    return AuthorizationCheckResponse(**result)


@router.post("/analyze_privacy_risk", response_model=PrivacyRiskResponse)
async def analyze_privacy_risk(req: PrivacyRiskAnalyzeRequest):
    """
    S5: 分析隐私风险
    对应专利2 S3: 敏感字段风险熵评估
    """
    if req.catalog_id:
        catalog = get_catalog(req.catalog_id)
        if not catalog:
            raise HTTPException(status_code=404, detail="数据目录不存在")
        fields = json.loads(catalog.get("fields_json", "[]"))
    else:
        fields = [f.dict() for f in req.fields]
    
    # 执行隐私风险检测
    risk_result = detect_privacy_risk(fields)
    
    log_audit("ANALYZE_PRIVACY_RISK", "privacy_risk", req.catalog_id,
              f"隐私风险分析: 检测到{len(risk_result.get('issues', []))}个问题")
    
    return PrivacyRiskResponse(
        catalog_id=req.catalog_id,
        personal_info_count=len(risk_result.get("personal_info_fields", [])),
        sensitive_info_count=len(risk_result.get("sensitive_info_fields", [])),
        reid_risk_count=len(risk_result.get("reid_risk_fields", [])),
        risk_level=risk_result.get("risk_level", "low"),
        risk_score=risk_result.get("risk_score", 0),
        anonymization_issues=[i["issue"] for i in risk_result.get("issues", []) if i.get("rule_id") == "RULE_D_007"],
        suggestions=risk_result.get("suggestions", [])
    )


@router.get("/get_risk_report/{catalog_id}", response_model=ReportResponse)
async def get_risk_report(catalog_id: int):
    """
    S6: 获取风险报告
    对应专利2 S4: 综合风险熵评分与等级判定
    对应专利4 S5: 全过程审计追踪
    """
    catalog = get_catalog(catalog_id)
    if not catalog:
        raise HTTPException(status_code=404, detail="数据目录不存在")
    
    # 获取历史分析结果
    existing_result = get_analysis_result(catalog_id)
    
    if not existing_result:
        # 首次分析
        fields = json.loads(catalog.get("fields_json", "[]"))
        
        # 隐私风险检测
        privacy_result = detect_privacy_risk(fields)
        
        # 授权检查
        auth_list = get_authorizations(catalog_id)
        auth_result = {"is_authorized": False, "issues": [], "authorized_fields": [], "unauthorized_fields": []}
        if auth_list:
            checker = get_authorization_checker()
            for auth in auth_list:
                scope = AuthorizationScope(
                    authorized_party=auth["authorized_party"],
                    usage_scope=auth["usage_scope"],
                    authorized_fields=["*"],
                    valid_from=datetime.strptime(auth["valid_from"], "%Y-%m-%d").date(),
                    valid_to=datetime.strptime(auth["valid_to"], "%Y-%m-%d").date()
                )
                checker.add_authorization(catalog_id, scope)
            auth_result = checker.check_authorization(catalog_id, "system", "合规审查", [f["name"] for f in fields])
        
        # 血缘分析
        tracker = get_lineage_tracker()
        lineage_result = tracker.get_lineage_path(catalog_id)
        
        # 综合风险评分
        risk_result = score_data_risk(catalog, privacy_result, auth_result, lineage_result)
        
        # 保存结果
        save_analysis_result(catalog_id, risk_result)
        
        # 生成报告
        report_data = generate_compliance_report(catalog, risk_result, privacy_result, auth_result, lineage_result)
    else:
        # 使用历史结果生成报告
        risk_result = json.loads(existing_result.get("details_json", "{}"))
        
        fields = json.loads(catalog.get("fields_json", "[]"))
        privacy_result = detect_privacy_risk(fields)
        auth_result = {"is_authorized": False, "issues": [], "authorized_fields": [], "unauthorized_fields": []}
        tracker = get_lineage_tracker()
        lineage_result = tracker.get_lineage_path(catalog_id)
        
        report_data = generate_compliance_report(catalog, risk_result, privacy_result, auth_result, lineage_result)
    
    log_audit("GET_RISK_REPORT", "risk_report", catalog_id,
              f"生成风险报告: {catalog['name']}, 风险等级: {risk_result.get('risk_level', 'unknown')}")
    
    return ReportResponse(
        catalog_id=catalog_id,
        catalog_name=catalog["name"],
        department=catalog["department"],
        risk_level=risk_result.get("risk_level", "low"),
        total_score=risk_result.get("total_entropy_score", 0),
        open_risk=risk_result.get("dimensions", {}).get("open_risk", 0),
        auth_risk=risk_result.get("dimensions", {}).get("auth_risk", 0),
        privacy_risk=risk_result.get("dimensions", {}).get("privacy_risk", 0),
        reid_risk=risk_result.get("dimensions", {}).get("reid_risk", 0),
        issues=report_data.get("issues", []),
        suggestions=report_data.get("rectification_suggestions", []),
        review_opinions=report_data.get("review_opinions", []),
        rectification_suggestions=report_data.get("rectification_suggestions", [])
    )


@router.get("/get_lineage/{catalog_id}", response_model=LineageResponse)
async def get_lineage(catalog_id: int):
    """
    S7: 获取数据血缘图谱
    对应专利1 S4: 数据血缘链路追踪
    """
    catalog = get_catalog(catalog_id)
    if not catalog:
        raise HTTPException(status_code=404, detail="数据目录不存在")
    
    tracker = get_lineage_tracker()
    graph_data = tracker.export_lineage_graph(catalog_id)
    
    return LineageResponse(
        catalog_id=catalog_id,
        nodes=[LineageNode(**n) for n in graph_data.get("nodes", [])],
        edges=[LineageEdge(**e) for e in graph_data.get("edges", [])],
        is_complete=len(graph_data.get("nodes", [])) > 0
    )


@router.get("/audit_logs")
async def get_audit_logs(limit: int = 50):
    """
    S8: 审计日志查询
    对应专利4 S6: 全链路审计时间序列
    """
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    
    return {
        "logs": [dict(row) for row in rows],
        "total": len(rows)
    }


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查"""
    return HealthResponse(
        status="healthy",
        service="public-data-compliance",
        version="1.0.0"
    )