#!/usr/bin/env bash
# ==============================================================================
# Setup & Launch Script for AMD Instinct MI300X (DigitalOcean Droplet)
# Launches official ROCm vLLM container with Qwen 2.5 72B Instruct
# ==============================================================================
set -euo pipefail

echo "=========================================================="
echo " Starting MI300X vLLM Setup & Model Deployment"
echo "=========================================================="

# 1. Verify ROCm GPU Driver & Hardware
echo "[1/4] Checking AMD GPU Hardware..."
if ! command -v rocm-smi &> /dev/null; then
    echo "[-] Error: rocm-smi not found. Ensure this is an AMD ROCm GPU droplet."
    exit 1
fi

rocm-smi --showproductname
rocm-smi --showmeminfo vram

# 2. Check Docker availability
echo "[2/4] Verifying Docker environment..."
if ! command -v docker &> /dev/null; then
    echo "[*] Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
fi

# Ensure /dev/kfd and /dev/dri permissions
sudo usermod -aG video,render "$USER" || true

# 3. Pull and Run vLLM ROCm Container
CONTAINER_NAME="vllm-mi300x"
MODEL_NAME="Qwen/Qwen2.5-72B-Instruct"
HF_CACHE_DIR="${HOME}/.cache/huggingface"
mkdir -p "$HF_CACHE_DIR"

echo "[3/4] Starting vLLM container (${CONTAINER_NAME}) with model: ${MODEL_NAME}..."

# Remove existing container if present
docker rm -f "$CONTAINER_NAME" 2>/dev/null || true

# Launch with ROCm devices mapped
docker run -d \
    --name "$CONTAINER_NAME" \
    --restart unless-stopped \
    --network host \
    --ipc host \
    --device=/dev/kfd \
    --device=/dev/dri \
    --group-add video \
    --cap-add=SYS_PTRACE \
    --security-opt seccomp=unconfined \
    -v "${HF_CACHE_DIR}:/root/.cache/huggingface" \
    rocm/vllm:latest \
    vllm serve "$MODEL_NAME" \
        --host 0.0.0.0 \
        --port 8000 \
        --tensor-parallel-size 1 \
        --gpu-memory-utilization 0.92 \
        --max-model-len 8192 \
        --max-num-batched-tokens 16384 \
        --enforce-eager \
        --disable-log-requests

echo "[+] vLLM container initiated in background."

# 4. Health Check Loop
echo "[4/4] Polling vLLM server endpoint (http://localhost:8000/v1/models)..."
MAX_ATTEMPTS=60
SLEEP_SECS=10
ATTEMPT=1

while [ $ATTEMPT -le $MAX_ATTEMPTS ]; do
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/v1/models || echo "000")
    if [ "$HTTP_CODE" -eq 200 ]; then
        echo ""
        echo "=========================================================="
        echo " [+] SUCCESS: vLLM is online and serving Qwen 2.5 72B!"
        echo " [+] Endpoint: http://localhost:8000/v1"
        echo "=========================================================="
        exit 0
    fi
    echo -n "."
    sleep $SLEEP_SECS
    ATTEMPT=$((ATTEMPT + 1))
done

echo ""
echo "[-] Timeout waiting for vLLM to initialize. Check logs with: docker logs -f ${CONTAINER_NAME}"
exit 1
