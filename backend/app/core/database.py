"""
数据库模块 - SQLite 轻量化存储
公共数据授权运营合规审查与数据风险熵评估系统
"""
import sqlite3
import os
from datetime import datetime
from typing import Optional

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "public_data_compliance.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cursor = conn.cursor()
    
    # 规则库表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rule_id TEXT UNIQUE NOT NULL,
            rule_type TEXT NOT NULL,
            description TEXT,
            severity TEXT NOT NULL,
            penalty INTEGER DEFAULT 10,
            enabled INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 数据目录表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS data_catalogs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            department TEXT,
            data_type TEXT,
            fields_json TEXT,
            sensitivity_level TEXT DEFAULT 'low',
            source_info TEXT,
            auth_scope TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 授权记录表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS authorization_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            catalog_id INTEGER NOT NULL,
            authorized_party TEXT NOT NULL,
            usage_scope TEXT,
            valid_from DATE,
            valid_to DATE,
            status TEXT DEFAULT 'active',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (catalog_id) REFERENCES data_catalogs(id)
        )
    """)
    
    # 数据血缘表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS data_lineage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_catalog INTEGER NOT NULL,
            target_product TEXT,
            process_type TEXT,
            lineage_data TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (source_catalog) REFERENCES data_catalogs(id)
        )
    """)
    
    # 分析结果表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analysis_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            catalog_id INTEGER NOT NULL,
            risk_score REAL DEFAULT 0.0,
            risk_level TEXT DEFAULT 'low',
            open_risk REAL DEFAULT 0.0,
            auth_risk REAL DEFAULT 0.0,
            privacy_risk REAL DEFAULT 0.0,
            reid_risk REAL DEFAULT 0.0,
            details_json TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (catalog_id) REFERENCES data_catalogs(id)
        )
    """)
    
    # 审计日志表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT NOT NULL,
            target_type TEXT,
            target_id INTEGER,
            details TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()
    
    # 初始化默认规则
    init_default_rules()

def init_default_rules():
    conn = get_conn()
    cursor = conn.cursor()
    
    default_rules = [
        ("RULE_D_001", "privacy", "涉及个人信息（需脱敏）", "high", 25),
        ("RULE_D_002", "privacy", "涉及敏感个人信息（需审批）", "high", 30),
        ("RULE_D_003", "authorization", "超出授权范围使用", "high", 35),
        ("RULE_D_004", "authorization", "跨部门共享未取得授权", "medium", 20),
        ("RULE_D_005", "reid", "数据产品存在再识别风险", "high", 30),
        ("RULE_D_006", "authorization", "数据运营机构越权开发", "high", 35),
        ("RULE_D_007", "privacy", "匿名化不充分", "medium", 20),
        ("RULE_D_008", "data_type", "数据类型识别异常", "medium", 15),
        ("RULE_D_009", "lineage", "数据血缘链路不完整", "low", 10),
        ("RULE_D_010", "lineage", "数据加工过程未记录", "medium", 15),
    ]
    
    for rule in default_rules:
        cursor.execute("""
            INSERT OR IGNORE INTO rules (rule_id, rule_type, description, severity, penalty)
            VALUES (?, ?, ?, ?, ?)
        """, rule)
    
    conn.commit()
    conn.close()

def log_audit(action: str, target_type: str = "", target_id: int = None, details: str = ""):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO audit_logs (action, target_type, target_id, details)
        VALUES (?, ?, ?, ?)
    """, (action, target_type, target_id, details))
    conn.commit()
    conn.close()

init_db()