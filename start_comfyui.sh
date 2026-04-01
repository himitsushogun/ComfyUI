#!/bin/bash

# ComfyUI Startup Script - AMD RX 7900 XTX (ROCm)
# ------------------------------------------------

# AMD/ROCm memory and performance settings
# Note: expandable_segments:True can cause segfaults on gfx1100/rocm6.2 after
# large VRAM free/alloc cycles (e.g. unloading 20GB GGUF then loading small VAE).
# Using max_split_size_mb instead to reduce fragmentation without the instability.
export PYTORCH_HIP_ALLOC_CONF=garbage_collection_threshold:0.8,max_split_size_mb:512
export HSA_OVERRIDE_GFX_VERSION=11.0.0
export HIP_VISIBLE_DEVICES=0
# Disable system DMA — prevents ROCm runtime crashes on cleanup on some gfx1100 setups
export HSA_ENABLE_SDMA=0

# 7900 XTX performance fixes (validated by community on gfx1100/RX 7900 XTX)
# Source: github.com/Comfy-Org/ComfyUI/issues/10460
# VAE decode: ~10x faster, ~10x less VRAM usage
export MIOPEN_FIND_MODE=2
export FLASH_ATTENTION_TRITON_AMD_ENABLE="FALSE"
export FLASH_ATTENTION_TRITON_AMD_AUTOTUNE="FALSE"
export TORCH_ROCM_AOTRITON_ENABLE_EXPERIMENTAL=1

# Fix: "HIP error: no kernel image is available" during Wan VAE decode
# PyTorch 2.7+rocm6.2 on gfx1100 has no compiled HIP kernels for
# F.interpolate upsample ops (nearest, nearest-exact). The VAE files
# (vae.py, vae2_2.py) are patched to use repeat_interleave instead,
# which bypasses the missing native kernels entirely.
# Source: github.com/ROCm/ROCm/issues/4729

cd ~/ComfyUI
source venv/bin/activate

echo "Starting ComfyUI..."
echo "GPU info:"
rocm-smi --showproductname 2>/dev/null | grep -v "^=" | grep -v "^$" | head -3
echo ""

python main.py \
    --reserve-vram 2.5 \
    --lowvram \
    --disable-assets-autoscan \
    --port 8188
