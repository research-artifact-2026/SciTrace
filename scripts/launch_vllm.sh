#!/usr/bin/env bash
# Manuscript GPU setup: 2× RTX A5000, AWQ quantization, tensor-parallel size 2.
set -euo pipefail

MODEL_KEY="${1:-qwen25_72b}"
PORT="${PORT:-8000}"
TP="${TP:-2}"
QUANTIZATION="${QUANTIZATION:-awq}"
DTYPE="${DTYPE:-auto}"

case "$MODEL_KEY" in
  llama31_70b) MODEL_NAME="meta-llama/Llama-3.1-70B-Instruct" ;;
  qwen25_72b) MODEL_NAME="Qwen/Qwen2.5-72B-Instruct" ;;
  deepseekv3) MODEL_NAME="deepseek-ai/DeepSeek-V3" ;;
  *)
    echo "Unknown MODEL_KEY: $MODEL_KEY"
    echo "Valid: llama31_70b, qwen25_72b, deepseekv3"
    exit 1
    ;;
esac

echo "Launching vLLM: $MODEL_NAME on port $PORT (TP=$TP, quant=$QUANTIZATION)"

python -m vllm.entrypoints.openai.api_server \
  --model "$MODEL_NAME" \
  --port "$PORT" \
  --tensor-parallel-size "$TP" \
  --quantization "$QUANTIZATION" \
  --dtype "$DTYPE" \
  --host 0.0.0.0
