"""
数据血缘追踪服务
追踪数据来源、流转路径、加工过程
构建数据血缘链路图
"""
from typing import List, Dict, Any, Optional, Set
from collections import defaultdict
import json

class LineageNode:
    """血缘节点"""
    def __init__(self, node_id: str, name: str, node_type: str, department: str = ""):
        self.id = node_id
        self.name = name
        self.node_type = node_type  # catalog, product, process
        self.department = department
        self.attributes = {}
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "node_type": self.node_type,
            "department": self.department
        }

class LineageEdge:
    """血缘边"""
    def __init__(self, source_id: str, target_id: str, process_type: str, 
                 process_desc: str = "", fields_transformed: List[str] = None):
        self.source_id = source_id
        self.target_id = target_id
        self.process_type = process_type  # collection, processing, sharing, etc.
        self.process_desc = process_desc
        self.fields_transformed = fields_transformed or []
    
    def to_dict(self) -> Dict:
        return {
            "source": self.source_id,
            "target": self.target_id,
            "process_type": self.process_type,
            "process_desc": self.process_desc
        }

class DataLineageTracker:
    """数据血缘追踪器"""
    
    def __init__(self):
        self.nodes: Dict[str, LineageNode] = {}
        self.edges: List[LineageEdge] = []
        self.catalog_products: Dict[int, List[str]] = defaultdict(list)  # catalog_id -> product_ids
    
    def add_catalog_node(self, catalog_id: int, catalog_name: str, department: str = "") -> LineageNode:
        """添加数据目录节点"""
        node_id = f"catalog_{catalog_id}"
        node = LineageNode(node_id, catalog_name, "catalog", department)
        self.nodes[node_id] = node
        return node
    
    def add_product_node(self, catalog_id: int, product_id: str, product_name: str) -> LineageNode:
        """添加数据产品节点"""
        node_id = f"product_{product_id}"
        node = LineageNode(node_id, product_name, "product")
        self.nodes[node_id] = node
        self.catalog_products[catalog_id].append(node_id)
        return node
    
    def add_process_node(self, process_id: str, process_name: str, department: str = "") -> LineageNode:
        """添加加工过程节点"""
        node_id = f"process_{process_id}"
        node = LineageNode(node_id, process_name, "process", department)
        self.nodes[node_id] = node
        return node
    
    def add_lineage_edge(self, source_id: str, target_id: str, 
                        process_type: str, process_desc: str = "",
                        fields_transformed: List[str] = None) -> LineageEdge:
        """添加血缘边"""
        edge = LineageEdge(source_id, target_id, process_type, process_desc, fields_transformed)
        self.edges.append(edge)
        return edge
    
    def track_field_lineage(self, catalog_id: int, field_name: str, 
                           source_catalog_id: Optional[int] = None) -> List[str]:
        """
        追踪字段血缘
        返回字段的完整流转路径
        """
        path = []
        
        # 起点
        if source_catalog_id:
            path.append(f"catalog_{source_catalog_id}")
        else:
            path.append(f"catalog_{catalog_id}")
        
        # 查找产品阶段
        product_nodes = self.catalog_products.get(catalog_id, [])
        for pn in product_nodes:
            path.append(pn)
        
        # 查找后续加工
        current = product_nodes[-1] if product_nodes else f"catalog_{catalog_id}"
        downstream = self._get_downstream(current)
        path.extend(downstream)
        
        return path
    
    def _get_downstream(self, node_id: str) -> List[str]:
        """获取下游节点"""
        downstream = []
        for edge in self.edges:
            if edge.source_id == node_id:
                downstream.append(edge.target_id)
        return downstream
    
    def get_lineage_path(self, catalog_id: int) -> Dict[str, Any]:
        """
        获取数据目录的完整血缘路径
        """
        result = {
            "catalog_id": catalog_id,
            "nodes": [],
            "edges": [],
            "is_complete": True,
            "issues": []
        }
        
        catalog_node_id = f"catalog_{catalog_id}"
        
        # 添加主目录节点
        if catalog_node_id in self.nodes:
            result["nodes"].append(self.nodes[catalog_node_id].to_dict())
        
        # 添加产品节点
        product_nodes = self.catalog_products.get(catalog_id, [])
        for pn in product_nodes:
            if pn in self.nodes:
                result["nodes"].append(self.nodes[pn].to_dict())
        
        # 添加相关边
        for edge in self.edges:
            if edge.source_id == catalog_node_id or edge.target_id == catalog_node_id:
                result["edges"].append(edge.to_dict())
        
        # 检查血缘完整性
        if not product_nodes:
            result["issues"].append({
                "rule_id": "RULE_D_009",
                "issue": "该数据目录尚未关联任何数据产品",
                "severity": "low"
            })
            result["is_complete"] = False
        
        return result
    
    def detect_lineage_issues(self, catalog_id: int, fields: List[Dict]) -> List[Dict]:
        """
        检测血缘链路问题
        """
        issues = []
        
        # 检查是否有来源不明的字段
        for field in fields:
            if field.get("source_unknown", False):
                issues.append({
                    "rule_id": "RULE_D_009",
                    "issue": f"字段 '{field.get('name')}' 来源不明确",
                    "severity": "medium",
                    "field": field.get("name")
                })
        
        # 检查加工过程是否记录
        catalog_node_id = f"catalog_{catalog_id}"
        has_processing = any(e.source_id == catalog_node_id and e.process_type == "processing" 
                           for e in self.edges)
        
        if not has_processing and len(self.catalog_products.get(catalog_id, [])) > 0:
            issues.append({
                "rule_id": "RULE_D_010",
                "issue": "数据加工过程未记录",
                "severity": "medium"
            })
        
        return issues
    
    def export_lineage_graph(self, catalog_id: int) -> Dict[str, Any]:
        """
        导出血缘图谱数据（供前端可视化）
        """
        path_data = self.get_lineage_path(catalog_id)
        
        # 添加额外的血缘详情
        catalog_node_id = f"catalog_{catalog_id}"
        
        # 查找所有相关节点（递归获取上下游）
        related_nodes = set()
        related_edges = []
        
        def find_related(node_id: str, direction: str = "both"):
            related_nodes.add(node_id)
            for edge in self.edges:
                if direction in ["both", "down"] and edge.source_id == node_id:
                    related_nodes.add(edge.target_id)
                    related_edges.append(edge.to_dict())
                    find_related(edge.target_id, "down")
                if direction in ["both", "up"] and edge.target_id == node_id:
                    related_nodes.add(edge.source_id)
                    related_edges.append(edge.to_dict())
                    find_related(edge.source_id, "up")
        
        find_related(catalog_node_id)
        
        nodes = [self.nodes[nid].to_dict() for nid in related_nodes if nid in self.nodes]
        
        return {
            "nodes": nodes,
            "edges": related_edges,
            "stats": {
                "total_nodes": len(nodes),
                "total_edges": len(related_edges)
            }
        }


