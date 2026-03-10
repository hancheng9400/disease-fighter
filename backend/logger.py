#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import re
import time
from datetime import datetime
from database import DatabaseManager

class Logger:
    def __init__(self, log_dir="/home/ugrad/Luzhonghao/log/Agent"):
        """
        初始化日志管理器
        """
        self.log_dir = log_dir
        self.db = DatabaseManager()
        self.log_patterns = {
            'vision_api': {
                'token_usage': r'tokens\s+used:\s+(\d+)',
                'response_time': r'response\s+time:\s+(\d+\.\d+)s',
                'status': r'status:\s+(\w+)',
                'error': r'error:\s+(.*)'
            },
            'text_api': {
                'token_usage': r'tokens\s+used:\s+(\d+)',
                'response_time': r'response\s+time:\s+(\d+\.\d+)s',
                'status': r'status:\s+(\w+)',
                'error': r'error:\s+(.*)'
            }
        }
    
    def collect_logs(self):
        """
        收集并解析日志文件
        """
        logs = []
        
        # 收集视觉 API 日志
        vision_log_file = os.path.join(self.log_dir, "vision_api.log")
        if os.path.exists(vision_log_file):
            vision_logs = self._parse_log_file(vision_log_file, 'vision_api')
            logs.extend(vision_logs)
        
        # 收集文本 API 日志
        text_log_file = os.path.join(self.log_dir, "text_api.log")
        if os.path.exists(text_log_file):
            text_logs = self._parse_log_file(text_log_file, 'text_api')
            logs.extend(text_logs)
        
        # 收集 Gradio 日志
        gradio_log_file = os.path.join(self.log_dir, "gradio_app.log")
        if os.path.exists(gradio_log_file):
            gradio_logs = self._parse_log_file(gradio_log_file, 'gradio')
            logs.extend(gradio_logs)
        
        return logs
    
    def _parse_log_file(self, log_file, api_type):
        """
        解析日志文件
        """
        logs = []
        
        try:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # 解析时间戳
                    timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})', line)
                    timestamp = timestamp_match.group(1) if timestamp_match else datetime.now().strftime('%Y-%m-%d %H:%M:%S,%f')[:-3]
                    
                    # 解析日志级别
                    level_match = re.search(r'\[(INFO|WARNING|ERROR|DEBUG)\]', line)
                    level = level_match.group(1) if level_match else 'INFO'
                    
                    # 解析消息
                    message = line
                    
                    # 提取 Token 使用量
                    token_usage = 0
                    if api_type in self.log_patterns:
                        token_match = re.search(self.log_patterns[api_type]['token_usage'], line)
                        if token_match:
                            token_usage = int(token_match.group(1))
                    
                    # 提取响应时间
                    response_time = 0.0
                    if api_type in self.log_patterns:
                        time_match = re.search(self.log_patterns[api_type]['response_time'], line)
                        if time_match:
                            response_time = float(time_match.group(1))
                    
                    # 提取状态
                    status = 'unknown'
                    if api_type in self.log_patterns:
                        status_match = re.search(self.log_patterns[api_type]['status'], line)
                        if status_match:
                            status = status_match.group(1)
                    
                    # 提取错误信息
                    error_message = None
                    if api_type in self.log_patterns:
                        error_match = re.search(self.log_patterns[api_type]['error'], line)
                        if error_match:
                            error_message = error_match.group(1)
                    
                    # 构建日志条目
                    log_entry = {
                        'timestamp': timestamp,
                        'level': level,
                        'api_type': api_type,
                        'message': message,
                        'token_usage': token_usage,
                        'response_time': response_time,
                        'status': status,
                        'error_message': error_message
                    }
                    
                    logs.append(log_entry)
                    
                    # 存储到数据库
                    self._store_log(log_entry)
                    
        except Exception as e:
            print(f"解析日志文件 {log_file} 时出错: {str(e)}")
        
        return logs
    
    def _store_log(self, log_entry):
        """
        存储日志到数据库
        """
        try:
            # 记录系统日志
            self.db.record_system_log(
                level=log_entry['level'],
                message=log_entry['message'],
                module=log_entry['api_type']
            )
            
            # 如果是 API 调用日志，记录到 API 调用表
            if log_entry['api_type'] in ['vision_api', 'text_api'] and log_entry['token_usage'] > 0:
                # 假设用户 ID 为 1（实际应用中需要根据 IP 地址获取）
                user_id = 1
                model_name = 'Qwen2-VL-7B' if log_entry['api_type'] == 'vision_api' else 'Qwen2.5-3B-Instruct'
                
                self.db.record_api_call(
                    user_id=user_id,
                    api_type=log_entry['api_type'],
                    model_name=model_name,
                    input_tokens=log_entry['token_usage'] // 2,  # 简化处理，实际应该从日志中提取
                    output_tokens=log_entry['token_usage'] // 2,
                    response_time=log_entry['response_time'],
                    status=log_entry['status'],
                    error_message=log_entry['error_message']
                )
                
        except Exception as e:
            print(f"存储日志时出错: {str(e)}")
    
    def monitor_logs(self, interval=60):
        """
        实时监控日志文件
        """
        print("开始监控日志文件...")
        
        while True:
            try:
                self.collect_logs()
                time.sleep(interval)
            except KeyboardInterrupt:
                print("停止监控日志文件")
                break
            except Exception as e:
                print(f"监控日志时出错: {str(e)}")
                time.sleep(interval)
    
    def get_recent_logs(self, api_type=None, limit=100):
        """
        获取最近的日志
        """
        # 从数据库获取日志
        logs = self.db.get_recent_logs(limit)
        
        # 过滤 API 类型
        if api_type:
            logs = [log for log in logs if log[3] == api_type]
        
        return logs
    
    def get_log_stats(self, days=7):
        """
        获取日志统计信息
        """
        # 从数据库获取 API 统计数据
        api_stats = self.db.get_api_stats(days)
        
        # 从数据库获取诊断统计数据
        diagnosis_stats = self.db.get_diagnosis_stats(days)
        
        return {
            'api_stats': api_stats,
            'diagnosis_stats': diagnosis_stats
        }

# 测试日志收集
if __name__ == "__main__":
    logger = Logger()
    
    # 收集日志
    print("收集日志...")
    logs = logger.collect_logs()
    print(f"收集到 {len(logs)} 条日志")
    
    # 获取统计信息
    print("\n获取统计信息...")
    stats = logger.get_log_stats()
    print("API 统计:", stats['api_stats']['overall_stats'])
    print("诊断统计:", stats['diagnosis_stats'])
    
    # 获取最近日志
    print("\n获取最近 10 条日志...")
    recent_logs = logger.get_recent_logs(limit=10)
    for log in recent_logs:
        print(f"{log[4]} [{log[1]}] {log[2]} (模块: {log[3]})")
    
    print("\n日志收集系统测试完成！")
