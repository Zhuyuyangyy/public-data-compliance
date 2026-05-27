"""
数据目录解析服务
识别字段、来源、部门、授权范围、敏感等级
判断数据资源类型（公共数据/敏感数据/个人信息）
"""
import json
from typing import List, Dict, Any, Tuple

# 个人信息字段关键词
PERSONAL_INFO_KEYWORDS = [
    "姓名", "name", "手机", "phone", "电话", "tel", "邮箱", "email", "email",
    "身份证", "id_card", "身份证号", "address", "地址", "出生日期", "birth",
    "生日", "gender", "性别", "民族", "nation", "籍贯", "户籍",
    "银行卡", "bank_card", "账户", "account", "车牌", "vehicle",
    "护照", "passport", "军官证", "社保", "医保", "公积金"
]

# 敏感个人信息字段关键词
SENSITIVE_INFO_KEYWORDS = [
    "健康", "health", "医疗", "medical", "疾病", "diagnosis",
    "宗教", "religion", "信仰", "政治", "politics", "工会",
    "犯罪", "criminal", "违法", "征信", "credit", "评分",
    "基因", "genetic", "生物", "biometric", "指纹", "face", "人脸",
    "位置", "location", "轨迹", "track", "行踪", "婚恋", "marital",
    "妊娠", "pregnancy", "年龄", "age", "财产", "property"
]

# 公共数据字段关键词（低敏感）
PUBLIC_DATA_KEYWORDS = [
    "企业", "company", "corporation", "business",
    "统计", "statistics", "数据", "data",
    "天气", "weather", "环境", "environment",
    "交通", "traffic", "地理", "geographic",
    "公共", "public", "服务", "service"
]

# 可重识别字段组合
REID_COMBINATION_FIELDS = [
    ("性别", "年龄"), ("地区", "职业"), ("时间", "位置"),
    ("科室", "疾病"), ("年龄", "收入")
]

class DataCatalogParser:
    """数据目录解析器"""
    
    def __init__(self):
        self.personal_keywords = PERSONAL_INFO_KEYWORDS
        self.sensitive_keywords = SENSITIVE_INFO_KEYWORDS
        self.public_keywords = PUBLIC_DATA_KEYWORDS
    
    def parse_catalog(self, name: str, department: str, data_type: str,
                      fields: List[Dict], source_info: str = "",
                      auth_scope: str = "", sensitivity_level: str = "low") -> Dict[str, Any]:
        """
        解析数据目录
        返回解析结果和检测到的问题
        """
        result = {
            "catalog_name": name,
            "department": department,
            "original_data_type": data_type,
            "detected_data_type": self._detect_data_type(fields),
            "field_count": len(fields),
            "fields": [],
            "issues": [],
            "sensitivity_assessment": {}
        }
        
        # 解析每个字段
        personal_count = 0
        sensitive_count = 0
        reid_risk_count = 0
        
        for field in fields:
            field_analysis = self._analyze_field(field)
            result["fields"].append(field_analysis)
            
            if field_analysis.get("is_personal_info"):
                personal_count += 1
            if field_analysis.get("is_sensitive_info"):
                sensitive_count += 1
            if field_analysis.get("can_reidentify"):
                reid_risk_count += 1
        
        # 数据类型检测
        if data_type == "public" and (personal_count > 0 or sensitive_count > 0):
            result["issues"].append({
                "rule_id": "RULE_D_001",
                "issue": "数据类型标注为公共数据，但包含个人信息字段",
                "severity": "high",
                "fields": [f["name"] for f in result["fields"] if f.get("is_personal_info")]
            })
        
        if sensitive_count > 0 and data_type != "sensitive":
            result["issues"].append({
                "rule_id": "RULE_D_002",
                "issue": "数据包含敏感个人信息，建议标注为敏感数据",
                "severity": "high",
                "fields": [f["name"] for f in result["fields"] if f.get("is_sensitive_info")]
            })
        
        # 敏感等级评估
        if personal_count > 0:
            result["sensitivity_assessment"]["has_personal_info"] = True
            result["sensitivity_assessment"]["personal_info_count"] = personal_count
        if sensitive_count > 0:
            result["sensitivity_assessment"]["has_sensitive_info"] = True
            result["sensitivity_assessment"]["sensitive_info_count"] = sensitive_count
        if reid_risk_count > 0:
            result["sensitivity_assessment"]["reid_risk_count"] = reid_risk_count
        
        # 建议敏感等级
        if sensitive_count > 0:
            result["recommended_sensitivity"] = "extreme"
        elif personal_count > 3:
            result["recommended_sensitivity"] = "high"
        elif personal_count > 0:
            result["recommended_sensitivity"] = "medium"
        else:
            result["recommended_sensitivity"] = sensitivity_level
        
        return result
    
    def _detect_data_type(self, fields: List[Dict]) -> str:
        """基于字段内容检测数据类型"""
        field_names = " ".join([f.get("name", "") + " " + f.get("description", "") for f in fields]).lower()
        
        personal_count = sum(1 for kw in self.personal_keywords if kw.lower() in field_names)
        sensitive_count = sum(1 for kw in self.sensitive_keywords if kw.lower() in field_names)
        public_count = sum(1 for kw in self.public_keywords if kw.lower() in field_names)
        
        if sensitive_count > 0:
            return "sensitive"
        elif personal_count > 0:
            return "personal"
        elif public_count > len(fields) * 0.5:
            return "public"
        else:
            return "unknown"
    
    def _analyze_field(self, field: Dict) -> Dict:
        """分析单个字段"""
        name = field.get("name", "")
        description = field.get("description", "")
        text = f"{name} {description}".lower()
        
        is_personal = any(kw.lower() in text for kw in self.personal_keywords)
        is_sensitive = any(kw.lower() in text for kw in self.sensitive_keywords)
        
        # 检查可重识别性
        can_reidentify = is_personal or self._check_reid_risk(name, description)
        
        # 检查匿名化标识
        is_anonymized = any(kw in text for kw in ["匿名", "脱敏", "mask", "hash", "encrypt"])
        
        return {
            "name": name,
            "description": description,
            "data_type": field.get("data_type", ""),
            "sensitivity": field.get("sensitivity", "low"),
            "is_personal_info": is_personal,
            "is_sensitive_info": is_sensitive,
            "can_reidentify": can_reidentify and not is_anonymized,
            "is_anonymized": is_anonymized
        }
    
    def _check_reid_risk(self, name: str, description: str) -> bool:
        """检查字段是否具有重识别风险"""
        text = f"{name} {description}".lower()
        # 唯一标识符风险
        risk_patterns = ["id", "编码", "编号", "identifier", "唯一", "标识"]
        return any(p in text for p in risk_patterns)


# 单例
_parser_instance = None

def get_catalog_parser() -> DataCatalogParser:
    global _parser_instance
    if _parser_instance is None:
        _parser_instance = DataCatalogParser()
    return _parser_instance

def parse_data_catalog(name: str, department: str, data_type: str,
                       fields: List[Dict], source_info: str = "",
                       auth_scope: str = "", sensitivity_level: str = "low") -> Dict[str, Any]:
    """便捷函数：解析数据目录"""
    parser = get_catalog_parser()
    return parser.parse_catalog(name, department, data_type, fields, source_info, auth_scope, sensitivity_level)