# 关系型血缘追踪（用于跨目录关联）
class RelationalLineageTracker:
    """关系型血缘追踪器"""
    
    def __init__(self):
        self.foreign_key_relations: List[Dict] = []  # 外键关联关系
        self.derived_fields: Dict[str, List[str]] = {}  # 派生字段映射
    
    def add_foreign_key_relation(self, from_catalog: int, from_field: str,
                                to_catalog: int, to_field: str, relation_type: str = "reference"):
        """添加外键关联关系"""
        self.foreign_key_relations.append({
            "from_catalog": from_catalog,
            "from_field": from_field,
            "to_catalog": to_catalog,
            "to_field": to_field,
            "relation_type": relation_type
        })
    
    def add_derived_field(self, source_catalog: int, source_field: str,
                         target_catalog: int, target_field: str,
                         derivation_rule: str = ""):
        """添加字段派生关系"""
        key = f"{target_catalog}:{target_field}"
        if key not in self.derived_fields:
            self.derived_fields[key] = []
        self.derived_fields[key].append({
            "source_catalog": source_catalog,
            "source_field": source_field,
            "derivation_rule": derivation_rule
        })
    
    def get_impact_analysis(self, catalog_id: int) -> Dict[str, Any]:
        """
        影响分析：修改某目录对其他目录的影响
        """
        affected = []
        
        for rel in self.foreign_key_relations:
            if rel["from_catalog"] == catalog_id:
                affected.append({
                    "target_catalog": rel["to_catalog"],
                    "target_field": rel["to_field"],
                    "relation_type": "foreign_key",
                    "impact_level": "high"
                })
        
        for key, sources in self.derived_fields.items():
            for src in sources:
                if src["source_catalog"] == catalog_id:
                    target_catalog, target_field = key.split(":")
                    affected.append({
                        "target_catalog": int(target_catalog),
                        "target_field": target_field,
                        "relation_type": "derived",
                        "impact_level": "medium"
                    })
        
        return {
            "catalog_id": catalog_id,
            "affected_count": len(affected),
            "affected_catalogs": affected
        }


# 单例
_tracker_instance = None

def get_lineage_tracker() -> DataLineageTracker:
    global _tracker_instance
    if _tracker_instance is None:
        _tracker_instance = DataLineageTracker()
    return _tracker_instance

def track_field_lineage(catalog_id: int, field_name: str) -> List[str]:
    """便捷函数：追踪字段血缘"""
    tracker = get_lineage_tracker()
    return tracker.track_field_lineage(catalog_id, field_name)

def get_lineage_path(catalog_id: int) -> Dict[str, Any]:
    """便捷函数：获取血缘路径"""
    tracker = get_lineage_tracker()
    return tracker.get_lineage_path(catalog_id)