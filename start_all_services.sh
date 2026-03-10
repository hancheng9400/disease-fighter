#!/bin/bash
# 农业病虫害诊断智能体 - 统一启动脚本
# 功能：启动所有服务或指定服务，智能分配GPU

# 项目路径
PROJECT_DIR="/home/ugrad/Luzhonghao/病虫害识别"
LOG_DIR="/home/ugrad/Luzhonghao/log/Agent"
LLAMA_FACTORY_DIR="/home/ugrad/Luzhonghao/病虫害识别/LLaMA-Factory"
CPOLAR_EXEC="/home/ugrad/tools/cpolar"
CADDY_EXEC="$HOME/tools/caddy/caddy"

# 创建必要的目录
mkdir -p "$LOG_DIR"
mkdir -p /tmp

# GPU分配锁文件
GPU_LOCK_FILE="/tmp/gpu_allocation.lock"

# 服务配置
declare -A SERVICES
SERVICES[vision]="视觉诊断 API|9400|Qwen2-VL-7B|16"
SERVICES[text]="中文农技顾问 API|9401|Qwen2.5-3B-Instruct|8"
SERVICES[gradio]="Gradio 网页界面|7860|无|0"
SERVICES[admin]="管理后台|7861|无|0"

# 公网访问地址（由 cpolar 设置）
PUBLIC_URL=""
MAXKB_PUBLIC_URL=""

# 显示帮助信息
show_help() {
    echo "农业病虫害诊断智能体 - 统一启动脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  --all              启动所有服务（默认）"
    echo "  --vision           只启动视觉诊断 API"
    echo "  --text             只启动中文农技顾问 API"
    echo "  --gradio           只启动 Gradio 网页界面"
    echo "  --admin            只启动管理后台"
    echo "  --tunnel           启动内网穿透（cpolar）"
    echo "  --stop             停止所有服务"
    echo "  --status           查看服务状态"
    echo "  --help             显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 --all           # 启动所有服务"
    echo "  $0 --all --tunnel  # 启动所有服务并开启内网穿透"
    echo "  $0 --vision        # 只启动视觉诊断 API"
    echo "  $0 --stop          # 停止所有服务"
}

# 初始化GPU分配系统
init_gpu_allocation() {
    # 清空GPU分配锁文件
    > "$GPU_LOCK_FILE"
    
    # 获取所有GPU信息
    nvidia-smi --query-gpu=index,name,memory.total,memory.free --format=csv,noheader,nounits > /tmp/gpu_info.txt
    
    echo "检测到以下 GPU:"
    while IFS=',' read -r gpu_id gpu_name gpu_total gpu_free; do
        echo "  GPU $gpu_id: $gpu_name (总显存: ${gpu_total}MB, 空闲: ${gpu_free}MB)"
    done < /tmp/gpu_info.txt
    echo ""
}

# 获取可用GPU（考虑显存需求和已分配情况）
get_available_gpu() {
    local required_memory=$1
    local service_name=$2
    
    # 读取已分配的GPU
    declare -A allocated_gpus
    if [ -f "$GPU_LOCK_FILE" ]; then
        while IFS=':' read -r gpu_id service; do
            allocated_gpus[$gpu_id]=$service
        done < "$GPU_LOCK_FILE"
    fi
    
    # 查找满足显存需求且未分配的GPU
    local best_gpu=-1
    local max_free_memory=0
    
    while IFS=',' read -r gpu_id gpu_name gpu_total gpu_free; do
        # 检查GPU是否已分配
        if [ -n "${allocated_gpus[$gpu_id]}" ]; then
            echo "  跳过 GPU $gpu_id（已分配给 ${allocated_gpus[$gpu_id]}）"
            continue
        fi
        
        # 检查显存是否满足需求
        if [ "$gpu_free" -ge "$required_memory" ]; then
            if [ "$gpu_free" -gt "$max_free_memory" ]; then
                max_free_memory=$gpu_free
                best_gpu=$gpu_id
            fi
        fi
    done < /tmp/gpu_info.txt
    
    if [ "$best_gpu" -eq -1 ]; then
        echo "错误：没有足够的显存满足 $service_name 的需求（需要 ${required_memory}MB）"
        return 1
    fi
    
    # 记录GPU分配
    echo "$best_gpu:$service_name" >> "$GPU_LOCK_FILE"
    echo "$best_gpu"
    return 0
}

