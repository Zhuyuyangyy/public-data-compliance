"""
隐私风险识别服务
检测个人信息、敏感个人信息、可重识别字段
匿名化/去标识化检测
"""
from typing import List, Dict, Any, Tuple
import re

# 个人信息字段模式
PERSONAL_INFO_PATTERNS = [
    (r"姓名|name|username", "personal"),
    (r"手机|mobile|phone|tel", "personal"),
    (r"邮箱|email|e-mail", "personal"),
    (r"身份证|id[_-]?card|identity", "personal"),
    (r"地址|address|addr", "personal"),
    (r"出生.*日期|birth.*date|dob", "personal"),
    (r"性别|gender|sex", "personal"),
    (r"银行卡|bank.*card", "personal"),
    (r"车牌|vehicle.*plate|license.*plate", "personal"),
    (r"护照|passport", "personal"),
    (r"社保号|医保号|公积金号", "personal"),
    (r"账号|account|user.*id", "personal"),
]

# 敏感个人信息模式
SENSITIVE_INFO_PATTERNS = [
    (r"健康|health|medical|医疗|疾病|diagnosis", "sensitive"),
    (r"宗教|religion|信仰|faith", "sensitive"),
    (r"政治.*面貌|political", "sensitive"),
    (r"犯罪记录|criminal|misdemeanor", "sensitive"),
    (r"征信|credit.*score|信用.*评分", "sensitive"),
    (r"基因|genetic|基因信息", "sensitive"),
    (r"指纹|face.*recog|人脸|biometric", "sensitive"),
    (r"位置|location|gps|坐标|经纬度", "sensitive"),
    (r"行踪|轨迹|track", "sensitive"),
    (r"婚恋|婚姻|marital.*status", "sensitive"),
    (r"妊娠|怀孕|pregnancy", "sensitive"),
    (r"财产|income|资产|property| wealth", "sensitive"),
]

# 匿名化检测模式
ANONYMIZATION_PATTERNS = [
    (r"匿名|anonym", "anonymized"),
    (r"脱敏|mask|masking", "anonymized"),
    (r"哈希|hash", "anonymized"),
    (r"加密|encrypt", "anonymized"),
    (r"去标识|de-?identif", "anonymized"),
    (r"泛化|generaliz", "anonymized"),
    (r"扰动|noise|perturb", "anonymized"),
]

# 再识别风险组合
REID_COMBINATIONS = [
    ("性别", "年龄"), ("地区", "职业"), ("时间", "位置"),
    ("年龄", "收入"), ("科室", "疾病"), ("职业", "收入"),
    ("籍贯", "民族"), ("出生日期", "地区")
]

