#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import gradio as gr
from database import DatabaseManager
from logger import Logger
from stats import StatsManager
from datetime import datetime

class AdminDashboard:
    def __init__(self):
        """
        初始化管理后台
        """
        self.db = DatabaseManager()
        self.logger = Logger()
        self.stats = StatsManager()
    
    def get_summary_stats(self):
        """
        获取汇总统计信息
        """
        summary = self.stats.get_summary_stats()
        
        token_usage = summary['token_usage']
        api_calls = summary['api_calls']
        diagnoses = summary['diagnoses']
        users = summary['users']
        
        return {
            'total_tokens': token_usage[2] if token_usage else 0,
            'total_api_calls': api_calls[0] if api_calls else 0,
            'successful_calls': api_calls[1] if api_calls else 0,
            'failed_calls': api_calls[2] if api_calls else 0,
            'total_diagnoses': diagnoses[0] if diagnoses else 0,
            'identified_diagnoses': diagnoses[1] if diagnoses else 0,
            'unknown_diagnoses': diagnoses[2] if diagnoses else 0,
            'total_users': users[0] if users else 0,
            'new_users': users[1] if users else 0
        }
    
    def get_recent_logs(self, limit=50):
        """
        获取最近的系统日志 (科技蓝风格的终端日志)
        """
        logs = self.db.get_recent_logs(limit)
        
        log_html = "<div style='background: #0f172a; border-radius: 16px; padding: 24px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); overflow-x: auto; margin-top: 10px; border: 1px solid #1e293b;'>"
        log_html += "<div style='display: flex; align-items: center; margin-bottom: 16px; border-bottom: 1px solid #334155; padding-bottom: 12px;'>"
        log_html += "<span style='color: #f8fafc; font-weight: 700; font-size: 16px;'>💻 实时终端日志 (Live Tail)</span>"
        log_html += "<span style='margin-left: auto; background: linear-gradient(135deg, #064e3b 0%, #059669 100%); color: #34d399; font-size: 12px; padding: 4px 12px; border-radius: 999px; display: flex; align-items: center; box-shadow: 0 0 10px rgba(16, 185, 129, 0.2);'><span style='width: 8px; height: 8px; background: #10b981; border-radius: 50%; margin-right: 6px;'></span> API Connected</span>"
        log_html += "</div>"
        log_html += "<table style='width: 100%; border-collapse: collapse; text-align: left; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size: 13.5px;'>"
        
        for log in logs:
            level = log[1]
            color = "#94a3b8" # default INFO
            if level == "ERROR":
                color = "#f87171"
            elif level == "WARNING" or level == "WARN":
                color = "#fbbf24"
            
            log_html += "<tr style='transition: background 0.2s;' onmouseover='this.style.background=\"#1e293b\"' onmouseout='this.style.background=\"transparent\"'>"
            log_html += f"<td style='padding: 6px 8px; color: #64748b; width: 170px; white-space: nowrap;'>[{log[4]}]</td>"
            log_html += f"<td style='padding: 6px 8px; color: {color}; width: 80px; font-weight: 600;'>[{level}]</td>"
            log_html += f"<td style='padding: 6px 8px; color: #cbd5e1;'>[{log[3]}] {log[2]}</td>"
            log_html += "</tr>"
            
        log_html += "<tr><td colspan='3' style='padding-top: 16px; color: #475569; font-style: italic;'>等待新日志输入... _</td></tr>"
        log_html += "</table></div>"
        return log_html
    
    def get_recent_diagnoses(self, limit=50):
        """
        获取最近的诊断记录 (科技蓝 + 生态绿风格)
        """
        diagnoses = self.db.get_recent_diagnoses(limit)
        
        diagnosis_html = "<div style='overflow-x: auto; background: white; border-radius: 16px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); border: 1px solid #e2e8f0; margin-top: 10px;'>"
        diagnosis_html += "<table style='width: 100%; border-collapse: collapse; text-align: left; font-size: 14px;'>"
        diagnosis_html += "<thead style='background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%); color: #64748b; font-weight: 700; font-size: 13px; text-transform: uppercase; letter-spacing: 0.05em;'>"
        diagnosis_html += "<tr>"
        diagnosis_html += "<th style='padding: 16px; border-bottom: 2px solid #e2e8f0;'>📅 触发时间</th>"
        diagnosis_html += "<th style='padding: 16px; border-bottom: 2px solid #e2e8f0;'>📍 来源终端 (IP)</th>"
        diagnosis_html += "<th style='padding: 16px; border-bottom: 2px solid #e2e8f0;'>✅ 诊断结果</th>"
        diagnosis_html += "<th style='padding: 16px; border-bottom: 2px solid #e2e8f0;'>📷 原始图像</th>"
        diagnosis_html += "</tr></thead><tbody style='color: #334155;'>"
        
        for diagnosis in diagnoses:
            time_str = diagnosis[4]
            ip = diagnosis[1]
            img = diagnosis[2]
            result = diagnosis[3]
            
            # 状态徽章渲染 - 生态绿 + 科技蓝配色
            if "健康" in result or "healthy" in str(result).lower():
                result_badge = f"<span style='background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%); color: #059669; padding: 6px 14px; border-radius: 999px; font-weight: 700; font-size: 12px; display: inline-flex; align-items: center; box-shadow: 0 2px 4px rgba(16, 185, 129, 0.2);'><span style='margin-right:6px'>🟢</span> {result}</span>"
            elif result and result.strip() != "":
                result_badge = f"<span style='background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%); color: #dc2626; padding: 6px 14px; border-radius: 999px; font-weight: 700; font-size: 12px; display: inline-flex; align-items: center; box-shadow: 0 2px 4px rgba(239, 68, 68, 0.2);'><span style='margin-right:6px'>🔴</span> {result}</span>"
            else:
                result_badge = f"<span style='background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%); color: #64748b; padding: 6px 14px; border-radius: 999px; font-weight: 700; font-size: 12px;'>未知</span>"

            img_badge = f"<span style='background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%); color: #475569; padding: 4px 10px; border-radius: 8px; font-size: 12px; font-family: monospace; border: 1px solid #e2e8f0;'>{img}</span>"

            diagnosis_html += f"<tr style='border-bottom: 1px solid #f1f5f9; transition: all 0.2s;' onmouseover='this.style.background=\"linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%)\"' onmouseout='this.style.background=\"transparent\"'>"
            diagnosis_html += f"<td style='padding: 16px; font-weight: 500;'>{time_str}</td>"
            diagnosis_html += f"<td style='padding: 16px; font-weight: 600;'>{ip}</td>"
            diagnosis_html += f"<td style='padding: 16px;'>{result_badge}</td>"
            diagnosis_html += f"<td style='padding: 16px;'>{img_badge}</td>"
            diagnosis_html += "</tr>"
            
        diagnosis_html += "</tbody></table></div>"
        return diagnosis_html
    
    def refresh_stats(self, days):
        """
        刷新统计数据
        """
        summary = self.get_summary_stats()
        token_chart = self.stats.generate_token_usage_chart(days)
        api_chart = self.stats.generate_api_call_chart(days)
        disease_chart = self.stats.generate_disease_distribution_chart(days)
        diagnosis_chart = self.stats.generate_daily_diagnosis_chart(days)
        
        return (
            summary['total_tokens'],
            summary['total_api_calls'],
            f"{summary['successful_calls']}/{summary['failed_calls']}",
            summary['total_diagnoses'],
            f"{summary['identified_diagnoses']}/{summary['unknown_diagnoses']}",
            summary['total_users'],
            token_chart,
            api_chart,
            disease_chart,
            diagnosis_chart
        )
    
    def refresh_logs(self):
        """
        刷新日志
        """
        self.logger.collect_logs()
        return self.get_recent_logs()
    
    def refresh_diagnoses(self):
        """
        刷新诊断记录
        """
        return self.get_recent_diagnoses()
    
    def create_interface(self):
        """
        创建 Gradio 界面 - 同步宽屏科技面板风格
        """
        custom_css = """
        /* =========================================================================
           1. 强制覆盖 Gradio 的深色模式变量，保证界面为纯净的亮色 SaaS 风格
           ========================================================================= */
        :root, body, .dark {
            --body-background-fill: #f0f4f8 !important;
            --background-fill-primary: #ffffff !important;
            --background-fill-secondary: #f8fafc !important;
            --border-color-primary: #e2e8f0 !important;
            --block-background-fill: #ffffff !important;
            --block-border-color: #e2e8f0 !important;
            --block-border-width: 1px !important;
            --block-radius: 16px !important;
            --body-text-color: #334155 !important;
            --body-text-color-subdued: #64748b !important;
            --block-label-text-color: #475569 !important;
            --block-title-text-color: #0f172a !important;
            --input-background-fill: #f8fafc !important;
        }
        
        body {
            background-color: #f0f4f8 !important;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif !important;
        }
        
        /* 【全屏展开配置】：保证 96% 的超宽屏展现 */
        .gradio-container {
            max-width: 96% !important;
            width: 100% !important;
            margin: 0 auto !important;
            padding-top: 30px !important;
            background-color: transparent !important;
            box-shadow: none !important;
            border: none !important;
        }
        
        footer { display: none !important; }
        
        /* 去除所有默认的难看边框，改为浅灰 */
        .gradio-container * {
            border-color: #e2e8f0 !important;
        }
        
        /* =========================================================================
           2. 顶部 Header 样式 (与主界面统一)
           ========================================================================= */
        .saas-header {
            background: linear-gradient(135deg, #ffffff 0%, #ecfdf5 100%);
            border-radius: 16px;
            padding: 35px 40px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.03);
            margin-bottom: 24px;
            border: 1px solid #d1fae5;
            position: relative;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }
        .saas-header::before {
            content: '';
            position: absolute;
            top: 0; left: 0; width: 6px; height: 100%;
            background: linear-gradient(to bottom, #10b981, #3b82f6);
        }
        .saas-title {
            font-size: 2.6rem;
            font-weight: 900;
            color: #064e3b;
            margin: 0 0 10px 0;
            letter-spacing: 1px;
            display: flex;
            align-items: center;
        }
        .saas-subtitle {
            color: #475569;
            font-size: 1.15rem;
            margin: 0;
            font-weight: 500;
        }
        .title-divider {
            font-size: 1.6rem;
            color: #94a3b8;
            font-weight: 400;
            margin-left: 12px;
            padding-left: 12px;
            border-left: 2px solid #cbd5e1;
        }

        /* =========================================================================
           3. 数据卡片 (核心监控指标) 
           ========================================================================= */
        .stat-card { 
            background: white !important; 
            border-radius: 16px !important; 
            padding: 24px !important; 
            box-shadow: 0 4px 15px rgba(0,0,0,0.03) !important; 
            border: 1px solid #e2e8f0 !important;
            transition: all 0.3s ease !important;
            height: 100%;
        }
        .stat-card:hover { 
            transform: translateY(-4px) !important; 
            box-shadow: 0 12px 20px -4px rgba(0,0,0,0.08) !important;
            border-color: #10b981 !important;
        }
        
        .stat-card label span { 
            color: #64748b !important; 
            font-size: 1.1rem !important; 
            font-weight: 800 !important; 
            letter-spacing: 0.05em; 
            margin-bottom: 12px !important; 
            display: block !important;
        }
        .stat-card input { 
            font-size: 2.4rem !important; 
            font-weight: 900 !important; 
            color: #0f172a !important; 
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            padding: 0 !important;
        }
        
        .status-text input { 
            font-size: 1.8rem !important; 
            color: #10b981 !important; 
            font-weight: 800 !important;
            background: #f0fdf4 !important;
            border-radius: 12px !important;
            padding: 12px !important;
            text-align: center !important;
            border: 1px solid #d1fae5 !important;
        }
        
        /* =========================================================================
           4. 图表容器 
           ========================================================================= */
        .chart-card {
            background: white !important; 
            border-radius: 16px !important; 
            padding: 24px !important; 
            box-shadow: 0 4px 15px rgba(0,0,0,0.03) !important; 
            border: 1px solid #e2e8f0 !important;
            margin-top: 10px !important;
        }
        .chart-card h2 { 
            margin-top: 0 !important; 
            font-size: 1.3rem !important; 
            color: #1e293b !important; 
            border-bottom: 2px solid #f1f5f9 !important; 
            padding-bottom: 16px !important; 
            margin-bottom: 20px !important;
            font-weight: 800 !important;
        }
        
        /* =========================================================================
           5. 按钮美化
           ========================================================================= */
        .primary-btn { 
            background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important; 
            color: white !important; 
            border: none !important; 
            border-radius: 12px !important; 
            font-weight: 700 !important;
            font-size: 1.15rem !important;
            padding: 14px !important;
            box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3) !important;
            transition: all 0.2s ease !important;
            margin-top: 8px !important;
            height: calc(100% - 8px) !important;
        }
        .primary-btn:hover { 
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 20px rgba(16, 185, 129, 0.4) !important;
        }
        
        .secondary-btn {
            background: #ffffff !important;
            border: 1px solid #cbd5e1 !important;
            color: #475569 !important;
            font-weight: 700 !important;
            border-radius: 12px !important;
            transition: all 0.2s !important;
            padding: 12px 24px !important;
        }
        .secondary-btn:hover { 
            background: #f1f5f9 !important; 
            color: #0f172a !important; 
            border-color: #94a3b8 !important;
        }
        
        /* =========================================================================
           6. 标签页及页面内部标题
           ========================================================================= */
        .tabs { border: none !important; background: transparent !important; }
        .tab-nav { border-bottom: 2px solid #e2e8f0 !important; margin-bottom: 24px !important; }
        .tab-nav button { 
            color: #64748b !important; 
            font-weight: 700 !important; 
            font-size: 1.15rem !important; 
            padding: 16px 32px !important; 
            border: none !important; 
            border-radius: 12px 12px 0 0 !important; 
            transition: all 0.2s ease !important;
        }
        .tab-nav button.selected { 
            color: #059669 !important; 
            border-bottom: 3px solid #10b981 !important; 
            background: white !important;
        }
        .tab-nav button:hover { background: #f8fafc !important; }

        .page-title {
            font-size: 1.6rem !important;
            font-weight: 900 !important;
            color: #0f172a !important;
            margin-bottom: 20px !important;
            border-left: 6px solid #10b981;
            padding-left: 12px;
            display: flex;
            align-items: center;
        }
        
        /* 表格容器 */
        .table-container {
            background: white !important;
            border-radius: 16px !important;
            padding: 24px !important;
            box-shadow: 0 4px 15px rgba(0,0,0,0.03) !important;
            border: 1px solid #e2e8f0 !important;
        }
        """
        
        with gr.Blocks(title="宇宙超级无敌祛病害大王 - 管理后台") as app:
            # 官方推荐的安全 CSS 注入方案
            gr.HTML(f"<style>{custom_css}</style>")
            
            # 【终极修复黑科技】：利用无效图片强行触发 onerror 事件注入脚本
            # 这个方案无视 Gradio 所有的虚拟 DOM 和事件加载拦截机制，确保脚本被强制加入真实的 document body 中。
            gr.HTML("""
            <img src="data:image/gif;base64,invalid" onerror='
                if(!window.maxkb_injected) {
                    window.maxkb_injected = true;
                    console.log("🚀 开始挂载 MaxKB 浮窗 (Bypass Gradio Shield)...");
                    var script = document.createElement("script");
                    script.src = "http://172.30.23.12:8080/chat/api/embed?protocol=http&host=172.30.23.12:8080&token=9f0fdf64c75b62c9";
                    script.async = true;
                    script.defer = true;
                    document.body.appendChild(script);
                }
            ' style="display:none;">
            """)
            
            # 自定义美化 Header
            gr.HTML("""
            <div class="saas-header">
                <h1 class="saas-title">
                    🌾 宇宙超级无敌祛病害大王 
                    <span class="title-divider">智能体数据调度中心</span>
                </h1>
                <p class="saas-subtitle">全息系统监控与多模态数据分析大屏</p>
            </div>
            """)
            
            # 仪表盘页面
            with gr.TabItem("📊 数据总览看板"):
                
                # 第一排：四个核心统计卡片
                with gr.Row():
                    with gr.Column(scale=1, elem_classes="stat-card"):
                        total_tokens = gr.Number(label="💻 本周消耗 Tokens", value=0, interactive=False)
                    with gr.Column(scale=1, elem_classes="stat-card"):
                        total_api_calls = gr.Number(label="⚡ API 调用总次数", value=0, interactive=False)
                    with gr.Column(scale=1, elem_classes="stat-card"):
                        total_diagnoses = gr.Number(label="🔍 历史诊断总数", value=0, interactive=False)
                    with gr.Column(scale=1, elem_classes="stat-card"):
                        total_users = gr.Number(label="👥 在线设备/用户", value=0, interactive=False)
                
                # 第二排：状态概览和控件
                gr.Markdown("<div style='height: 10px'></div>")
                with gr.Row():
                    with gr.Column(scale=2, elem_classes="stat-card status-text"):
                        api_status = gr.Textbox(label="🟢 API 状态 (成功 / 失败)", value="0/0", interactive=False)
                    with gr.Column(scale=2, elem_classes="stat-card status-text"):
                        diagnosis_status = gr.Textbox(label="🩺 检出状态 (已识别 / 未知)", value="0/0", interactive=False)
                    with gr.Column(scale=2, elem_classes="stat-card"):
                        days = gr.Slider(minimum=1, maximum=30, value=7, step=1, label="📅 统计追溯天数")
                    with gr.Column(scale=1):
                        refresh_btn = gr.Button("🔄 刷新全部数据", elem_classes="primary-btn")
                
                # 第三排：图表区域 1
                with gr.Row():
                    with gr.Column(scale=1, elem_classes="chart-card"):
                        gr.Markdown("<h2>📈 模型调用趋势 & Token 消耗</h2>")
                        token_chart = gr.HTML()
                    with gr.Column(scale=1, elem_classes="chart-card"):
                        gr.Markdown("<h2>⚡ API 并发统计</h2>")
                        api_chart = gr.HTML()
                
                # 第四排：图表区域 2
                with gr.Row():
                    with gr.Column(scale=1, elem_classes="chart-card"):
                        gr.Markdown("<h2>🦠 近期检出病害分布占比</h2>")
                        disease_chart = gr.HTML()
                    with gr.Column(scale=1, elem_classes="chart-card"):
                        gr.Markdown("<h2>📊 每日图传诊断频次</h2>")
                        diagnosis_chart = gr.HTML()
            
            # 诊断记录页面
            with gr.TabItem("🛰️ 实时监控 (大疆图传)"):
                with gr.Row():
                    gr.HTML("<div class='page-title'>📡 接收终端诊断监测列表</div>")
                    diagnosis_refresh_btn = gr.Button("🔄 刷新最新记录", elem_classes="secondary-btn")
                with gr.Column(elem_classes="table-container"):
                    diagnoses_output = gr.HTML()
            
            # 日志监控页面
            with gr.TabItem("⚙️ 模型与系统日志"):
                with gr.Row():
                    gr.HTML("<div class='page-title'>🖥️ 底层系统运行状态</div>")
                    log_refresh_btn = gr.Button("🔄 拉取最新日志", elem_classes="secondary-btn")
                with gr.Column(elem_classes="table-container"):
                    logs_output = gr.HTML()
            
            # 系统设置页面
            with gr.TabItem("🛠️ 高级设置"):
                with gr.Row():
                    with gr.Column(scale=1, elem_classes="chart-card"):
                        gr.Markdown("<h2>🔌 服务状态检测</h2>")
                        service_status = gr.Textbox(
                            label="当前引擎状态",
                            value="所有节点运行正常 (Dify, Qwen2-VL, Qwen2.5-3B)",
                            interactive=False
                        )
                    
                    with gr.Column(scale=1, elem_classes="chart-card"):
                        gr.Markdown("<h2>🚁 大疆 Cloud API 集成</h2>")
                        dji_api_status = gr.Textbox(
                            label="Webhook 监听口",
                            value="等待配置 (Pending)",
                            interactive=False
                        )
                
                with gr.Row():
                    with gr.Column(scale=1, elem_classes="chart-card"):
                        gr.Markdown("<h2>ℹ️ 系统基础信息</h2>")
                        system_info = gr.Textbox(
                            label="服务器当前时间",
                            value=f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (已同步 NTP)",
                            interactive=False
                        )
            
            # 事件绑定
            refresh_btn.click(
                fn=self.refresh_stats,
                inputs=[days],
                outputs=[
                    total_tokens, total_api_calls, api_status, total_diagnoses,
                    diagnosis_status, total_users, token_chart, api_chart,
                    disease_chart, diagnosis_chart
                ]
            )
            
            log_refresh_btn.click(
                fn=self.refresh_logs,
                outputs=[logs_output]
            )
            
            diagnosis_refresh_btn.click(
                fn=self.refresh_diagnoses,
                outputs=[diagnoses_output]
            )
            
            # 页面加载时自动刷新数据
            app.load(
                fn=self.refresh_stats,
                inputs=[days],
                outputs=[
                    total_tokens, total_api_calls, api_status, total_diagnoses,
                    diagnosis_status, total_users, token_chart, api_chart,
                    disease_chart, diagnosis_chart
                ]
            )
            app.load(fn=self.refresh_logs, outputs=[logs_output])
            app.load(fn=self.refresh_diagnoses, outputs=[diagnoses_output])
            
        return app

if __name__ == "__main__":
    dashboard = AdminDashboard()
    app = dashboard.create_interface()
    # 允许局域网访问，启动服务
    app.launch(
        server_name="0.0.0.0",
        server_port=7861,
        share=False,
        show_error=True
    )