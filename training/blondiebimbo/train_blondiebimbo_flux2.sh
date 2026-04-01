#!/bin/bash
# Blondiebimbo LoRA training — Flux2 (Flex.2) via AI-Toolkit
# Optimizer: AdamW  |  LoRA dim=32  |  1500 steps, checkpoint every 250
#
# Usage:
#   bash train_blondiebimbo_flux2.sh

set -e

AI_TOOLKIT="/home/derek/Packages/ai-toolkit"
CONFIG="$AI_TOOLKIT/config/blondiebimbo_flux2.yaml"

# AMD ROCm — required for RX 7900 XTX (gfx1100)
export HSA_OVERRIDE_GFX_VERSION=11.0.0
export TORCH_ROCM_AOTRITON_ENABLE_EXPERIMENTAL=1
# Reduce memory fragmentation
export PYTORCH_HIP_ALLOC_CONF=expandable_segments:True

echo "=== Blondiebimbo Flux2 LoRA Training ==="
echo "  Config:   $CONFIG"
echo "  Output:   /home/derek/ComfyUI/models/loras/blondiebimbo/"
echo ""
echo "  NOTE: First run will cache text embeddings (slow, ~5-10 min)."
echo "  If you see Mistral tokenizer errors, run:"
echo "    $AI_TOOLKIT/venv/bin/python3 $AI_TOOLKIT/fix_mistral_tokenizer.py"
echo "  Then restart this script."
echo ""

source "$AI_TOOLKIT/venv/bin/activate"
cd "$AI_TOOLKIT"

python3 run.py "$CONFIG"

echo ""
echo "=== Done! ==="
echo "LoRA checkpoints: /home/derek/ComfyUI/models/loras/blondiebimbo/blondiebimbo_flux2_v1/"
echo "Trigger word: blondiebimbo"
echo "Use with: Flux2 workflows (image_flux2.json, bb_body_v2_t2i.json adapted for Flux2)"