class PrivacyRiskDetector:
    """隐私风险检测器"""
    
    def __init__(self):
        self.personal_patterns = [(re.compile(p, re.I), t) for p, t in PERSONAL_INFO_PATTERNS]
        self.sensitive_patterns = [(re.compile(p, re.I), t) for p, t in SENSITIVE_INFO_PATTERNS]
        self.anonym_patterns = [(re.compile(p, re.I), t) for p, t in ANONYMIZATION_PATTERNS]
    
    def detect_privacy_risk(self, fields: List[Dict]) -> Dict[str, Any]:
        """
        检测隐私风险
        返回：个人信息数、敏感信息数、再识别风险、问题列表、建议
        """
        result = {
            "personal_info_fields": [],
            "sensitive_info_fields": [],
            "reid_risk_fields": [],
            "anonymized_fields": [],
            "issues": [],
            "suggestions": [],
            "risk_score": 0.0,
            "risk_level": "low"
        }
        
        field_names = [f.get("name", "") for f in fields]
        detected_personal = set()
        detected_sensitive = set()
        detected_anonymized = set()
        
        # 分析每个字段
        for field in fields:
            name = field.get("name", "")
            desc = field.get("description", "")
            text = f"{name} {desc}"
            
            # 检测个人信息
            for pattern, ptype in self.personal_patterns:
                if pattern.search(text):
                    detected_personal.add(name)
                    result["personal_info_fields"].append({
                        "field_name": name,
                        "description": desc,
                        "risk_type": "personal_info",
                        "suggestion": "需脱敏处理"
                    })
                    break
            
            # 检测敏感个人信息
            for pattern, ptype in self.sensitive_patterns:
                if pattern.search(text):
                    detected_sensitive.add(name)
                    result["sensitive_info_fields"].append({
                        "field_name": name,
                        "description": desc,
                        "risk_type": "sensitive_info",
                        "suggestion": "需审批并加强保护"
                    })
                    break
            
            # 检测匿名化标识
            for pattern, ptype in self.anonym_patterns:
                if pattern.search(text):
                    detected_anonymized.add(name)
                    result["anonymized_fields"].append(name)
                    break
        
        # 检测再识别风险
        reid_risk = self._detect_reid_risk(field_names, detected_personal, detected_sensitive, detected_anonymized)
        result["reid_risk_fields"] = reid_risk
        
        # 生成问题列表
        self._generate_issues(result, detected_personal, detected_sensitive, 
                            detected_anonymized, reid_risk)
        
        # 计算风险评分
        self._calculate_risk_score(result)
        
        return result
    
    def _detect_reid_risk(self, field_names: List[str],
                         personal: set, sensitive: set,
                         anonymized: set = None) -> List[str]:
        """
        检测再识别风险
        检查字段组合是否可能用于重识别
        """
        if anonymized is None:
            anonymized = set()
        reid_risk = []

        for f1, f2 in REID_COMBINATIONS:
            # 检查是否存在危险组合
            has_f1 = any(f1 in fn or fn in f1 for fn in field_names)
            has_f2 = any(f2 in fn or fn in f2 for fn in field_names)

            if has_f1 and has_f2:
                # 检查是否已经脱敏
                f1_masked = any(f1 in fn and any(kw in fn.lower() for kw in ["mask", "anon", "hash"])
                               for fn in field_names)
                f2_masked = any(f2 in fn and any(kw in fn.lower() for kw in ["mask", "anon", "hash"])
                               for fn in field_names)

                if not (f1_masked or f2_masked):
                    reid_risk.append(f"{f1}+{f2}组合")

        # 检查唯一标识符
        for name in field_names:
            if any(kw in name.lower() for kw in ["id", "编号", "编码", "identifier"]):
                if name not in anonymized:
                    reid_risk.append(name)

        return reid_risk
    
    def _generate_issues(self, result: Dict, personal: set, sensitive: set,
                        anonymized: set, reid_risk: List[str]):
        """生成问题列表"""
        
        if personal:
            result["issues"].append({
                "rule_id": "RULE_D_001",
                "issue": f"检测到 {len(personal)} 个个人信息字段，需进行脱敏处理",
                "severity": "high",
                "fields": list(personal)
            })
            result["suggestions"].append("建议对个人信息字段进行脱敏处理（如姓名打码、手机号加密）")
        
        if sensitive:
            result["issues"].append({
                "rule_id": "RULE_D_002",
                "issue": f"检测到 {len(sensitive)} 个敏感个人信息字段，需额外审批",
                "severity": "high",
                "fields": list(sensitive)
            })
            result["suggestions"].append("敏感个人信息需单独审批，建议设置访问权限和加密措施")
        
        # 检查未脱敏的个人信息
        unprotected_personal = personal - anonymized
        if unprotected_personal:
            result["issues"].append({
                "rule_id": "RULE_D_001",
                "issue": f"存在 {len(unprotected_personal)} 个个人信息字段未脱敏",
                "severity": "high",
                "fields": list(unprotected_personal)
            })
        
        if reid_risk:
            result["issues"].append({
                "rule_id": "RULE_D_005",
                "issue": f"检测到 {len(reid_risk)} 种再识别风险（字段组合可能导致重识别）",
                "severity": "high",
                "risk_combinations": reid_risk
            })
            result["suggestions"].append("建议对再识别风险字段进行泛化处理（如年龄段代替具体年龄）")
        
        # 检测匿名化不充分
        if personal and len(anonymized) < len(personal) * 0.5:
            result["issues"].append({
                "rule_id": "RULE_D_007",
                "issue": "匿名化不充分，仅有少数字段完成脱敏",
                "severity": "medium"
            })
            result["suggestions"].append("建议全面检查脱敏策略，确保所有个人信息均已处理")
    
    def _calculate_risk_score(self, result: Dict):
        """计算风险评分"""
        score = 0.0
        
        # 个人信息分数
        score += len(result["personal_info_fields"]) * 5
        
        # 敏感信息分数
        score += len(result["sensitive_info_fields"]) * 10
        
        # 再识别风险分数
        score += len(result["reid_risk_fields"]) * 15
        
        # 匿名化不充分
        if len(result["anonymized_fields"]) == 0 and len(result["personal_info_fields"]) > 0:
            score += 20
        
        result["risk_score"] = min(score, 100)
        
        # 风险等级
        if score >= 60:
            result["risk_level"] = "extreme"
        elif score >= 40:
            result["risk_level"] = "high"
        elif score >= 20:
            result["risk_level"] = "medium"
        else:
            result["risk_level"] = "low"
    
    def check_anonymization_quality(self, fields: List[Dict], 
                                   original_fields: List[str]) -> Dict[str, Any]:
        """
        检查匿名化质量
        对比处理前后的字段
        """
        result = {
            "is_anonymized": False,
            "quality_score": 0,
            "issues": [],
            "suggestions": []
        }
        
        # 检查是否有明显的匿名化标识
        anonymized_count = 0
        for field in fields:
            name = field.get("name", "")
            if any(kw in name.lower() for kw in ["anon", "mask", "hash", "encrypted"]):
                anonymized_count += 1
        
        if anonymized_count > 0:
            result["is_anonymized"] = True
            result["quality_score"] = min(anonymized_count / len(fields) * 100, 100)
        
        if result["quality_score"] < 80:
            result["issues"].append({
                "rule_id": "RULE_D_007",
                "issue": "匿名化不充分，建议加强脱敏措施",
                "severity": "medium"
            })
            result["suggestions"].append("可以使用k-匿名、l-多样性等方法增强匿名化效果")
        
        return result


# 单例
_detector_instance = None

def get_privacy_detector() -> PrivacyRiskDetector:
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = PrivacyRiskDetector()
    return _detector_instance

def detect_privacy_risk(fields: List[Dict]) -> Dict[str, Any]:
    """便捷函数：检测隐私风险"""
    detector = get_privacy_detector()
    return detector.detect_privacy_risk(fields)