# 启动视觉诊断API
start_vision_api() {
    local required_memory=${SERVICES[vision]##*|}
    local gpu_id=$(get_available_gpu "$required_memory" "视觉诊断API")
    
    if [ $? -ne 0 ]; then
        return 1
    fi
    
    echo "启动视觉诊断 API 服务..."
    echo "使用 GPU: $gpu_id"
    
    export CUDA_VISIBLE_DEVICES=$gpu_id
    export PYTHONPATH="$LLAMA_FACTORY_DIR/src:$PYTHONPATH"
    export API_PORT=9400
    
    cd "$LLAMA_FACTORY_DIR"
    
    local config_file="/tmp/vision_api_config.yaml"
    cat > "$config_file" << EOF
model_name_or_path: /home/ugrad/Luzhonghao/病虫害识别/models/qwen2-vl-7b
adapter_name_or_path: /home/ugrad/Luzhonghao/病虫害识别/output/llamafactory-qwenvl-crop-disease
template: qwen2_vl
infer_backend: huggingface
trust_remote_code: true
EOF
    
    local python_path="$LLAMA_FACTORY_DIR/llama_factory_env/bin/python"
    CUDA_VISIBLE_DEVICES=$gpu_id $python_path -m llamafactory.cli api "$config_file" > "$LOG_DIR/vision_api.log" 2>&1 &
    
    echo "✅ 视觉诊断 API 启动成功 (端口 9400, GPU $gpu_id)"
    return 0
}

# 启动中文农技顾问API
start_text_api() {
    local required_memory=${SERVICES[text]##*|}
    local gpu_id=$(get_available_gpu "$required_memory" "中文农技顾问API")
    
    if [ $? -ne 0 ]; then
        return 1
    fi
    
    echo "启动中文农技顾问 API 服务..."
    echo "使用 GPU: $gpu_id"
    
    export CUDA_VISIBLE_DEVICES=$gpu_id
    export PYTHONPATH="$LLAMA_FACTORY_DIR/src:$PYTHONPATH"
    export API_PORT=9401
    
    cd "$LLAMA_FACTORY_DIR"
    
    local config_file="/tmp/text_api_config.yaml"
    cat > "$config_file" << EOF
model_name_or_path: /home/ugrad/HuggingFace/Qwen2.5-3B-Instruct
adapter_name_or_path: /home/ugrad/Luzhonghao/病虫害识别/LLaMA-Factory/output/disease_train/Qwen2.5-3B-Instruct
template: qwen
infer_backend: huggingface
trust_remote_code: true
EOF
    
    local python_path="$LLAMA_FACTORY_DIR/llama_factory_env/bin/python"
    CUDA_VISIBLE_DEVICES=$gpu_id $python_path -m llamafactory.cli api "$config_file" > "$LOG_DIR/text_api.log" 2>&1 &
    
    echo "✅ 中文农技顾问 API 启动成功 (端口 9401, GPU $gpu_id)"
    return 0
}

# 启动Gradio界面
start_gradio() {
    echo "启动 Gradio 网页界面..."
    
    source /opt/anaconda3/etc/profile.d/conda.sh
    conda activate lzh_vllm
    
    cd "$PROJECT_DIR"
    python gradio_app.py > "$LOG_DIR/gradio_app.log" 2>&1 &
    
    echo "✅ Gradio 网页界面启动成功 (端口 7860)"
    return 0
}

# 启动管理后台
start_admin() {
    echo "启动管理后台..."
    
    source /opt/anaconda3/etc/profile.d/conda.sh
    conda activate lzh_vllm
    
    cd "$PROJECT_DIR"
    python backend/admin_dashboard.py > "$LOG_DIR/admin_dashboard.log" 2>&1 &
    
    echo "✅ 管理后台启动成功 (端口 7861)"
    return 0
}

# 启动 Caddy 反向代理
start_caddy() {
    echo ""
    echo "启动 Caddy 反向代理服务..."
    
    # 检查 Caddyfile 是否存在
    if [ ! -f "$PROJECT_DIR/Caddyfile" ]; then
        echo "❌ Caddyfile 不存在"
        return 1
    fi
    
    # 停止之前的 Caddy 服务
    pkill -f "caddy run" > /dev/null 2>&1
    sleep 1
    
    # 检查 Caddy 是否已安装
    if [ ! -f "$CADDY_EXEC" ]; then
        echo "下载 Caddy..."
        mkdir -p "$HOME/tools/caddy"
        cd "$HOME/tools/caddy"
        curl -L "https://github.com/caddyserver/caddy/releases/download/v2.7.6/caddy_2.7.6_linux_amd64.tar.gz" -o caddy.tar.gz
        if [ $? -ne 0 ]; then
            echo "❌ Caddy 下载失败"
            return 1
        fi
        tar -xzf caddy.tar.gz caddy
        chmod +x caddy
        rm caddy.tar.gz
        echo "✅ Caddy 安装完成"
    fi
    
    # 启动 Caddy
    "$CADDY_EXEC" run --config "$PROJECT_DIR/Caddyfile" --adapter caddyfile > "$LOG_DIR/caddy.log" 2>&1 &
    CADDY_PID=$!
    
    sleep 3
    
    # 检查 Caddy 是否成功启动
    if ps -p $CADDY_PID > /dev/null; then
        echo "✅ Caddy 启动成功 (端口 8888)"
        echo ""
        echo "路由规则："
        echo "  - /chat/* -> MaxKB (172.30.23.12:8080)"
        echo "  - /api/*  -> MaxKB (172.30.23.12:8080)"
        echo "  - /ui/*   -> MaxKB (172.30.23.12:8080)"
        echo "  - /*      -> Gradio (127.0.0.1:7860)"
        return 0
    else
        echo "❌ Caddy 启动失败"
        return 1
    fi
}

# 启动 cpolar 内网穿透
start_cpolar_tunnel() {
    echo ""
    echo "启动 cpolar 内网穿透服务..."
    
    # 检查 cpolar 是否存在
    if [ ! -f "$CPOLAR_EXEC" ]; then
        echo "❌ cpolar 不存在: $CPOLAR_EXEC"
        echo "请先下载并安装 cpolar"
        return 1
    fi
    
    # 停止之前的 cpolar 服务
    pkill -f "cpolar http" > /dev/null 2>&1
    sleep 2
    
    # 启动 cpolar 穿透 Caddy 的 8888 端口
    echo "启动 cpolar 隧道（端口 8888 -> 公网）..."
    "$CPOLAR_EXEC" http 8888 --log=stdout --log-level=info > "$LOG_DIR/cpolar.log" 2>&1 &
    CPOLAR_PID=$!
    
    # 等待隧道建立
    echo "等待 cpolar 建立隧道..."
    sleep 10
    
    # 检查 cpolar 是否成功启动
    if ps -p $CPOLAR_PID > /dev/null; then
        echo "✅ cpolar 服务启动成功"
        
        # 尝试获取公网地址
        sleep 3
        PUBLIC_URL=$(grep -a 'Tunnel established at http' "$LOG_DIR/cpolar.log" | grep -oP 'http://[^"]+' | tail -1)
        
        if [ -n "$PUBLIC_URL" ]; then
            echo ""
            echo "🌐 公网访问地址: $PUBLIC_URL"
            echo ""
            echo "📋 使用说明："
            echo "  1. 通过公网地址访问 Gradio 界面"
            echo "  2. 点击'AI 农技专家问答'标签页即可使用 MaxKB"
            echo "  3. 所有服务都通过 Caddy 反向代理统一暴露"
        else
            echo "⏳ 公网地址获取中..."
            echo "   请稍后访问 http://localhost:4040 查看公网地址"
        fi
        
        return 0
    else
        echo "❌ cpolar 服务启动失败"
        echo "请检查 cpolar 配置和 token 是否正确"
        return 1
    fi
}

# 停止所有服务
stop_all_services() {
    echo "停止所有服务..."
    
    # 终止各个服务
    for service in vision text gradio admin; do
        local pattern="${service}_api"
        if [ "$service" = "gradio" ]; then
            pattern="gradio_app.py"
        elif [ "$service" = "admin" ]; then
            pattern="admin_dashboard.py"
        fi
        
        pids=$(ps aux | grep "$pattern" | grep -v grep | awk '{print $2}')
        if [ -n "$pids" ]; then
            for pid in $pids; do
                kill $pid 2>/dev/null
                echo "  终止 $pattern (PID: $pid)"
            done
        fi
    done
    
    # 停止 Caddy 服务
    pkill -f "caddy run" > /dev/null 2>&1
    echo "  终止 Caddy 服务"
    
    # 停止 cpolar 服务
    pkill -f "cpolar http" > /dev/null 2>&1
    echo "  终止 cpolar 服务"
    
    # 清空GPU分配锁文件
    > "$GPU_LOCK_FILE"
    
    echo "✅ 所有服务已停止"
}

# 查看服务状态
show_status() {
    echo "服务状态："
    echo ""
    
    local ports="9400 9401 7860 7861"
    for port in $ports; do
        if ss -tlnp 2>/dev/null | grep -q ":$port"; then
            echo "  端口 $port: ✅ 运行中"
        else
            echo "  端口 $port: ❌ 未运行"
        fi
    done
    
    echo ""
    
    # 显示GPU分配情况
    if [ -f "$GPU_LOCK_FILE" ]; then
        echo "GPU 分配情况："
        while IFS=':' read -r gpu_id service; do
            echo "  GPU $gpu_id: $service"
        done < "$GPU_LOCK_FILE"
    fi
}

# 等待服务启动
wait_for_service() {
    local port=$1
    local service_name=$2
    local max_wait=60
    local wait_time=0
    
    echo "等待 $service_name 启动..."
    
    while [ $wait_time -lt $max_wait ]; do
        if ss -tlnp 2>/dev/null | grep -q ":$port"; then
            echo "✅ $service_name 启动成功"
            return 0
        fi
        sleep 2
        wait_time=$((wait_time + 2))
    done
    
    echo "❌ $service_name 启动超时"
    return 1
}

# 主函数
main() {
    # 解析命令行参数
    local start_all=false
    local start_vision=false
    local start_text=false
    local start_gradio=false
    local start_admin=false
    local start_tunnel=false
    local stop_services=false
    local show_status=false
    
    while [ $# -gt 0 ]; do
        case "$1" in
            --all)
                start_all=true
                shift
                ;;
            --vision)
                start_vision=true
                shift
                ;;
            --text)
                start_text=true
                shift
                ;;
            --gradio)
                start_gradio=true
                shift
                ;;
            --admin)
                start_admin=true
                shift
                ;;
            --tunnel)
                start_tunnel=true
                shift
                ;;
            --stop)
                stop_services=true
                shift
                ;;
            --status)
                show_status=true
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                echo "未知选项: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # 如果没有指定任何选项，默认启动所有服务
    if [ "$start_all" = false ] && [ "$start_vision" = false ] && [ "$start_text" = false ] && [ "$start_gradio" = false ] && [ "$start_admin" = false ] && [ "$start_tunnel" = false ] && [ "$stop_services" = false ] && [ "$show_status" = false ]; then
        start_all=true
    fi
    
    # 执行相应操作
    if [ "$stop_services" = true ]; then
        stop_all_services
    elif [ "$show_status" = true ]; then
        show_status
    else
        # 初始化GPU分配系统
        init_gpu_allocation
        
        echo "========================================"
        echo "农业病虫害诊断智能体 - 启动服务"
        echo "========================================"
        echo ""
        
        # 启动指定的服务
        if [ "$start_all" = true ] || [ "$start_vision" = true ]; then
            start_vision_api
            sleep 2
        fi
        
        if [ "$start_all" = true ] || [ "$start_text" = true ]; then
            start_text_api
            sleep 2
        fi
        
        if [ "$start_all" = true ] || [ "$start_gradio" = true ]; then
            start_gradio
            sleep 2
        fi
        
        if [ "$start_all" = true ] || [ "$start_admin" = true ]; then
            start_admin
            sleep 2
        fi
        
        # 启动 Caddy 反向代理（在 Gradio 启动之后）
        if [ "$start_all" = true ] || [ "$start_gradio" = true ]; then
            start_caddy
        fi
        
        # 启动 cpolar 内网穿透（如果需要）
        if [ "$start_tunnel" = true ]; then
            start_cpolar_tunnel
        fi
        
        echo ""
        echo "========================================"
        echo "服务启动完成"
        echo "========================================"
        echo ""
        echo "访问地址："
        echo "  - Gradio 界面: http://localhost:7860"
        echo "  - 统一入口: http://localhost:8888 (Caddy 反向代理)"
        echo "  - 管理后台: http://localhost:7861"
        echo "  - 视觉API文档: http://localhost:9400/docs"
        echo "  - 文本API文档: http://localhost:9401/docs"
        echo ""
        
        # Caddy 反向代理信息
        if [ "$start_all" = true ] || [ "$start_gradio" = true ]; then
            echo ""
            echo "Caddy 路由规则："
            echo "  - /chat/* -> MaxKB (172.30.23.12:8080)"
            echo "  - /api/*  -> MaxKB (172.30.23.12:8080)"
            echo "  - /ui/*   -> MaxKB (172.30.23.12:8080)"
            echo "  - /*      -> Gradio (127.0.0.1:7860)"
        fi
        
        # 内网穿透信息
        if [ "$start_tunnel" = true ] && [ -n "$PUBLIC_URL" ]; then
            echo ""
            echo "🌐 公网访问地址: $PUBLIC_URL"
        fi
        
        echo ""
        echo "日志目录: $LOG_DIR"
        echo ""
        echo "使用 '$0 --status' 查看服务状态"
        echo "使用 '$0 --stop' 停止所有服务"
        echo "========================================"
    fi
}

# 执行主函数
main "$@"
