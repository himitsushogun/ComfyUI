#!/bin/bash
# Blondiebimbo LoRA training script
# Base model: Flux1 DEV fp8  |  Optimizer: AdamW
# LoRA: dim=64, alpha=32  |  Target: ~1500 steps, checkpoint every 250
#
# Usage:
#   ./train_blondiebimbo.sh                    # standard run (~1500 steps)
#   STEPS=2000 ./train_blondiebimbo.sh         # more steps if identity still weak
#   DIM=64 ./train_blondiebimbo.sh             # stronger identity (if dim=32 weak)
#   DIM=64 STEPS=2000 ./train_blondiebimbo.sh  # both

set -e

STEPS="${STEPS:-1500}"
DIM="${DIM:-64}"
ALPHA="${ALPHA:-32}"
LR="${LR:-1e-4}"

SD_SCRIPTS="/home/derek/sd-scripts"
COMFY="/home/derek/ComfyUI"
TRAINING_DIR="$COMFY/training/blondiebimbo"
OUTPUT_DIR="$COMFY/models/loras/blondiebimbo"
CACHE_DIR="$TRAINING_DIR/cache"
LOG_DIR="$TRAINING_DIR/logs"

mkdir -p "$OUTPUT_DIR" "$CACHE_DIR" "$LOG_DIR"

# AMD ROCm — required for RX 7900 XTX (gfx1100)
export HSA_OVERRIDE_GFX_VERSION=11.0.0
# Enable experimental Flash Attention (aotriton) for gfx1100 — required for --sdpa
export TORCH_ROCM_AOTRITON_ENABLE_EXPERIMENTAL=1

# Write sample prompts file (regenerated each run)
cat > "$TRAINING_DIR/sample_prompts.txt" << 'EOF'
blondiebimbo, close-up portrait, white background, studio lighting, photorealistic
blondiebimbo, full body front view, woman wearing white blouse, black pencil mini skirt, white background, studio lighting, photorealistic
blondiebimbo, happy smiling expression, close-up portrait, white background, photorealistic
blondiebimbo, woman wearing pink latex bodysuit, white background, photorealistic
EOF

echo "=== Blondiebimbo LoRA Training ==="
echo "  Steps:     $STEPS  (watch samples at 500/750/1000 — stop before overfit)"
echo "  Dim/Alpha: $DIM / $ALPHA  (bump DIM to 64 if identity is weak)"
echo "  LR:        $LR"
echo "  Output:    $OUTPUT_DIR"
echo ""

source "$SD_SCRIPTS/venv/bin/activate"
cd "$SD_SCRIPTS"

# ---------------------------------------------------------------------------
# Step 1: Cache latents + text embeddings to disk
# Loads VAE + T5XXL once, encodes all images and captions, then frees VRAM.
# Subsequent runs skip this quickly if cache already exists.
# ---------------------------------------------------------------------------
echo "--- Caching latents and text embeddings (runs once) ---"
accelerate launch flux_train_network.py \
  --pretrained_model_name_or_path "$COMFY/models/diffusion_models/flux1-dev-fp8.safetensors" \
  --clip_l "$COMFY/models/clip/clip_l.safetensors" \
  --t5xxl "$COMFY/models/text_encoders/t5xxl_fp8_e4m3fn_scaled.safetensors" \
  --ae "$COMFY/models/vae/ae.safetensors" \
  --dataset_config "$TRAINING_DIR/dataset.toml" \
  --output_dir "$OUTPUT_DIR" \
  --output_name "blondiebimbo_dim${DIM}" \
  --cache_latents_to_disk \
  --cache_text_encoder_outputs \
  --cache_text_encoder_outputs_to_disk \
  --fp8_base \
  --network_module networks.lora_flux \
  --network_dim "$DIM" \
  --network_alpha "$ALPHA" \
  --max_train_steps 1 \
  --learning_rate "$LR" \
  --mixed_precision bf16 \
  --save_precision bf16 \
  --sdpa \
  --gradient_checkpointing \
  --seed 42

# ---------------------------------------------------------------------------
# Step 2: Train
# VAE + T5XXL off VRAM (disk cache). Flux1 fp8 (~17GB) + LoRA + activations
# fits comfortably in 24GB. blocks_to_swap=0 — increase to 8 or 16 if OOM.
# ---------------------------------------------------------------------------
echo ""
echo "--- Training ($STEPS steps, sampling every 250) ---"
accelerate launch flux_train_network.py \
  --pretrained_model_name_or_path "$COMFY/models/diffusion_models/flux1-dev-fp8.safetensors" \
  --clip_l "$COMFY/models/clip/clip_l.safetensors" \
  --t5xxl "$COMFY/models/text_encoders/t5xxl_fp8_e4m3fn_scaled.safetensors" \
  --ae "$COMFY/models/vae/ae.safetensors" \
  --dataset_config "$TRAINING_DIR/dataset.toml" \
  --output_dir "$OUTPUT_DIR" \
  --output_name "blondiebimbo_dim${DIM}" \
  --cache_latents_to_disk \
  --cache_text_encoder_outputs \
  --cache_text_encoder_outputs_to_disk \
  --fp8_base \
  --fp8_base_unet \
  --blocks_to_swap 16 \
  --offload_optimizer_device cpu \
  --network_module networks.lora_flux \
  --network_dim "$DIM" \
  --network_alpha "$ALPHA" \
  --network_train_unet_only \
  --optimizer_type AdamW \
  --learning_rate "$LR" \
  --lr_scheduler constant_with_warmup \
  --lr_warmup_steps 100 \
  --max_train_steps "$STEPS" \
  --save_every_n_steps 250 \
  --save_last_n_steps_state 2 \
  --mixed_precision bf16 \
  --save_precision bf16 \
  --sdpa \
  --gradient_checkpointing \
  --timestep_sampling flux_shift \
  --discrete_flow_shift 3.1582 \
  --model_prediction_type raw \
  --guidance_scale 1.0 \
  --loss_type l2 \
  --model_type flux \
  --apply_t5_attn_mask \
  --seed 42 \
  --sample_prompts "$TRAINING_DIR/sample_prompts.txt" \
  --sample_every_n_steps 250 \
  --sample_sampler euler \
  --sample_at_first \
  --metadata_trigger_phrase "blondiebimbo" \
  --log_with tensorboard \
  --logging_dir "$LOG_DIR"

echo ""
echo "=== Done! ==="
echo "LoRA checkpoints:  $OUTPUT_DIR/blondiebimbo_dim${DIM}-*.safetensors"
echo "Tensorboard:       tensorboard --logdir $LOG_DIR"
echo ""
echo "Load in ComfyUI:  LoraLoaderModelOnly → blondiebimbo_dim${DIM} + Flux1 workflow"
echo "Trigger word:     blondiebimbo"
echo ""
echo "Evaluation tips:"
echo "  - Compare step 500 vs 1000 vs 1500 samples — stop before face looks 'cooked'"
echo "  - If identity weak at 1500: re-run with DIM=64 or STEPS=2000"
echo "  - LoRA also loads in Flux2 workflows (same transformer architecture)"
