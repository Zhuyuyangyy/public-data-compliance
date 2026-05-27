"""
合规报告生成服务
生成授权运营审查意见和整改建议
"""
from typing import Dict, Any, List
from datetime import datetime

class ReportGenerator:
    """合规报告生成器"""
    
    def __init__(self):
        self.report_template = {
            "header": "公共数据资源授权运营合规审查报告",
            "version": "V1.0"
        }
    
    def generate_report(self, catalog_data: Dict, risk_result: Dict,
                       privacy_result: Dict, auth_result: Dict,
                       lineage_result: Dict) -> Dict[str, Any]:
        """
        生成完整的合规审查报告
        """
        report = {
            "report_info": {
                "report_id": f"PCR_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "catalog_id": catalog_data.get("id"),
                "catalog_name": catalog_data.get("name"),
                "department": catalog_data.get("department"),
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "report_type": "授权运营合规审查",
                "version": self.report_template["version"]
            },
            "risk_assessment": {
                "total_score": risk_result.get("total_entropy_score", 0),
                "risk_level": risk_result.get("risk_level", "low"),
                "dimensions": risk_result.get("dimensions", {}),
                "is_coupled": risk_result.get("is_coupled", False),
                "coupling_penalty": risk_result.get("coupling_penalty", 0),
                "fuse_triggered": risk_result.get("fuse_triggered", False),
                "fuse_reason": risk_result.get("fuse_reason", "")
            },
            "privacy_assessment": {
                "personal_info_count": len(privacy_result.get("personal_info_fields", [])),
                "sensitive_info_count": len(privacy_result.get("sensitive_info_fields", [])),
                "reid_risk_count": len(privacy_result.get("reid_risk_fields", [])),
                "anonymization_quality": self._assess_anonymization(privacy_result)
            },
            "authorization_assessment": {
                "is_authorized": auth_result.get("is_authorized", False),
                "authorized_fields": auth_result.get("authorized_fields", []),
                "unauthorized_fields": auth_result.get("unauthorized_fields", []),
                "issues_count": len(auth_result.get("issues", []))
            },
            "lineage_assessment": {
                "is_complete": lineage_result.get("is_complete", True),
                "nodes_count": len(lineage_result.get("nodes", [])),
                "edges_count": len(lineage_result.get("edges", []))
            },
            "issues": self._compile_issues(privacy_result, auth_result, lineage_result, risk_result),
            "review_opinions": [],
            "rectification_suggestions": []
        }
        
        # 生成审查意见
        report["review_opinions"] = self._generate_review_opinions(report)
        
        # 生成整改建议
        report["rectification_suggestions"] = self._generate_rectification_suggestions(report)
        
        return report
    
    def _assess_anonymization(self, privacy_result: Dict) -> str:
        """评估匿名化质量"""
        personal_count = len(privacy_result.get("personal_info_fields", []))
        anonymized_count = len(privacy_result.get("anonymized_fields", []))
        
        if personal_count == 0:
            return "无个人信息"
        
        ratio = anonymized_count / personal_count if personal_count > 0 else 0
        
        if ratio >= 1.0:
            return "优秀"
        elif ratio >= 0.8:
            return "良好"
        elif ratio >= 0.5:
            return "一般"
        else:
            return "不合格"
    
    def _compile_issues(self, privacy_result: Dict, auth_result: Dict,
                        lineage_result: Dict, risk_result: Dict) -> List[Dict]:
        """汇总所有问题"""
        all_issues = []
        
        # 隐私相关问题
        for issue in privacy_result.get("issues", []):
            all_issues.append({
                "category": "privacy",
                "rule_id": issue.get("rule_id", "UNKNOWN"),
                "issue": issue.get("issue", ""),
                "severity": issue.get("severity", "medium"),
                "fields": issue.get("fields", [])
            })
        
        # 授权相关问题
        for issue in auth_result.get("issues", []):
            all_issues.append({
                "category": "authorization",
                "rule_id": issue.get("rule_id", "UNKNOWN"),
                "issue": issue.get("issue", ""),
                "severity": issue.get("severity", "medium")
            })
        
        # 血缘问题
        for issue in lineage_result.get("issues", []):
            all_issues.append({
                "category": "lineage",
                "rule_id": issue.get("rule_id", "UNKNOWN"),
                "issue": issue.get("issue", ""),
                "severity": issue.get("severity", "low")
            })
        
        # 风险耦合问题
        if risk_result.get("is_coupled"):
            all_issues.append({
                "category": "risk_coupling",
                "rule_id": "RULE_COUPLE",
                "issue": f"检测到多维风险耦合，耦合惩罚: {risk_result.get('coupling_penalty', 0)}",
                "severity": "high"
            })
        
        # 熔断问题
        if risk_result.get("fuse_triggered"):
            all_issues.append({
                "category": "risk_fuse",
                "rule_id": "RULE_FUSE",
                "issue": f"风险熔断触发: {risk_result.get('fuse_reason', '')}",
                "severity": "critical"
            })
        
        return all_issues
    
    def _generate_review_opinions(self, report: Dict) -> List[str]:
        """生成审查意见"""
        opinions = []
        
        risk_level = report["risk_assessment"]["risk_level"]
        total_score = report["risk_assessment"]["total_score"]
        
        # 总体意见
        if risk_level in ["extreme", "high"]:
            opinions.append(f"经审查，该数据资源综合风险评分{total_score}分，风险等级{risk_level}，建议暂停当前授权运营活动")
        elif risk_level == "medium":
            opinions.append(f"经审查，该数据资源综合风险评分{total_score}分，风险等级{risk_level}，需完成整改后方可继续")
        else:
            opinions.append(f"经审查，该数据资源综合风险评分{total_score}分，风险等级{risk_level}，基本合规，建议持续监控")
        
        # 隐私意见
        personal_count = report["privacy_assessment"]["personal_info_count"]
        sensitive_count = report["privacy_assessment"]["sensitive_info_count"]
        
        if sensitive_count > 0:
            opinions.append(f"检测到{sensitive_count}个敏感个人信息字段，涉及敏感信息处理需额外审批")
        
        if personal_count > 0:
            opinions.append(f"检测到{personal_count}个个人信息字段，需确保脱敏措施有效")
        
        # 授权意见
        if not report["authorization_assessment"]["is_authorized"]:
            opinions.append("存在越权使用风险，建议重新评估授权范围和有效性")
        
        unauthorized = report["authorization_assessment"]["unauthorized_fields"]
        if unauthorized:
            opinions.append(f"存在{len(unauthorized)}个未授权字段，建议申请扩展授权或调整使用范围")
        
        # 血缘意见
        if not report["lineage_assessment"]["is_complete"]:
            opinions.append("数据血缘链路不完整，建议完善数据流转记录")
        
        return opinions
    
    def _generate_rectification_suggestions(self, report: Dict) -> List[str]:
        """生成整改建议"""
        suggestions = []
        
        # 按优先级排序
        risk_level = report["risk_assessment"]["risk_level"]
        
        # 紧急整改（高风险及以上）
        if risk_level in ["extreme", "high"]:
            suggestions.append("【紧急】立即暂停存在风险的数据操作，制定应急处置方案")
            
            if report["privacy_assessment"]["sensitive_info_count"] > 0:
                suggestions.append("【紧急】对敏感个人信息实施加密存储，限制访问权限")
            
            if not report["authorization_assessment"]["is_authorized"]:
                suggestions.append("【紧急】重新签订授权协议，明确授权范围和有效期")
        
        # 标准整改
        if report["privacy_assessment"]["anonymization_quality"] in ["一般", "不合格"]:
            suggestions.append("建议采用k-匿名、差分隐私等技术提升匿名化质量")
        
        if report["privacy_assessment"]["reid_risk_count"] > 0:
            suggestions.append(f"建议对{report['privacy_assessment']['reid_risk_count']}个再识别风险字段进行泛化处理")
        
        if report["authorization_assessment"]["unauthorized_fields"]:
            fields = report["authorization_assessment"]["unauthorized_fields"]
            suggestions.append(f"建议申请扩展授权，涵盖字段: {', '.join(fields[:5])}{'...' if len(fields) > 5 else ''}")
        
        if not report["lineage_assessment"]["is_complete"]:
            suggestions.append("建议完善数据血缘记录，确保从数据采集到产品发布的全流程可追溯")
        
        # 持续改进
        if risk_level in ["extreme", "high"]:
            suggestions.append("建议每季度进行风险复评，持续监控风险变化")
        
        if report["risk_assessment"]["is_coupled"]:
            suggestions.append("建议建立多维风险耦合监测机制，提前预警风险叠加")
        
        return suggestions
    
    def format_report_markdown(self, report: Dict) -> str:
        """格式化报告为Markdown"""
        md = []
        
        # 标题
        md.append(f"# {self.report_template['header']}")
        md.append(f"**报告编号**: {report['report_info']['report_id']}")
        md.append(f"**生成时间**: {report['report_info']['generated_at']}")
        md.append("")
        
        # 基本信息
        md.append("## 一、基本信息")
        md.append(f"- **数据目录**: {report['report_info']['catalog_name']}")
        md.append(f"- **所属部门**: {report['report_info']['department']}")
        md.append(f"- **数据目录ID**: {report['report_info']['catalog_id']}")
        md.append("")
        
        # 风险评估
        md.append("## 二、风险评估结果")
        assessment = report["risk_assessment"]
        md.append(f"- **综合风险评分**: {assessment['total_score']} 分")
        md.append(f"- **风险等级**: {assessment['risk_level']}")
        md.append(f"- **多维耦合**: {'是' if assessment['is_coupled'] else '否'}")
        if assessment['is_coupled']:
            md.append(f"  - 耦合惩罚: {assessment['coupling_penalty']}")
        md.append(f"- **熔断触发**: {'是' if assessment['fuse_triggered'] else '否'}")
        if assessment['fuse_triggered']:
            md.append(f"  - 熔断原因: {assessment['fuse_reason']}")
        md.append("")
        
        # 分项评分
        md.append("### 分项风险评分")
        dims = assessment.get("dimensions", {})
        md.append(f"- 开放风险: {dims.get('open_risk', 0)}")
        md.append(f"- 授权风险: {dims.get('auth_risk', 0)}")
        md.append(f"- 隐私风险: {dims.get('privacy_risk', 0)}")
        md.append(f"- 再识别风险: {dims.get('reid_risk', 0)}")
        md.append("")
        
        # 问题汇总
        md.append("## 三、问题汇总")
        for i, issue in enumerate(report["issues"], 1):
            severity_icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(issue["severity"], "⚪")
            md.append(f"{i}. [{severity_icon}] {issue['issue']}")
            md.append(f"   - 类别: {issue['category']}, 规则: {issue['rule_id']}")
        md.append("")
        
        # 审查意见
        md.append("## 四、审查意见")
        for opinion in report["review_opinions"]:
            md.append(f"- {opinion}")
        md.append("")
        
        # 整改建议
        md.append("## 五、整改建议")
        for suggestion in report["rectification_suggestions"]:
            md.append(f"- {suggestion}")
        md.append("")
        
        # 页脚
        md.append("---")
        md.append(f"*本报告由公共数据资源授权运营合规审查系统自动生成 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        
        return "\n".join(md)


# 单例
_generator_instance = None

def get_report_generator() -> ReportGenerator:
    global _generator_instance
    if _generator_instance is None:
        _generator_instance = ReportGenerator()
    return _generator_instance

def generate_compliance_report(catalog_data: Dict, risk_result: Dict,
                               privacy_result: Dict, auth_result: Dict,
                               lineage_result: Dict) -> Dict[str, Any]:
    """便捷函数：生成合规报告"""
    generator = get_report_generator()
    return generator.generate_report(catalog_data, risk_result, privacy_result, auth_result, lineage_result)