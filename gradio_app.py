#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import gradio as gr
import requests
import json
import base64
import os
from datetime import datetime
from backend.database import DatabaseManager

# API 配置
VISION_API_URL = "http://localhost:9400/v1/chat/completions"
TEXT_API_URL = "http://localhost:9401/v1/chat/completions"

# MaxKB 配置 - 支持内网地址和公网地址
MAXKB_URL = os.getenv("MAXKB_PUBLIC_URL", "http://172.30.23.12:8080")

# 初始化数据库管理器
db = DatabaseManager()

def call_vision_api(image_path):
    """
    调用视觉诊断 API
    """
    try:
        start_time = datetime.now()
        
        with open(image_path, "rb") as f:
            image_data = f.read()
        
        # 将图片转换为 base64
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {
                    "role": "system",
                    "content": "你是一位专业的植物病理学专家。请仔细分析用户上传的农作物病虫害图片，识别出具体的病害或虫害名称。\n\n要求：\n1. 只输出英文病害名称，例如：Tomato Early Blight、Powdery Mildew、Aphids\n2. 不要输出任何解释或额外文字\n3. 如果无法识别，输出 Unknown Disease\n4. 确保名称准确，使用标准的英文植物病理学术语"
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "请识别这张图片中的病虫害名称，只输出英文名称"},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}]
                }
            ],
            "temperature": 0.01,
            "max_tokens": 100
        }
        
        response = requests.post(VISION_API_URL, json=payload, timeout=60)
        result = response.json()
        
        end_time = datetime.now()
        response_time = (end_time - start_time).total_seconds()
        
        # 计算 Token 使用量（简化处理）
        input_tokens = len(image_base64) // 4 + len(payload["messages"][0]["content"]) // 4 + len(payload["messages"][1]["content"][0]["text"]) // 4
        output_tokens = 0
        
        if "choices" in result and len(result["choices"]) > 0:
            disease_name = result["choices"][0]["message"]["content"].strip()
            output_tokens = len(disease_name) // 4
            
            # 记录 API 调用
            user_id = 1
            db.record_api_call(
                user_id=user_id,
                api_type="vision",
                model_name="Qwen2-VL-7B",
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                response_time=response_time,
                status="success"
            )
            
            return disease_name, None
        else:
            # 记录 API 调用失败
            user_id = 1
            db.record_api_call(
                user_id=user_id,
                api_type="vision",
                model_name="Qwen2-VL-7B",
                input_tokens=input_tokens,
                output_tokens=0,
                response_time=response_time,
                status="error",
                error_message=str(result)
            )
            return None, f"API 返回错误: {result}"
    
    except Exception as e:
        # 记录 API 调用异常
        user_id = 1
        db.record_api_call(
            user_id=user_id,
            api_type="vision",
            model_name="Qwen2-VL-7B",
            input_tokens=0,
            output_tokens=0,
            response_time=0,
            status="error",
            error_message=str(e)
        )
        return None, f"调用视觉 API 失败: {str(e)}"

