# 🌾 农业病虫害诊断智能体

<div align="center">
<img src="https://img.shields.io/badge/PyTorch-2.2.0-red.svg" alt="PyTorch">
<img src="https://img.shields.io/badge/Transformers-5.2.0-blue.svg" alt="Transformers">
<img src="https://img.shields.io/badge/Gradio-4.41.0-orange.svg" alt="Gradio">
<img src="https://img.shields.io/badge/FastAPI-0.104.1-green.svg" alt="FastAPI">
<img src="https://img.shields.io/badge/CUDA-12.1-yellow.svg" alt="CUDA">
</div>

<br>

<div align="center">
<strong>基于多模态大模型的农作物病虫害诊断智能体</strong><br>
支持图片识别、自动诊断和专业防治建议，提供端到端的病虫害诊断解决方案

南京农业大学信息管理学院
</div>

## 功能特性

- **视觉诊断**: 上传病虫害图片，AI 自动识别病害类型并给出防治建议
- **农技问答**: 智能对话系统，解答农药配比、种植技术等问题
- **知识库检索**: 集成 MaxKB 知识库，提供专业的农业知识支持
- **管理后台**: 数据统计、日志查看、系统监控

## 技术栈

- **视觉模型**: Qwen2-VL-7B (微调版)
- **文本模型**: Qwen2.5-3B-Instruct (微调版)
- **训练框架**: LLaMA-Factory
- **前端界面**: Gradio
- **反向代理**: Caddy
- **内网穿透**: cpolar

## 项目结构

```
病虫害识别/
├── gradio_app.py              # Gradio 主界面
├── start_all_services.sh      # 一键启动脚本
├── Caddyfile                  # Caddy 反向代理配置
├── requirements.txt           # Python 依赖
├── backend/
│   ├── admin_dashboard.py     # 管理后台
│   ├── database.py            # 数据库管理
│   ├── logger.py              # 日志记录
│   └── stats.py               # 统计分析
├── models/                    # 模型文件 (需自行下载)
└── output/                    # 训练输出 (可邮箱联系获取15390459400@163.com)
```

## 快速开始

### 1. 环境准备

```bash
# 创建虚拟环境
conda create -n pest_diagnosis python=3.10
conda activate pest_diagnosis

# 安装依赖
pip install -r requirements.txt
```

### 2. 模型准备

将训练好的模型放置到以下目录：
- 视觉模型: `models/qwen2-vl-7b/`
- 文本模型: `output/llamafactory-qwenvl-crop-disease/`

### 3. 启动服务

```bash
# 启动所有服务（本地访问）
./start_all_services.sh --all

# 启动所有服务 + 内网穿透（公网访问）
./start_all_services.sh --all --tunnel

# 停止所有服务
./start_all_services.sh --stop

# 查看服务状态
./start_all_services.sh --status
```

### 4. 访问地址

启动成功后可通过以下地址访问：

| 服务 | 地址 |
|------|------|
| Gradio 界面 | http://localhost:7860 |
| 统一入口 (Caddy) | http://localhost:8888 |
| 管理后台 | http://localhost:7861 |
| 视觉 API 文档 | http://localhost:9400/docs |
| 文本 API 文档 | http://localhost:9401/docs |

使用 `--tunnel` 参数启动后，还会显示公网访问地址。

## API 接口

### 视觉诊断 API

```bash
POST http://localhost:9400/v1/chat/completions
Content-Type: application/json

{
  "model": "qwen2-vl-7b",
  "messages": [
    {
      "role": "user",
      "content": [
        {"type": "text", "text": "这是什么病害？"},
        {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}}
      ]
    }
  ]
}
```

### 文本问答 API

```bash
POST http://localhost:9401/v1/chat/completions
Content-Type: application/json

{
  "model": "qwen2.5-3b",
  "messages": [
    {"role": "user", "content": "如何防治水稻稻瘟病？"}
  ]
}
```

## 配置说明

### Caddy 反向代理

Caddy 配置文件 `Caddyfile` 实现了以下路由：
- `/chat/*` → MaxKB 知识库服务
- `/api/*` → MaxKB API 接口
- `/ui/*` → MaxKB 管理界面
- `/*` → Gradio 主界面

### 内网穿透

使用 cpolar 实现内网穿透，只需穿透 Caddy 的 8888 端口即可同时暴露所有服务。

## 依赖说明

- CUDA 11.8+
- Python 3.10+
- PyTorch 2.0+
- Transformers 4.37+
- Gradio 4.0+

## 许可证

本项目仅供学习和研究使用。

## 联系方式

如有问题，请提交 Issue 或联系项目维护者。
