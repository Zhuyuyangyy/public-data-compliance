# 公共数据资源授权运营合规审查与数据风险熵评估系统 V1.0

基于数据血缘图谱与多维风险熵评估的智能合规审查平台。

## 🎯 系统概述

本系统针对公共数据授权运营场景，提供从数据目录注册到合规报告生成的全流程支持。通过数据血缘图谱追踪、隐私风险识别、授权范围校验和多维风险熵评分，实现公共数据授权运营的智能合规审查。

## 📋 核心功能

### 1. 数据目录注册与解析
- 自动识别数据类型（公共数据/敏感数据/个人信息）
- 智能检测敏感字段和个人信息字段
- 评估数据敏感等级并给出建议

### 2. 授权范围校验（专利1）
- 基于数据血缘图谱的授权范围校验方法
- 检测越权开发风险
- 跨部门共享授权管理

### 3. 隐私风险识别（专利2）
- 个人信息字段自动检测
- 敏感个人信息识别
- 再识别风险评估
- 匿名化/去标识化质量检测

### 4. 数据血缘图谱（专利1）
- 追踪数据来源、流转路径、加工过程
- 构建完整的数据血缘链路
- 支持下游影响分析

### 5. 多维风险熵评分（专利2）
- 开放风险评估
- 授权风险评估
- 隐私风险评估
- 再识别风险评估
- 多维风险耦合分析
- 风险熔断机制

### 6. 合规报告生成（专利3&4）
- 综合风险评估报告
- 问题汇总与分类
- 审查意见生成
- 整改建议输出

## 🔧 技术架构

```
public-data-compliance/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes.py          # API路由（8个接口）
│   │   ├── core/
│   │   │   └── database.py        # SQLite数据库初始化
│   │   ├── models/
│   │   │   └── schemas.py         # Pydantic数据模型
│   │   ├── services/
│   │   │   ├── data_catalog_parser.py    # 数据目录解析
│   │   │   ├── data_lineage_tracker.py   # 数据血缘追踪
│   │   │   ├── authorization_checker.py  # 授权范围匹配
│   │   │   ├── privacy_risk_detector.py   # 隐私风险识别
│   │   │   ├── data_risk_scorer.py        # 数据风险熵评分
│   │   │   └── report_generator.py        # 合规报告生成
│   │   ├── rules/
│   │   │   └── data_compliance_rules.json # 规则库
│   │   └── main.py                 # FastAPI入口
│   ├── data/                        # SQLite数据库目录
│   ├── requirements.txt
│   └── start.bat                   # 启动脚本
└── frontend/
    └── index.html                  # Vue3单文件前端
```

## 🔌 API接口

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/v1/register_catalog` | 注册数据目录 |
| POST | `/api/v1/create_authorization` | 创建授权记录 |
| POST | `/api/v1/upload_data_product` | 上传数据产品 |
| POST | `/api/v1/check_authorization` | 检查授权范围 |
| POST | `/api/v1/analyze_privacy_risk` | 分析隐私风险 |
| GET | `/api/v1/get_risk_report/{catalog_id}` | 获取风险报告 |
| GET | `/api/v1/get_lineage/{catalog_id}` | 获取血缘图谱 |
| GET | `/api/v1/audit_logs` | 审计日志查询 |
| GET | `/api/v1/health` | 健康检查 |

## 📦 依赖

- Python 3.12+
- FastAPI 0.115.0
- uvicorn 0.30.6
- Pydantic 2.9.2
- SQLite3（内置）

## 🚀 启动

### 后端启动

```batch
cd backend
pip install -r requirements.txt
start.bat
```

后端运行在 `http://localhost:8013`

### 前端使用

直接用浏览器打开 `frontend/index.html`

## 📊 数据库表结构

```sql
-- 规则库
rules (id, rule_id, rule_type, description, severity, penalty, enabled)

-- 数据目录
data_catalogs (id, name, department, data_type, fields_json, sensitivity_level, source_info, auth_scope)

-- 授权记录
authorization_records (id, catalog_id, authorized_party, usage_scope, valid_from, valid_to, status)

-- 数据血缘
data_lineage (id, source_catalog, target_product, process_type, lineage_data)

-- 分析结果
analysis_results (id, catalog_id, risk_score, risk_level, open_risk, auth_risk, privacy_risk, reid_risk, details_json)

-- 审计日志
audit_logs (id, action, target_type, target_id, details, created_at)
```

## 📝 专利对应

1. **一种基于数据血缘图谱的公共数据授权范围校验方法**
   - 数据血缘追踪服务 (`data_lineage_tracker.py`)
   - 授权范围检查服务 (`authorization_checker.py`)

2. **一种面向公共数据运营的敏感字段风险熵评估方法**
   - 隐私风险识别服务 (`privacy_risk_detector.py`)
   - 数据风险熵评分服务 (`data_risk_scorer.py`)

3. **一种基于语义闭环的数据产品合规审查方法**
   - 数据产品上传与检测 (`routes.py` - upload_data_product)
   - 语义分析整合 (`data_catalog_parser.py`)

4. **一种公共数据授权运营全过程审计追踪系统**
   - 审计日志 (`audit_logs` 表)
   - 报告生成服务 (`report_generator.py`)

## ⚠️ 免责声明

本系统仅供技术参考，不构成法律意见。使用者应自行承担风险。