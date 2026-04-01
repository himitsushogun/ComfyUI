#!/bin/bash
# Poll until ComfyUI is ready at localhost:8188
# Usage: wait_comfyui.sh [max_attempts] [interval_seconds]
MAX=${1:-24}
INTERVAL=${2:-5}

for i in $(seq 1 "$MAX"); do
    if curl -s http://localhost:8188/system_stats > /dev/null 2>&1; then
        echo "ComfyUI ready after $((i * INTERVAL))s"
        exit 0
    fi
    echo "Waiting... $((i * INTERVAL))s"
    sleep "$INTERVAL"
done

echo "ComfyUI not ready after $((MAX * INTERVAL))s"
exit 1
