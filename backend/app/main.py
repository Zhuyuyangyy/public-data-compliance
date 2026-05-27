"""
公共数据资源授权运营合规审查与数据风险熵评估系统 V1.0

FastAPI Backend - 端口 8013

专利对应:
1. 一种基于数据血缘图谱的公共数据授权范围校验方法
2. 一种面向公共数据运营的敏感字段风险熵评估方法
3. 一种基于语义闭环的数据产品合规审查方法
4. 一种公共数据授权运营全过程审计追踪系统
"""
from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime
import random

from app.api.routes import router
from app.core.database import init_db

# 创建FastAPI应用
app = FastAPI(
    title="公共数据资源授权运营合规审查系统",
    description="""
    公共数据资源授权运营合规审查与数据风险熵评估系统
    
    ## 核心功能
    - 数据目录注册与解析
    - 授权范围校验与越权检测
    - 隐私风险识别与匿名化检测
    - 数据血缘图谱追踪
    - 多维风险熵评分
    - 合规报告生成
    
    ## 专利技术
    1. 基于数据血缘图谱的授权范围校验
    2. 面向公共数据运营的敏感字段风险熵评估
    3. 基于语义闭环的数据产品合规审查
    4. 全过程审计追踪系统
    """,
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化数据库
init_db()

# 注册路由
app.include_router(router)


# ============================================================
# 公共数据合规 API Router
# ============================================================
pdc_router = APIRouter(prefix="/api/v1", tags=["public-data-compliance"])


class SensitivityMapRequest(BaseModel):
    data_items: List[Dict]  # [{"name": str, "category": str, "collection_scope": str, "retention_period": str}]


class BreachRiskRequest(BaseModel):
    data_category: str
    collection_scale: str  # "mass_surveillance" | "targeted" | "individual"
    authorization_status: str  # "authorized" | "partial" | "none"
    third_party_sharing: bool
    security_measures: List[str]


class AuthorizeDataRequest(BaseModel):
    applicant_id: str
    data_category: str
    intended_use: str
    authorization_level: str  # "full" | "partial" | "denied"
    conditions: Optional[List[str]] = None


class CheckComplianceRequest(BaseModel):
    organization_id: str
    data_operations: List[Dict]  # [{"operation": str, "data_category": str, "authorized": bool}]


@pdc_router.post("/map_sensitivity")
async def map_sensitivity(req: SensitivityMapRequest):
    """Map data items to sensitivity levels"""
    sensitivity_levels = {
        "个人生物信息": 0.95, "金融账户": 0.88, "医疗健康": 0.92,
        "位置轨迹": 0.85, "社交关系": 0.78, "一般联系信息": 0.45, "公开数据": 0.1
    }
    results = []
    for item in req.data_items:
        base = sensitivity_levels.get(item["category"], 0.5)
        scope_factor = (
            1.2 if "全量" in item.get("collection_scope", "") else
            0.9 if "必要" in item.get("collection_scope", "") else 1.0
        )
        retention_factor = (
            1.15 if "永久" in item.get("retention_period", "") else
            0.95 if "临时" in item.get("retention_period", "") else 1.0
        )
        score = round(min(0.99, base * scope_factor * retention_factor), 3)
        results.append({
            "item_name": item["name"],
            "category": item["category"],
            "sensitivity_score": score,
            "sensitivity_level": (
                "critical" if score > 0.85 else
                "high" if score > 0.65 else
                "medium" if score > 0.4 else "low"
            ),
            "key_concerns": [
                c for c in [
                    "生物特征数据" if item["category"] in ["个人生物信息"] else "",
                    "数据过度收集" if scope_factor > 1.1 else "",
                    "永久存储风险" if retention_factor > 1.1 else "",
                ] if c
            ]
        })
    avg = round(sum(r["sensitivity_score"] for r in results) / len(results), 3)
    return {
        "data_item_count": len(results),
        "average_sensitivity": avg,
        "critical_count": sum(1 for r in results if r["sensitivity_level"] == "critical"),
        "items": results
    }


@pdc_router.post("/assess_breach_risk")
async def assess_breach_risk(req: BreachRiskRequest):
    """Assess data breach/exposure risk"""
    base_risk = {"mass_surveillance": 0.8, "targeted": 0.5, "individual": 0.2}.get(req.collection_scale, 0.5)
    auth_factor = {"authorized": 0.3, "partial": 0.6, "none": 0.9}.get(req.authorization_status, 0.5)
    share_factor = 0.15 if req.third_party_sharing else 0
    security_score = sum(
        {"加密": -0.2, "访问控制": -0.15, "审计日志": -0.1, "脱敏处理": -0.12}.get(m, 0)
        for m in req.security_measures
    )
    risk = round(min(0.99, base_risk * 0.4 + auth_factor * 0.35 + share_factor + security_score), 3)
    return {
        "risk_score": risk,
        "risk_level": (
            "critical" if risk > 0.75 else
            "high" if risk > 0.55 else
            "medium" if risk > 0.35 else "low"
        ),
        "breach_probability": round(risk * 0.8, 3),
        "estimated_impact": (
            "大规模个人信息泄露" if req.collection_scale == "mass_surveillance" else "局部数据泄露"
        ),
        "key_risk_factors": [
            f for f in [
                "未授权数据处理" if auth_factor > 0.5 else "",
                "第三方共享缺乏管控" if req.third_party_sharing else "",
                "安全措施不足" if security_score > -0.1 else "",
            ] if f
        ]
    }


@pdc_router.post("/authorize_data_use")
async def authorize_data_use(req: AuthorizeDataRequest):
    """Process data use authorization request"""
    approval_prob = (
        0.85 if req.authorization_level == "full" else
        0.5 if req.authorization_level == "partial" else 0.15
    )
    decision = "approved" if random.random() < approval_prob else "denied"
    conditions = req.conditions or []
    if decision == "approved" and req.data_category in ["个人生物信息", "医疗健康"]:
        conditions.append("须完成数据保护影响评估(DPIA)")
    if decision == "approved" and req.intended_use:
        conditions.append(f"仅限{req.intended_use}用途")
    return {
        "request_id": f"auth-{req.applicant_id[:8]}-{datetime.now().strftime('%Y%m%d')}",
        "applicant_id": req.applicant_id,
        "data_category": req.data_category,
        "decision": decision,
        "authorization_level": req.authorization_level,
        "conditions": conditions,
        "decision_timestamp": datetime.now().isoformat()
    }


@pdc_router.get("/check_compliance")
async def check_compliance(organization_id: str, data_operations: str):
    """Check overall compliance status for an organization"""
    import json
    try:
        ops = json.loads(data_operations)
    except Exception:
        raise HTTPException(status_code=400, detail="data_operations must be a valid JSON array")

    total = len(ops)
    unauthorized = [op for op in ops if not op.get("authorized", False)]
    compliance_rate = round((total - len(unauthorized)) / total * 100, 1) if total > 0 else 100
    return {
        "organization_id": organization_id,
        "total_operations": total,
        "compliance_rate": compliance_rate,
        "unauthorized_operations": unauthorized,
        "compliance_status": (
            "compliant" if compliance_rate >= 95 else
            "partial" if compliance_rate >= 70 else "non_compliant"
        ),
        "risk_assessment": {
            "unauthorized_data_types": list(set(op["data_category"] for op in unauthorized)) if unauthorized else [],
            "recommendation": (
                "立即终止未授权操作" if len(unauthorized) > total * 0.3 else
                "完善授权流程" if unauthorized else "维持现状"
            )
        }
    }


# 注册公共数据合规路由
app.include_router(pdc_router)


@app.get("/")
async def root():
    return {
        "service": "公共数据资源授权运营合规审查系统",
        "version": "1.0.0",
        "status": "running",
        "port": 8013,
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8013)