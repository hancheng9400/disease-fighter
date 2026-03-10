#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sqlite3
import os
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
from database import DatabaseManager

class StatsManager:
    def __init__(self, db_path="/home/ugrad/Luzhonghao/病虫害识别/data/database.db"):
        """
        初始化统计管理器
        """
        self.db_path = db_path
    
    def get_connection(self):
        """
        获取数据库连接
        """
        return sqlite3.connect(self.db_path)
    
    def get_token_usage_stats(self, days=7):
        """
        获取 Token 使用统计
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 计算开始时间
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # 获取每日 Token 使用量
        cursor.execute('''
        SELECT 
            DATE(created_at) as date,
            SUM(input_tokens) as input_tokens,
            SUM(output_tokens) as output_tokens,
            SUM(total_tokens) as total_tokens
        FROM api_calls
        WHERE created_at >= ?
        GROUP BY DATE(created_at)
        ORDER BY date
        ''', (start_date,))
        
        daily_tokens = cursor.fetchall()
        
        # 获取总体 Token 使用量
        cursor.execute('''
        SELECT 
            SUM(input_tokens) as total_input,
            SUM(output_tokens) as total_output,
            SUM(total_tokens) as total_tokens,
            AVG(total_tokens) as avg_tokens_per_call
        FROM api_calls
        WHERE created_at >= ?
        ''', (start_date,))
        
        overall_tokens = cursor.fetchone()
        
        # 获取按模型分类的 Token 使用量
        cursor.execute('''
        SELECT 
            model_name,
            SUM(total_tokens) as total_tokens,
            COUNT(*) as call_count
        FROM api_calls
        WHERE created_at >= ?
        GROUP BY model_name
        ORDER BY total_tokens DESC
        ''', (start_date,))
        
        model_tokens = cursor.fetchall()
        
        conn.close()
        
        return {
            'daily_tokens': daily_tokens,
            'overall_tokens': overall_tokens,
            'model_tokens': model_tokens
        }
    
    def get_api_call_stats(self, days=7):
        """
        获取 API 调用统计
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 计算开始时间
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # 获取每日 API 调用量
        cursor.execute('''
        SELECT 
            DATE(created_at) as date,
            COUNT(*) as call_count,
            AVG(response_time) as avg_response_time
        FROM api_calls
        WHERE created_at >= ?
        GROUP BY DATE(created_at)
        ORDER BY date
        ''', (start_date,))
        
        daily_calls = cursor.fetchall()
        
        # 获取总体 API 调用统计
        cursor.execute('''
        SELECT 
            COUNT(*) as total_calls,
            SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful_calls,
            SUM(CASE WHEN status != 'success' THEN 1 ELSE 0 END) as failed_calls,
            AVG(response_time) as avg_response_time
        FROM api_calls
        WHERE created_at >= ?
        ''', (start_date,))
        
        overall_calls = cursor.fetchone()
        
        # 获取按 API 类型分类的调用统计
        cursor.execute('''
        SELECT 
            api_type,
            COUNT(*) as call_count,
            AVG(response_time) as avg_response_time
        FROM api_calls
        WHERE created_at >= ?
        GROUP BY api_type
        ORDER BY call_count DESC
        ''', (start_date,))
        
        api_type_calls = cursor.fetchall()
        
        conn.close()
        
        return {
            'daily_calls': daily_calls,
            'overall_calls': overall_calls,
            'api_type_calls': api_type_calls
        }
    
    def get_diagnosis_stats(self, days=7):
        """
        获取诊断统计
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 计算开始时间
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # 获取每日诊断数量
        cursor.execute('''
        SELECT 
            DATE(created_at) as date,
            COUNT(*) as diagnosis_count
        FROM diagnoses
        WHERE created_at >= ?
        GROUP BY DATE(created_at)
        ORDER BY date
        ''', (start_date,))
        
        daily_diagnoses = cursor.fetchall()
        
        # 获取病害分布
        cursor.execute('''
        SELECT 
            disease_name,
            COUNT(*) as count
        FROM diagnoses
        WHERE created_at >= ? AND disease_name != 'Unknown Disease'
        GROUP BY disease_name
        ORDER BY count DESC
        LIMIT 10
        ''', (start_date,))
        
        disease_distribution = cursor.fetchall()
        
        # 获取总体诊断统计
        cursor.execute('''
        SELECT 
            COUNT(*) as total_diagnoses,
            SUM(CASE WHEN disease_name != 'Unknown Disease' THEN 1 ELSE 0 END) as identified_diagnoses,
            SUM(CASE WHEN disease_name = 'Unknown Disease' THEN 1 ELSE 0 END) as unknown_diagnoses
        FROM diagnoses
        WHERE created_at >= ?
        ''', (start_date,))
        
        overall_diagnoses = cursor.fetchone()
        
        conn.close()
        
        return {
            'daily_diagnoses': daily_diagnoses,
            'disease_distribution': disease_distribution,
            'overall_diagnoses': overall_diagnoses
        }
    
    def get_user_stats(self, days=7):
        """
        获取用户统计
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 计算开始时间
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # 获取每日活跃用户数
        cursor.execute('''
        SELECT 
            DATE(last_seen) as date,
            COUNT(DISTINCT id) as active_users
        FROM users
        WHERE last_seen >= ?
        GROUP BY DATE(last_seen)
        ORDER BY date
        ''', (start_date,))
        
        daily_users = cursor.fetchall()
        
        # 获取总体用户统计
        cursor.execute('''
        SELECT 
            COUNT(*) as total_users,
            COUNT(CASE WHEN first_seen >= ? THEN 1 END) as new_users
        FROM users
        ''', (start_date,))
        
        overall_users = cursor.fetchone()
        
        conn.close()
        
        return {
            'daily_users': daily_users,
            'overall_users': overall_users
        }
    
    def generate_token_usage_chart(self, days=7):
        """
        生成 Token 使用量图表
        """
        stats = self.get_token_usage_stats(days)
        daily_tokens = stats['daily_tokens']
        
        if not daily_tokens:
            return "暂无数据"
        
        dates = [item[0] for item in daily_tokens]
        input_tokens = [item[1] or 0 for item in daily_tokens]
        output_tokens = [item[2] or 0 for item in daily_tokens]
        total_tokens = [item[3] or 0 for item in daily_tokens]
        
        fig = go.Figure()
        fig.add_trace(go.Bar(x=dates, y=input_tokens, name='输入 Token'))
        fig.add_trace(go.Bar(x=dates, y=output_tokens, name='输出 Token'))
        fig.add_trace(go.Scatter(x=dates, y=total_tokens, name='总 Token', yaxis='y2'))
        
        fig.update_layout(
            title=f'Token 使用量趋势 ({days}天)',
            xaxis_title='日期',
            yaxis_title='Token 数量',
            yaxis2=dict(
                title='总 Token',
                overlaying='y',
                side='right'
            ),
            barmode='stack',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        return fig.to_html(full_html=False)
    
    def generate_api_call_chart(self, days=7):
        """
        生成 API 调用统计图表
        """
        stats = self.get_api_call_stats(days)
        daily_calls = stats['daily_calls']
        
        if not daily_calls:
            return "暂无数据"
        
        dates = [item[0] for item in daily_calls]
        call_counts = [item[1] for item in daily_calls]
        response_times = [item[2] or 0 for item in daily_calls]
        
        fig = go.Figure()
        fig.add_trace(go.Bar(x=dates, y=call_counts, name='API 调用次数', yaxis='y1'))
        fig.add_trace(go.Scatter(x=dates, y=response_times, name='平均响应时间 (秒)', yaxis='y2'))
        
        fig.update_layout(
            title=f'API 调用统计 ({days}天)',
            xaxis_title='日期',
            yaxis_title='调用次数',
            yaxis2=dict(
                title='响应时间 (秒)',
                overlaying='y',
                side='right'
            ),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        return fig.to_html(full_html=False)
    
    def generate_disease_distribution_chart(self, days=7):
        """
        生成病害分布图表
        """
        stats = self.get_diagnosis_stats(days)
        disease_distribution = stats['disease_distribution']
        
        if not disease_distribution:
            return "暂无数据"
        
        diseases = [item[0] for item in disease_distribution]
        counts = [item[1] for item in disease_distribution]
        
        fig = px.pie(
            names=diseases,
            values=counts,
            title=f'病害分布 ({days}天)',
            hole=0.3
        )
        
        return fig.to_html(full_html=False)
    
    def generate_daily_diagnosis_chart(self, days=7):
        """
        生成每日诊断数量图表
        """
        stats = self.get_diagnosis_stats(days)
        daily_diagnoses = stats['daily_diagnoses']
        
        if not daily_diagnoses:
            return "暂无数据"
        
        dates = [item[0] for item in daily_diagnoses]
        counts = [item[1] for item in daily_diagnoses]
        
        fig = go.Figure()
        fig.add_trace(go.Bar(x=dates, y=counts, name='诊断数量'))
        
        fig.update_layout(
            title=f'每日诊断数量 ({days}天)',
            xaxis_title='日期',
            yaxis_title='诊断数量'
        )
        
        return fig.to_html(full_html=False)
    
    def get_summary_stats(self, days=7):
        """
        获取汇总统计信息
        """
        token_stats = self.get_token_usage_stats(days)
        api_stats = self.get_api_call_stats(days)
        diagnosis_stats = self.get_diagnosis_stats(days)
        user_stats = self.get_user_stats(days)
        
        return {
            'token_usage': token_stats['overall_tokens'],
            'api_calls': api_stats['overall_calls'],
            'diagnoses': diagnosis_stats['overall_diagnoses'],
            'users': user_stats['overall_users']
        }

# 测试统计功能
if __name__ == "__main__":
    stats = StatsManager()
    
    # 测试 Token 使用统计
    print("Token 使用统计:")
    token_stats = stats.get_token_usage_stats()
    print(f"总体 Token 使用: {token_stats['overall_tokens']}")
    print(f"按模型分类: {token_stats['model_tokens']}")
    
    # 测试 API 调用统计
    print("\nAPI 调用统计:")
    api_stats = stats.get_api_call_stats()
    print(f"总体调用: {api_stats['overall_calls']}")
    
    # 测试诊断统计
    print("\n诊断统计:")
    diagnosis_stats = stats.get_diagnosis_stats()
    print(f"总体诊断: {diagnosis_stats['overall_diagnoses']}")
    print(f"病害分布: {diagnosis_stats['disease_distribution']}")
    
    # 测试用户统计
    print("\n用户统计:")
    user_stats = stats.get_user_stats()
    print(f"总体用户: {user_stats['overall_users']}")
    
    # 测试汇总统计
    print("\n汇总统计:")
    summary = stats.get_summary_stats()
    print(summary)
    
    print("\n统计分析功能测试完成！")
