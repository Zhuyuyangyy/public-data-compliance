# 公共数据资源授权运营合规审查系统 - API 文档

> 版本: 1.0.0 | 基础路径: `/api/v1` | FastAPI Backend 端口: 8013

---

## 目录

- [概述](#概述)
- [数据敏感性映射 `/map_sensitivity`](#数据敏感性映射-map_sensitivity)
- [泄露风险评估 `/assess_breach_risk`](#泄露风险评估-assess_breach_risk)
- [数据使用授权 `/authorize_data_use`](#数据使用授权-authorize_data_use)
- [合规状态检查 `/check_compliance`](#合规状态检查-check_compliance)

---

## 概述

本系统提供四个核心 API 端点，用于公共数据资源授权运营过程中的合规审查与风险熵评估。每个端点均基于专利技术实现。

### 专利技术对应

| 专利 | 对应功能 |
|------|---------|
| 基于数据血缘图谱的公共数据授权范围校验方法 | `/authorize_data_use` |
| 面向公共数据运营的敏感字段风险熵评估方法 | `/map_sensitivity` |
| 基于语义闭环的数据产品合规审查方法 | `/check_compliance` |
| 全过程审计追踪系统 | `/assess_breach_risk` |

---

## 数据敏感性映射 `/map_sensitivity`

**POST** `/api/v1/map_sensitivity`

对数据条目进行敏感性等级映射，考虑类别、收集范围和留存周期三个维度。

### 请求体

```json
{
  "data_items": [
    {
      "name": "string",          // 数据项名称
      "category": "string",       // 数据类别
      "collection_scope": "string", // 收集范围 ("全量收集" | "必要范围内" | ...)
      "retention_period": "string"  // 留存周期 ("永久" | "临时" | ...)
    }
  ]
}
```

### 支持的数据类别

| 类别 | 基础敏感性得分 |
|------|--------------|
| 个人生物信息 | 0.95 |
| 医疗健康 | 0.92 |
| 金融账户 | 0.88 |
| 位置轨迹 | 0.85 |
| 社交关系 | 0.78 |
| 一般联系信息 | 0.45 |
| 公开数据 | 0.10 |

### 敏感性等级划分

| 等级 | 得分区间 |
|------|---------|
| critical（极高） | > 0.85 |
| high（高） | 0.65 ~ 0.85 |
| medium（中） | 0.40 ~ 0.65 |
| low（低） | < 0.40 |

### 响应示例

```json
{
  "data_item_count": 3,
  "average_sensitivity": 0.857,
  "critical_count": 2,
  "items": [
    {
      "item_name": "指纹数据",
      "category": "个人生物信息",
      "sensitivity_score": 0.912,
      "sensitivity_level": "critical",
      "key_concerns": ["生物特征数据", "永久存储风险"]
    }
  ]
}
```

---

## 泄露风险评估 `/assess_breach_risk`

**POST** `/api/v1/assess_breach_risk`

评估数据泄露/暴露风险，综合考虑收集规模、授权状态、第三方共享和安全措施。

### 请求体

```json
{
  "data_category": "string",         // 数据类别
  "collection_scale": "string",      // 收集规模 ("mass_surveillance" | "targeted" | "individual")
  "authorization_status": "string",  // 授权状态 ("authorized" | "partial" | "none")
  "third_party_sharing": boolean,    // 是否向第三方共享
  "security_measures": ["string"]    // 已实施的安全措施列表
}
```

### 安全措施扣减系数

| 安全措施 | 风险扣减 |
|---------|---------|
| 加密 | -0.20 |
| 访问控制 | -0.15 |
| 脱敏处理 | -0.12 |
| 审计日志 | -0.10 |

### 响应示例

```json
{
  "risk_score": 0.72,
  "risk_level": "high",
  "breach_probability": 0.576,
  "estimated_impact": "大规模个人信息泄露",
  "key_risk_factors": ["未授权数据处理", "第三方共享缺乏管控"]
}
```

---

## 数据使用授权 `/authorize_data_use`

**POST** `/api/v1/authorize_data_use`

处理数据使用授权申请，基于申请级别和条件自动决定审批结果。

### 请求体

```json
{
  "applicant_id": "string",      // 申请人ID
  "data_category": "string",     // 数据类别
  "intended_use": "string",     // 预期用途
  "authorization_level": "string", // 申请授权级别 ("full" | "partial" | "denied")
  "conditions": ["string"]       // 附加条件（可选）
}
```

### 自动附加条件

| 条件 | 触发规则 |
|------|---------|
| 须完成数据保护影响评估(DPIA) | 审批通过且类别为"个人生物信息"或"医疗健康" |
| 仅限{用途}用途 | 审批通过且指定了预期用途 |

### 响应示例

```json
{
  "request_id": "auth-20250601-ABC12345",
  "applicant_id": "org-001",
  "data_category": "医疗健康",
  "decision": "approved",
  "authorization_level": "full",
  "conditions": ["须完成数据保护影响评估(DPIA)", "仅限临床研究用途"],
  "decision_timestamp": "2026-05-17T20:46:00.000Z"
}
```

---

## 合规状态检查 `/check_compliance`

**GET** `/api/v1/check_compliance`

检查组织的整体合规状态，评估其数据操作的授权合规率。

### 查询参数

| 参数 | 类型 | 说明 |
|------|------|------|
| organization_id | string | 组织ID |
| data_operations | string | JSON 格式的数据操作数组 |

### data_operations 数组项

```json
{
  "operation": "string",    // 操作描述
  "data_category": "string", // 数据类别
  "authorized": boolean     // 是否已授权
}
```

### 合规状态判定

| 合规率 | 状态 |
|-------|------|
| ≥ 95% | compliant（合规） |
| 70% ~ 95% | partial（部分合规） |
| < 70% | non_compliant（不合规） |

### 风险建议

| 场景 | 建议 |
|------|------|
| 未授权操作占比 > 30% | 立即终止未授权操作 |
| 存在未授权操作 | 完善授权流程 |
| 无未授权操作 | 维持现状 |

### 响应示例

```json
{
  "organization_id": "org-example-001",
  "total_operations": 10,
  "compliance_rate": 80.0,
  "unauthorized_operations": [
    {"operation": "批量导出用户位置", "data_category": "位置轨迹", "authorized": false}
  ],
  "compliance_status": "partial",
  "risk_assessment": {
    "unauthorized_data_types": ["位置轨迹"],
    "recommendation": "完善授权流程"
  }
}
```

---

## 快速测试（curl）

```bash
# 测试敏感性映射
curl -X POST http://localhost:8013/api/v1/map_sensitivity \
  -H "Content-Type: application/json" \
  -d '{"data_items":[{"name":"指纹","category":"个人生物信息","collection_scope":"全量收集","retention_period":"永久"}]}'

# 测试泄露风险评估
curl -X POST http://localhost:8013/api/v1/assess_breach_risk \
  -H "Content-Type: application/json" \
  -d '{"data_category":"位置轨迹","collection_scale":"mass_surveillance","authorization_status":"none","third_party_sharing":true,"security_measures":[]}'

# 测试数据使用授权
curl -X POST http://localhost:8013/api/v1/authorize_data_use \
  -H "Content-Type: application/json" \
  -d '{"applicant_id":"app-123","data_category":"医疗健康","intended_use":"临床研究","authorization_level":"full"}'

# 测试合规状态检查
curl "http://localhost:8013/api/v1/check_compliance?organization_id=org-001&data_operations=%5B%7B%22operation%22%3A%22%E8%AF%B7%E6%B1%82%22%2C%22data_category%22%3A%22%E9%80%9A%E4%BF%A1%E5%BD%95%22%2C%22authorized%22%3Atrue%7D%5D"
```

---

*最后更新: 2026-05-17*