#!/bin/bash
# Check ComfyUI status: port, HTTP, queue, GPU, compile workers, recent outputs
# Usage: bash batch/comfyui_status.sh

PORT=8188
cd /home/derek/ComfyUI

# Port check
if ss -tlnp 2>/dev/null | grep -q ":${PORT}"; then
    echo "Port:     :${PORT} is bound"
else
    echo "Port:     :${PORT} NOT bound — ComfyUI not running"
    exit 1
fi

# HTTP check
stats=$(curl -s --max-time 2 http://localhost:${PORT}/system_stats 2>/dev/null)
if [ -z "$stats" ]; then
    echo "HTTP:     not responding (port bound but server frozen?)"
    exit 1
fi
echo "HTTP:     responding"

# Queue
queue=$(curl -s --max-time 2 http://localhost:${PORT}/queue 2>/dev/null)
if [ -n "$queue" ]; then
    running=$(echo "$queue" | python3 -c "import sys,json; q=json.load(sys.stdin); print(len(q.get('queue_running',[])))" 2>/dev/null)
    pending=$(echo "$queue" | python3 -c "import sys,json; q=json.load(sys.stdin); print(len(q.get('queue_pending',[])))" 2>/dev/null)
    echo "Queue:    ${running:-?} running, ${pending:-?} pending"
fi

# GPU utilization
gpu_use=$(rocm-smi --showuse 2>/dev/null | grep "GPU use" | awk '{print $NF}')
if [ -n "$gpu_use" ]; then
    echo "GPU:      ${gpu_use} busy"
else
    echo "GPU:      (rocm-smi unavailable)"
fi

# Compile workers (torch inductor — present during first-run kernel compilation)
workers=$(ps aux 2>/dev/null | grep "compile_worker" | grep -v grep | wc -l)
if [ "$workers" -gt 0 ]; then
    echo "Compile:  ${workers} torch inductor worker(s) active — model compiling, not sampling yet"
else
    echo "Compile:  no compile workers (sampling or idle)"
fi

# Recent outputs (any prefix)
recent=$(ls -t output/*.png output/*.jpg 2>/dev/null | head -5)
if [ -n "$recent" ]; then
    echo "Outputs:"
    echo "$recent" | while read f; do
        echo "  $(ls -lh "$f" 2>/dev/null | awk '{print $5, $6, $7, $8, $9}')"
    done
fi
