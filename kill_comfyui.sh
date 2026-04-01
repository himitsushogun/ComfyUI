#!/bin/bash

# Kill ComfyUI (and optionally clear Triton cache)
# Usage:
#   ./kill_comfyui.sh            — stop ComfyUI, preserve all caches
#   ./kill_comfyui.sh --clear-cache  — stop + clear Triton cache (NaN/black output fix)

CLEAR_CACHE=0
if [[ "$1" == "--clear-cache" ]]; then
    CLEAR_CACHE=1
fi

echo "Stopping ComfyUI..."
pkill -f "python.*main.py" 2>/dev/null
sleep 2

if [[ $CLEAR_CACHE -eq 1 ]]; then
    echo "Clearing Triton cache..."
    rm -rf ~/.triton/cache/
    echo "Done (cache cleared). Run start_comfyui.sh to restart."
else
    echo "Done (cache preserved). Run start_comfyui.sh to restart."
    echo "Tip: use --clear-cache to fix black/NaN output issues."
fi