def call_text_api(disease_name):
    """
    调用中文农技顾问 API
    """
    try:
        start_time = datetime.now()
        
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {
                    "role": "system",
                    "content": "你是一位资深的农业技术推广专家，拥有 20 年以上的农作物病虫害防治经验。\n\n你的任务是：\n1. 将用户提供的英文病害名称翻译为准确的中文\n2. 提供详细的防治建议，包括：\n   - 病害特征描述\n   - 发病原因分析\n   - 预防措施\n   - 治疗方法（化学防治、生物防治、物理防治）\n   - 推荐药剂及使用方法\n   - 注意事项\n\n输出格式要求：\n使用清晰的标题和分段，方便农民阅读和理解。语言要通俗易懂，避免过于专业的术语。\n\n示例输出格式：\n---\n番茄早疫病\n\n【病害特征】\n...\n\n【发病原因】\n...\n\n【预防措施】\n...\n\n【防治方法】\n...\n\n【推荐药剂】\n...\n\n【注意事项】\n...\n---"
                },
                {
                    "role": "user",
                    "content": f"{disease_name}"
                }
            ],
            "temperature": 0.7,
            "max_tokens": 2000
        }
        
        response = requests.post(TEXT_API_URL, json=payload, timeout=120)
        result = response.json()
        
        end_time = datetime.now()
        response_time = (end_time - start_time).total_seconds()
        
        # 计算 Token 使用量
        input_tokens = len(payload["messages"][0]["content"]) // 4 + len(disease_name) // 4
        output_tokens = 0
        
        if "choices" in result and len(result["choices"]) > 0:
            advice = result["choices"][0]["message"]["content"].strip()
            output_tokens = len(advice) // 4
            
            # 记录 API 调用
            user_id = 1  
            db.record_api_call(
                user_id=user_id,
                api_type="text",
                model_name="Qwen2.5-3B-Instruct",
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                response_time=response_time,
                status="success"
            )
            
            return advice, None
        else:
            # 记录 API 调用失败
            user_id = 1
            db.record_api_call(
                user_id=user_id,
                api_type="text",
                model_name="Qwen2.5-3B-Instruct",
                input_tokens=input_tokens,
                output_tokens=0,
                response_time=response_time,
                status="error",
                error_message=str(result)
            )
            return None, f"API 返回错误: {result}"
    
    except Exception as e:
        # 记录 API 调用异常
        user_id = 1
        db.record_api_call(
            user_id=user_id,
            api_type="text",
            model_name="Qwen2.5-3B-Instruct",
            input_tokens=0,
            output_tokens=0,
            response_time=0,
            status="error",
            error_message=str(e)
        )
        return None, f"调用文本 API 失败: {str(e)}"

def diagnose_disease(image, request: gr.Request):
    """
    完整的诊断流程
    """
    if image is None:
        return None, "错误：请先上传图片", "", ""
    
    ip_address = request.client.host if request else "127.0.0.1"
    user_agent = request.headers.get("user-agent", "Unknown") if request else "Unknown"
    
    user_id = db.get_user_id(ip_address, user_agent)
    
    disease_name, error1 = call_vision_api(image)
    if error1:
        return None, f"视觉诊断失败: {error1}", "", ""
    
    advice, error2 = call_text_api(disease_name)
    if error2:
        return None, f"获取防治建议失败: {error2}", disease_name, ""
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = f"""# 农业病虫害诊断报告\n\n**诊断时间**: {timestamp}\n\n---\n\n## 英文病害名称\n{disease_name}\n\n---\n\n## 中文防治建议\n{advice}\n\n---\n\n*本报告由农业病虫害诊断智能体自动生成*"""
    
    db.record_diagnosis(
        user_id=user_id,
        image_path=image,
        disease_name=disease_name,
        diagnosis_result=report
    )
    
    return report, "诊断成功完成", disease_name, advice


