#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sqlite3
import os
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_path="/home/ugrad/Luzhonghao/病虫害识别/data/database.db"):
        """
        初始化数据库管理器
        """
        self.db_path = db_path
        self._ensure_db_exists()
    
    def _ensure_db_exists(self):
        """
        确保数据库文件存在并创建必要的表
        """
        # 确保数据目录存在
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # 连接数据库
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建用户表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip_address TEXT,
            user_agent TEXT,
            first_seen TIMESTAMP,
            last_seen TIMESTAMP
        )
        ''')
        
        # 创建 API 调用记录表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_calls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            api_type TEXT,
            model_name TEXT,
            input_tokens INTEGER,
            output_tokens INTEGER,
            total_tokens INTEGER,
            response_time REAL,
            status TEXT,
            error_message TEXT,
            created_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
        
        # 创建诊断记录表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS diagnoses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            image_path TEXT,
            disease_name TEXT,
            diagnosis_result TEXT,
            created_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
        
        # 创建系统日志表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            level TEXT,
            message TEXT,
            module TEXT,
            created_at TIMESTAMP
        )
        ''')
        
        # 提交并关闭连接
        conn.commit()
        conn.close()
    
    def get_user_id(self, ip_address, user_agent):
        """
        获取或创建用户 ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 查找现有用户
        cursor.execute('''
        SELECT id FROM users WHERE ip_address = ?
        ''', (ip_address,))
        result = cursor.fetchone()
        
        if result:
            user_id = result[0]
            # 更新最后访问时间
            cursor.execute('''
            UPDATE users SET last_seen = ?, user_agent = ? WHERE id = ?
            ''', (datetime.now(), user_agent, user_id))
        else:
            # 创建新用户
            cursor.execute('''
            INSERT INTO users (ip_address, user_agent, first_seen, last_seen)
            VALUES (?, ?, ?, ?)
            ''', (ip_address, user_agent, datetime.now(), datetime.now()))
            user_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        return user_id
    
    def record_api_call(self, user_id, api_type, model_name, input_tokens, output_tokens, 
                      response_time, status, error_message=None):
        """
        记录 API 调用
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        total_tokens = input_tokens + output_tokens
        
        cursor.execute('''
        INSERT INTO api_calls (user_id, api_type, model_name, input_tokens, output_tokens, 
                             total_tokens, response_time, status, error_message, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, api_type, model_name, input_tokens, output_tokens, 
              total_tokens, response_time, status, error_message, datetime.now()))
        
        conn.commit()
        conn.close()
    
    def record_diagnosis(self, user_id, image_path, disease_name, diagnosis_result):
        """
        记录诊断结果
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO diagnoses (user_id, image_path, disease_name, diagnosis_result, created_at)
        VALUES (?, ?, ?, ?, ?)
        ''', (user_id, image_path, disease_name, diagnosis_result, datetime.now()))
        
        conn.commit()
        conn.close()
    
    def record_system_log(self, level, message, module):
        """
        记录系统日志
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO system_logs (level, message, module, created_at)
        VALUES (?, ?, ?, ?)
        ''', (level, message, module, datetime.now()))
        
        conn.commit()
        conn.close()
    
    def get_api_stats(self, days=7):
        """
        获取 API 调用统计数据
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 计算开始时间
        start_time = datetime.now()
        start_time = start_time.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # 获取每日统计
        cursor.execute('''
        SELECT 
            DATE(created_at) as date,
            COUNT(*) as call_count,
            SUM(input_tokens) as total_input_tokens,
            SUM(output_tokens) as total_output_tokens,
            SUM(total_tokens) as total_tokens,
            AVG(response_time) as avg_response_time
        FROM api_calls
        WHERE created_at >= ?
        GROUP BY DATE(created_at)
        ORDER BY date
        ''', (start_time,))
        
        daily_stats = cursor.fetchall()
        
        # 获取总体统计
        cursor.execute('''
        SELECT 
            COUNT(*) as total_calls,
            SUM(input_tokens) as total_input_tokens,
            SUM(output_tokens) as total_output_tokens,
            SUM(total_tokens) as total_tokens,
            AVG(response_time) as avg_response_time
        FROM api_calls
        WHERE created_at >= ?
        ''', (start_time,))
        
        overall_stats = cursor.fetchone()
        
        conn.close()
        
        return {
            'daily_stats': daily_stats,
            'overall_stats': overall_stats
        }
    
    def get_diagnosis_stats(self, days=7):
        """
        获取诊断统计数据
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 计算开始时间
        start_time = datetime.now()
        start_time = start_time.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # 获取病害分布
        cursor.execute('''
        SELECT 
            disease_name,
            COUNT(*) as count
        FROM diagnoses
        WHERE created_at >= ? AND disease_name != 'Unknown Disease'
        GROUP BY disease_name
        ORDER BY count DESC
        ''', (start_time,))
        
        disease_distribution = cursor.fetchall()
        
        # 获取每日诊断数量
        cursor.execute('''
        SELECT 
            DATE(created_at) as date,
            COUNT(*) as diagnosis_count
        FROM diagnoses
        WHERE created_at >= ?
        GROUP BY DATE(created_at)
        ORDER BY date
        ''', (start_time,))
        
        daily_diagnoses = cursor.fetchall()
        
        conn.close()
        
        return {
            'disease_distribution': disease_distribution,
            'daily_diagnoses': daily_diagnoses
        }
    
    def get_recent_logs(self, limit=100):
        """
        获取最近的系统日志
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT id, level, message, module, created_at
        FROM system_logs
        ORDER BY created_at DESC
        LIMIT ?
        ''', (limit,))
        
        logs = cursor.fetchall()
        conn.close()
        
        return logs
    
    def get_recent_diagnoses(self, limit=50):
        """
        获取最近的诊断记录
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT d.id, u.ip_address, d.image_path, d.disease_name, d.created_at
        FROM diagnoses d
        JOIN users u ON d.user_id = u.id
        ORDER BY d.created_at DESC
        LIMIT ?
        ''', (limit,))
        
        diagnoses = cursor.fetchall()
        conn.close()
        
        return diagnoses

# 测试数据库连接
if __name__ == "__main__":
    db = DatabaseManager()
    print("数据库初始化成功！")
    
    # 测试插入数据
    user_id = db.get_user_id("127.0.0.1", "Mozilla/5.0")
    print(f"用户 ID: {user_id}")
    
    db.record_api_call(
        user_id=user_id,
        api_type="vision",
        model_name="Qwen2-VL-7B",
        input_tokens=100,
        output_tokens=50,
        response_time=1.5,
        status="success"
    )
    print("API 调用记录成功！")
    
    # 测试统计功能
    stats = db.get_api_stats()
    print("API 统计数据:", stats)
    
    print("数据库测试完成！")
