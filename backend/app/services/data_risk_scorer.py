"""
数据风险熵评分服务
输出开放风险、授权风险、隐私风险、再识别风险
多维风险耦合模型
"""
from typing import Dict, Any, List, Tuple
import math

class RiskEntropyScorer:
    """
    数据风险熵评分器
    
    基于信息熵理论，量化数据风险的不确定性和严重程度
    
    专利核心：多维风险耦合模型
    - 开放风险：数据对外开放的暴露程度
    - 授权风险：授权边界清晰度
    - 隐私风险：个人信息泄露风险
    - 再识别风险：去标识化后被重识别风险
    """
    
    def __init__(self):
        # 各维度权重（可根据实际调整）
        self.weights = {
            "open_risk": 0.25,
            "auth_risk": 0.25,
            "privacy_risk": 0.30,
            "reid_risk": 0.20
        }
        
        # 耦合系数（风险间相互影响）
        self.coupling_matrix = {
            ("privacy", "reid"): 0.8,  # 隐私+再识别高度耦合
            ("open", "privacy"): 0.6,  # 开放度与隐私风险中度耦合
            ("auth", "privacy"): 0.5,  # 授权与隐私中度耦合
            ("open", "reid"): 0.7,     # 开放与再识别高中度耦合
        }
    
    def score(self, catalog_data: Dict, privacy_result: Dict,
             auth_result: Dict, lineage_result: Dict) -> Dict[str, Any]:
        """
        计算综合风险熵评分
        
        参数:
            catalog_data: 数据目录信息
            privacy_result: 隐私风险检测结果
            auth_result: 授权检查结果
            lineage_result: 血缘分析结果
        
        返回:
            风险评分结果
        """
        result = {
            "catalog_id": catalog_data.get("id"),
            "catalog_name": catalog_data.get("name"),
            "dimensions": {},
            "total_entropy_score": 0.0,
            "risk_level": "low",
            "is_coupled": False,
            "coupling_penalty": 0.0,
            "fuse_triggered": False,
            "fuse_reason": "",
            "details": [],
            "suggestions": []
        }
        
        # 1. 开放风险评分
        open_risk = self._score_open_risk(catalog_data)
        result["dimensions"]["open_risk"] = open_risk
        
        # 2. 授权风险评分
        auth_risk = self._score_auth_risk(auth_result)
        result["dimensions"]["auth_risk"] = auth_risk
        
        # 3. 隐私风险评分
        privacy_risk = self._score_privacy_risk(privacy_result)
        result["dimensions"]["privacy_risk"] = privacy_risk
        
        # 4. 再识别风险评分
        reid_risk = self._score_reid_risk(privacy_result)
        result["dimensions"]["reid_risk"] = reid_risk
        
        # 5. 多维耦合分析
        coupling_score, coupling_details = self._analyze_coupling(
            open_risk, auth_risk, privacy_risk, reid_risk
        )
        result["is_coupled"] = coupling_score > 0
        result["coupling_penalty"] = coupling_score * 10
        
        # 6. 计算综合熵评分
        total = (
            open_risk * self.weights["open_risk"] +
            auth_risk * self.weights["auth_risk"] +
            privacy_risk * self.weights["privacy_risk"] +
            reid_risk * self.weights["reid_risk"]
        )
        
        # 应用耦合惩罚
        total = min(total + result["coupling_penalty"], 100)
        result["total_entropy_score"] = round(total, 2)
        
        # 7. 风险熔断机制
        fuse_result = self._check_fuse_condition(
            open_risk, auth_risk, privacy_risk, reid_risk
        )
        result["fuse_triggered"] = fuse_result["triggered"]
        result["fuse_reason"] = fuse_result.get("reason", "")
        
        if result["fuse_triggered"]:
            result["total_entropy_score"] = min(result["total_entropy_score"] * 1.5, 100)
        
        # 8. 确定风险等级
        result["risk_level"] = self._get_risk_level(result["total_entropy_score"])
        
        # 9. 生成建议
        result["details"] = coupling_details
        result["suggestions"] = self._generate_suggestions(
            open_risk, auth_risk, privacy_risk, reid_risk, coupling_score
        )
        
        return result
    
    def _score_open_risk(self, catalog_data: Dict) -> float:
        """
        开放风险评分
        数据对外开放的暴露程度
        """
        score = 0.0
        
        # 数据类型风险
        data_type = catalog_data.get("data_type", "public")
        if data_type == "sensitive":
            score += 30
        elif data_type == "personal":
            score += 50
        
        # 敏感等级风险
        sensitivity = catalog_data.get("sensitivity_level", "low")
        sensitivity_scores = {"low": 5, "medium": 20, "high": 40, "extreme": 60}
        score += sensitivity_scores.get(sensitivity, 10)
        
        # 授权范围（无授权=高风险）
        auth_scope = catalog_data.get("auth_scope", "")
        if not auth_scope:
            score += 20
        
        return min(score, 100)
    
    def _score_auth_risk(self, auth_result: Dict) -> float:
        """
        授权风险评分
        授权边界清晰度和合规性
        """
        score = 0.0
        
        if not auth_result:
            return 50.0  # 无授权记录，默认中等风险
        
        # 未授权字段
        unauthorized = auth_result.get("unauthorized_fields", [])
        if unauthorized:
            score += len(unauthorized) * 10
        
        # 授权失效
        if not auth_result.get("is_authorized", False):
            score += 30
        
        # 越权用途
        for issue in auth_result.get("issues", []):
            if issue.get("rule_id") == "RULE_D_006":
                score += 25
        
        return min(score, 100)
    
    def _score_privacy_risk(self, privacy_result: Dict) -> float:
        """
        隐私风险评分
        个人信息泄露风险
        """
        score = 0.0
        
        if not privacy_result:
            return 0.0
        
        # 个人信息字段数
        personal_count = len(privacy_result.get("personal_info_fields", []))
        score += personal_count * 8
        
        # 敏感信息字段数（权重更高）
        sensitive_count = len(privacy_result.get("sensitive_info_fields", []))
        score += sensitive_count * 15
        
        # 未脱敏字段
        issues = privacy_result.get("issues", [])
        for issue in issues:
            if issue.get("rule_id") in ["RULE_D_001", "RULE_D_007"]:
                score += 10
        
        return min(score, 100)
    
    def _score_reid_risk(self, privacy_result: Dict) -> float:
        """
        再识别风险评分
        去标识化后被重识别的风险
        """
        score = 0.0
        
        if not privacy_result:
            return 0.0
        
        # 再识别风险组合
        reid_risks = privacy_result.get("reid_risk_fields", [])
        score += len(reid_risks) * 20
        
        # 唯一标识符风险
        field_names = [f.get("field_name", "") for f in privacy_result.get("personal_info_fields", [])]
        for name in field_names:
            if any(kw in name.lower() for kw in ["id", "编号", "编码"]):
                score += 15
        
        return min(score, 100)
    
    def _analyze_coupling(self, open_r: float, auth_r: float, 
                         privacy_r: float, reid_r: float) -> Tuple[float, List[Dict]]:
        """
        多维风险耦合分析
        
        当多个维度风险同时较高时，耦合效应会放大总体风险
        """
        coupling_score = 0.0
        details = []
        
        # 检查各维度两两耦合
        high_threshold = 50
        
        risk_levels = [
            ("open", open_r),
            ("auth", auth_r),
            ("privacy", privacy_r),
            ("reid", reid_r)
        ]
        
        for i in range(len(risk_levels)):
            for j in range(i + 1, len(risk_levels)):
                dim1, score1 = risk_levels[i]
                dim2, score2 = risk_levels[j]
                
                # 两者都高于阈值
                if score1 >= high_threshold and score2 >= high_threshold:
                    key = tuple(sorted([dim1, dim2]))
                    coupling_coeff = self.coupling_matrix.get(key, 0.3)
                    
                    # 耦合效应 = 两者均值 * 耦合系数
                    coupling_effect = ((score1 + score2) / 2) * coupling_coeff
                    coupling_score += coupling_effect * 0.1
                    
                    details.append({
                        "coupled_dims": [dim1, dim2],
                        "coupling_effect": round(coupling_effect, 2),
                        "explanation": f"{dim1}与{dim2}风险耦合，放大总体风险"
                    })
        
        return min(coupling_score, 30), details
    
    def _check_fuse_condition(self, open_r: float, auth_r: float,
                             privacy_r: float, reid_r: float) -> Dict:
        """
        风险熔断机制
        
        当任一维度风险极高时，触发熔断，大幅提升总体风险
        """
        fuse_threshold = 80
        extreme_threshold = 90
        
        result = {"triggered": False, "reason": ""}
        
        risks = [
            ("open_risk", open_r),
            ("auth_risk", auth_r),
            ("privacy_risk", privacy_r),
            ("reid_risk", reid_r)
        ]
        
        for dim_name, score in risks:
            if score >= extreme_threshold:
                result["triggered"] = True
                result["reason"] = f"{dim_name}达到极值风险({score})，触发熔断"
                return result
            elif score >= fuse_threshold:
                count_high = sum(1 for _, s in risks if s >= fuse_threshold)
                if count_high >= 2:
                    result["triggered"] = True
                    result["reason"] = f"多个维度({count_high}个)达到高压风险阈值，触发熔断"
                    return result
        
        return result
    
    def _get_risk_level(self, total_score: float) -> str:
        """根据总分确定风险等级"""
        if total_score >= 80:
            return "extreme"
        elif total_score >= 60:
            return "high"
        elif total_score >= 40:
            return "medium"
        else:
            return "low"
    
    def _generate_suggestions(self, open_r: float, auth_r: float,
                            privacy_r: float, reid_r: float,
                            coupling_score: float) -> List[str]:
        """生成整改建议"""
        suggestions = []
        
        if open_r >= 50:
            suggestions.append("建议限制数据开放范围，设置访问权限控制")
        
        if auth_r >= 50:
            suggestions.append("建议完善授权管理，明确授权对象和范围")
        
        if privacy_r >= 50:
            suggestions.append("建议对个人信息进行脱敏处理，加强隐私保护")
        
        if reid_r >= 50:
            suggestions.append("建议采用k-匿名、差分隐私等技术防止重识别")
        
        if coupling_score >= 15:
            suggestions.append("存在多维风险耦合，建议进行系统性整改")
        
        if not suggestions:
            suggestions.append("当前风险可控，建议持续监控")
        
        return suggestions


# 单例
_scorer_instance = None

def get_risk_scorer() -> RiskEntropyScorer:
    global _scorer_instance
    if _scorer_instance is None:
        _scorer_instance = RiskEntropyScorer()
    return _scorer_instance

def score_data_risk(catalog_data: Dict, privacy_result: Dict,
                   auth_result: Dict, lineage_result: Dict) -> Dict[str, Any]:
    """便捷函数：评分数据风险"""
    scorer = get_risk_scorer()
    return scorer.score(catalog_data, privacy_result, auth_result, lineage_result)