"""
授权范围匹配服务
判断用途、主体、数据字段是否超授权
检测越权开发风险
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, date

class AuthorizationScope:
    """授权范围定义"""
    def __init__(self, authorized_party: str, usage_scope: str, 
                 authorized_fields: List[str], valid_from: date, valid_to: date):
        self.authorized_party = authorized_party
        self.usage_scope = usage_scope
        self.authorized_fields = set(authorized_fields)
        self.valid_from = valid_from
        self.valid_to = valid_to
    
    def is_valid(self, check_date: date = None) -> bool:
        """检查授权是否有效"""
        if check_date is None:
            check_date = date.today()
        return self.valid_from <= check_date <= self.valid_to
    
    def contains_field(self, field_name: str) -> bool:
        """检查字段是否在授权范围内"""
        # 通配符支持
        if "*" in self.authorized_fields:
            return True
        return field_name in self.authorized_fields
    
    def matches_purpose(self, intended_use: str) -> bool:
        """检查用途是否匹配"""
        if not self.usage_scope:
            return True
        # 部分匹配
        return intended_use in self.usage_scope or self.usage_scope in intended_use


class AuthorizationChecker:
    """授权范围检查器"""
    
    # 授权类型关键词
    AUTHORIZED_USE_KEYWORDS = [
        "统计分析", "数据研究", "科研", "政府决策", "公共服务",
        "市场监管", "应急管理", "环境监测", "交通管理"
    ]
    
    # 越权用途关键词
    UNAUTHORIZED_USE_KEYWORDS = [
        "商业销售", "marketing", "advertising", "广告推送",
        "个人信息交易", "数据贩卖", "非法获取", "军事用途", "情报收集"
    ]
    
    def __init__(self):
        self.scope_cache: Dict[int, List[AuthorizationScope]] = {}
    
    def add_authorization(self, catalog_id: int, auth: AuthorizationScope):
        """添加授权记录"""
        if catalog_id not in self.scope_cache:
            self.scope_cache[catalog_id] = []
        self.scope_cache[catalog_id].append(auth)
    
    def check_authorization(self, catalog_id: int, requester: str,
                          intended_use: str, requested_fields: List[str],
                          check_date: date = None) -> Dict[str, Any]:
        """
        检查授权范围
        返回：是否授权、授权字段、未授权字段、问题列表、建议
        """
        if check_date is None:
            check_date = date.today()
        
        result = {
            "is_authorized": False,
            "catalog_id": catalog_id,
            "requester": requester,
            "intended_use": intended_use,
            "authorized_fields": [],
            "unauthorized_fields": [],
            "issues": [],
            "suggestions": []
        }
        
        # 获取授权范围
        auth_list = self.scope_cache.get(catalog_id, [])
        
        if not auth_list:
            result["issues"].append({
                "rule_id": "RULE_D_003",
                "issue": "该数据目录尚未创建任何授权记录",
                "severity": "high"
            })
            result["suggestions"].append("请先创建授权记录，明确授权对象、范围和有效期")
            return result
        
        # 检查是否有有效授权
        valid_auth = None
        for auth in auth_list:
            if auth.is_valid(check_date):
                valid_auth = auth
                break
        
        if not valid_auth:
            result["issues"].append({
                "rule_id": "RULE_D_003",
                "issue": "该数据目录当前无有效授权记录（可能已过期或被撤销）",
                "severity": "high"
            })
            result["suggestions"].append("请检查授权有效期，更新或续期授权记录")
            return result
        
        # 检查授权对象是否匹配
        if valid_auth.authorized_party != requester and valid_auth.authorized_party != "*":
            result["issues"].append({
                "rule_id": "RULE_D_004",
                "issue": f"请求方 '{requester}' 不在授权对象范围内（授权对象：{valid_auth.authorized_party}）",
                "severity": "high"
            })
            result["suggestions"].append("跨部门共享需取得新的授权许可")
            return result
        
        # 检查用途是否合规
        purpose_issues = self._check_purpose(intended_use)
        result["issues"].extend(purpose_issues)
        
        # 检查字段授权范围
        for field in requested_fields:
            if valid_auth.contains_field(field):
                result["authorized_fields"].append(field)
            else:
                result["unauthorized_fields"].append(field)
        
        if result["unauthorized_fields"]:
            result["issues"].append({
                "rule_id": "RULE_D_003",
                "issue": f"字段 {result['unauthorized_fields']} 未在授权范围内",
                "severity": "medium"
            })
            result["suggestions"].append("请申请扩展授权范围或调整数据使用目的")
        
        # 综合判断
        if not purpose_issues and not result["unauthorized_fields"]:
            result["is_authorized"] = True
        
        return result
    
    def _check_purpose(self, intended_use: str) -> List[Dict]:
        """检查用途是否合规"""
        issues = []
        use_lower = intended_use.lower()
        
        # 检查是否属于越权用途
        for keyword in self.UNAUTHORIZED_USE_KEYWORDS:
            if keyword.lower() in use_lower:
                issues.append({
                    "rule_id": "RULE_D_006",
                    "issue": f"用途 '{intended_use}' 属于越权开发行为",
                    "severity": "high"
                })
        
        # 如果没有匹配任何授权用途关键词，给出警告
        if not any(kw in use_lower for kw in self.AUTHORIZED_USE_KEYWORDS):
            if not issues:
                issues.append({
                    "rule_id": "RULE_D_003",
                    "issue": f"用途 '{intended_use}' 未在预定义授权用途列表中，请确认是否在授权范围内",
                    "severity": "low"
                })
        
        return issues
    
    def check_cross_department_sharing(self, catalog_id: int, requester: str,
                                      auth_list: List[Dict]) -> Dict[str, Any]:
        """
        检查跨部门共享授权
        """
        result = {
            "is_authorized": False,
            "department_match": False,
            "issues": [],
            "suggestions": []
        }
        
        for auth in auth_list:
            if auth.get("authorized_party") == requester:
                result["is_authorized"] = True
                result["department_match"] = True
                break
        
        if not result["is_authorized"]:
            result["issues"].append({
                "rule_id": "RULE_D_004",
                "issue": f"请求方 '{requester}' 未经授权进行跨部门数据共享",
                "severity": "medium"
            })
            result["suggestions"].append("需取得原授权部门的书面同意")
        
        return result
    
    def detect_over_auth_issues(self, catalog_id: int, fields: List[str],
                               auth_list: List[Dict]) -> List[Dict]:
        """
        检测越权开发风险
        """
        issues = []
        
        for auth in auth_list:
            if auth.get("catalog_id") != catalog_id:
                continue
            
            authorized_fields = set(auth.get("authorized_fields", []))
            
            for field in fields:
                if field not in authorized_fields:
                    issues.append({
                        "rule_id": "RULE_D_006",
                        "issue": f"字段 '{field}' 使用超出授权范围",
                        "severity": "high",
                        "field": field,
                        "auth_id": auth.get("id")
                    })
        
        return issues


# 单例
_checker_instance = None

def get_authorization_checker() -> AuthorizationChecker:
    global _checker_instance
    if _checker_instance is None:
        _checker_instance = AuthorizationChecker()
    return _checker_instance

def check_authorization(catalog_id: int, requester: str,
                       intended_use: str, requested_fields: List[str]) -> Dict[str, Any]:
    """便捷函数：检查授权范围"""
    checker = get_authorization_checker()
    return checker.check_authorization(catalog_id, requester, intended_use, requested_fields)