def create_interface():
    """
    创建 Gradio 界面 - 科技蓝 + 生态绿主题，内嵌 MaxKB iframe
    """
    custom_css = """
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
    
    .gradio-container * {
        border-color: #e2e8f0 !important;
    }
    
    /* Header 区域 */
    .main-header {
        background: linear-gradient(135deg, #ffffff 0%, #ecfdf5 100%);
        border-radius: 16px;
        padding: 35px 20px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.03);
        margin-bottom: 24px;
        border: 1px solid #d1fae5;
        position: relative;
        overflow: hidden;
    }
    .main-header::before {
        content: '';
        position: absolute;
        top: 0; left: 0; width: 100%; height: 5px;
        background: linear-gradient(to right, #10b981, #3b82f6);
    }
    .header-title {
        font-weight: 900;
        font-size: 2.6rem;
        color: #064e3b;
        margin-bottom: 10px;
        letter-spacing: 1px;
    }
    .header-subtitle {
        color: #475569;
        font-size: 1.15rem;
        margin: 0;
        font-weight: 500;
    }
    
    /* 卡片式容器美化 */
    .panel-box {
        background: #ffffff !important;
        border-radius: 16px !important;
        padding: 24px !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04) !important;
        border: 1px solid #e2e8f0 !important;
        height: 100%;
    }
    .panel-title {
        font-size: 1.3rem;
        font-weight: 800;
        color: #0f172a;
        margin-bottom: 16px;
        padding-bottom: 12px;
        border-bottom: 2px solid #f1f5f9;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    /* 图片上传区域 */
    .image-upload-container {
        border: 2px dashed #6ee7b7 !important;
        border-radius: 12px !important;
        background-color: #f8fafc !important;
        overflow: hidden !important;
        transition: all 0.3s ease !important;
    }
    .image-upload-container:hover {
        background-color: #f0fdf4 !important;
        border-color: #10b981 !important;
    }
    
    /* 按钮美化 */
    .diagnose-btn {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: bold !important;
        font-size: 1.25rem !important;
        padding: 14px !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3) !important;
        width: 100% !important;
        margin-top: 10px !important;
    }
    .diagnose-btn:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(16, 185, 129, 0.4) !important;
    }
    
    .status-box textarea {
        background-color: #f8fafc !important;
        border: 1px solid #e2e8f0 !important;
        color: #64748b !important;
        text-align: center !important;
        font-weight: bold !important;
        border-radius: 8px !important;
    }

    .secondary-btn {
        background: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        color: #475569 !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        transition: all 0.2s !important;
    }
    .secondary-btn:hover { 
        background: #f1f5f9 !important; 
        color: #0f172a !important; 
    }
    
    .stop-btn {
        background: #ffffff !important;
        color: #ef4444 !important; 
        border: 1px solid #fca5a5 !important; 
        font-weight: 600 !important;
        border-radius: 8px !important;
        transition: all 0.2s !important;
    }
    .stop-btn:hover { 
        background: #fef2f2 !important; 
        color: #dc2626 !important; 
    }
    
    /* 标签页全局样式 */
    .tabs { border: none !important; background: transparent !important; }
    .tab-nav { border-bottom: 2px solid #e2e8f0 !important; margin-bottom: 0 !important; }
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
        background: white !important;
        border-bottom: 3px solid #10b981 !important;
    }
    .tab-nav button:hover {
        background: #f8fafc !important;
    }
    
    /* 专门为最外层主标签页增加一点下边距 */
    .main-tabs > .tab-nav {
        margin-bottom: 24px !important;
    }

    /* Chatbot 和 Markdown 结果展示 */
    .advice-box {
        background: #f8fafc !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 12px !important;
        padding: 20px !important;
        height: 520px !important;
        overflow-y: auto !important;
        font-size: 1.05rem !important;
        line-height: 1.7 !important;
        color: #1e293b !important;
    }
    
    .result-card textarea {
        font-size: 1.8rem !important;
        font-weight: 900 !important;
        color: #047857 !important;
        background-color: #ecfdf5 !important;
        text-align: center !important;
        border: 2px solid #a7f3d0 !important;
        border-radius: 12px !important;
        padding: 20px !important;
    }
    
    /* Footer 使用说明卡片 */
    .usage-card {
        background: #ffffff;
        border-radius: 12px;
        padding: 24px;
        border-left: 5px solid #3b82f6;
        box-shadow: 0 2px 10px rgba(0,0,0,0.02);
        margin-top: 24px;
        border: 1px solid #e2e8f0;
        border-left-width: 5px;
        color: #475569;
    }
    .usage-card h3 { margin-top: 0; color: #1e293b; font-weight: 800; font-size: 1.15rem;}
    .usage-card li { margin-bottom: 8px; line-height: 1.6;}
    """
    
    with gr.Blocks(title="宇宙超级无敌祛病害大王 - 农作物病虫害多模态智能诊断系统") as app:
        # 添加自定义 CSS
        gr.HTML(f"<style>{custom_css}</style>")
        
        # Header 区域
        gr.HTML("""
        <div class="main-header">
            <h1 class="header-title">🌾 宇宙超级无敌祛病害大王</h1>
            <p class="header-subtitle">农作物病虫害多模态智能诊断系统 —— 边缘计算与双引擎大模型强力驱动</p>
        </div>
        """)
        
        # 【核心架构改变：顶层增加两个大功能选项卡】
        with gr.Tabs(elem_classes="main-tabs"):
            
            # ================= 第一个主选项卡：智能图片诊断 =================
            with gr.TabItem("🔍 智能病害图片诊断"):
                
                # 主体工作区 - 左右分栏布局 (比例 4:6)
                with gr.Row():
                    # 左侧专区 - 图像输入区
                    with gr.Column(scale=4, elem_classes="panel-box"):
                        gr.HTML("<div class='panel-title'>📷 视觉感知输入</div>")
                        image_input = gr.Image(
                            label="请上传待诊断的农作物叶片图片",
                            type="filepath",
                            height=500,
                            elem_classes="image-upload-container"
                        )
                        diagnose_btn = gr.Button(
                            "🔍 开始智能诊断",
                            elem_classes="diagnose-btn"
                        )
                        status_output = gr.Textbox(
                            label="系统运行状态", 
                            value="系统就绪，等待上传图片...", 
                            interactive=False, 
                            elem_classes="status-box",
                            lines=1
                        )
                    
                    # 右侧专区 - 诊断与对话区
                    with gr.Column(scale=6, elem_classes="panel-box"):
                        gr.HTML("<div class='panel-title'>📊 智能体决策输出</div>")
                        
                        with gr.Tabs():
                            # 核心诊断结果标签页
                            with gr.TabItem("✅ 核心诊断结果"):
                                disease_output = gr.Textbox(
                                    label="视觉大模型 (Qwen2-VL) 检出病害",
                                    value="等待图像输入...",
                                    lines=1,
                                    interactive=False,
                                    elem_classes="result-card"
                                )
                                gr.Markdown("<div style='height: 16px'></div>")
                                advice_output = gr.Markdown(
                                    value="*等待生成农业专家防治报告...*",
                                    elem_classes="advice-box"
                                )
                            
                            # 完整报告标签页
                            with gr.TabItem("📋 完整诊断报告"):
                                report_output = gr.Markdown(
                                    label="诊断报告",
                                    value="*请上传图片并点击左侧的“开始智能诊断”按钮...*"
                                )
                
                # 底部按钮区
                gr.Markdown("<div style='height: 10px'></div>")
                with gr.Row():
                    download_btn = gr.Button(
                        "📥 一键下载诊断报告",
                        elem_classes="secondary-btn"
                    )
                    clear_btn = gr.Button(
                        "🗑️ 清空面板数据",
                        elem_classes="stop-btn"
                    )
                
                # 底部说明区 (更新了引导文案)
                gr.HTML("""
                <div class="usage-card">
                    <h3>📌 使用说明与注意事项</h3>
                    <ul style="padding-left: 20px;">
                        <li><strong>清晰度优先</strong>：请上传清晰的病虫害图片，建议分辨率不低于 <code>800x600</code>，并确保病害特征明显可见。</li>
                        <li><strong>多角度尝试</strong>：如果一次识别不够准确，建议尝试更换拍摄角度或在更好的光照条件下重新拍摄。</li>
                        <li><strong>处理时效</strong>：本系统在本地 P40 集群上采用双模型级联推理，单次诊断响应时间通常在 30-60 秒之间，请耐心等待。</li>
                    </ul>
                </div>
                """)
                
                gr.HTML("""
                <div class="usage-card" style="border-left-color: #10b981; text-align: center;">
                    <h3 style="color: #10b981;">💬 AI 农技在线答疑中心</h3>
                    <p style="color: #64748b; margin-bottom: 0; font-size: 1.1rem;">对诊断结果有疑问？或者想了解更多农药配比知识，<strong>请点击顶部的【💬 AI 农技专家问答】标签页直接与我对话！</strong></p>
                </div>
                """)

            # ================= 第二个主选项卡：MaxKB 全屏内嵌 =================
            with gr.TabItem("💬 AI 农技专家问答 (MaxKB)"):
                
                # 采用 iframe 无缝满屏嵌入 MaxKB，使用相对路径配合 Caddy 反向代理
                gr.HTML("""
                <div style="height: 850px; width: 100%; border-radius: 16px; overflow: hidden; border: 1px solid #e2e8f0; box-shadow: 0 4px 20px rgba(0,0,0,0.04); background: white;">
                    <iframe
                        src="/chat/9f0fdf64c75b62c9"
                        style="width: 100%; height: 100%; border: none;"
                        frameborder="0"
                        allow="microphone">
                    </iframe>
                </div>
                """)
        
        # --- 事件绑定 ---
        diagnose_btn.click(
            fn=diagnose_disease,
            inputs=[image_input],
            outputs=[report_output, status_output, disease_output, advice_output]
        )
        
        download_btn.click(
            fn=lambda report: report,
            inputs=[report_output],
            outputs=None
        )
        
        clear_btn.click(
            fn=lambda: (None, "系统就绪，等待上传图片...", "等待图像输入...", "*等待生成农业专家防治报告...*", "*文档将在诊断完成后自动生成...*"),
            outputs=[image_input, status_output, disease_output, advice_output, report_output]
        )
    
    return app

if __name__ == "__main__":
    app = create_interface()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )