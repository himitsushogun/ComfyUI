# ComfyUI – Session Memory

## Disabled Skills (this project)
- **Do NOT invoke `superpowers:using-superpowers`** — adds unnecessary overhead for image generation work
- **Do NOT invoke `superpowers:brainstorming`** — not appropriate for image gen sessions; use directly

## System
- **GPU**: AMD Radeon RX 7900 XTX — 24GB VRAM (ROCm)
- **Platform**: Linux
- **ComfyUI path**: `/home/derek/ComfyUI`

## General Preferences
- Prefer quantized/GGUF models to stay within 24GB VRAM
- City96 (Hugging Face) is a trusted source for GGUF-quantized diffusion models and text encoders
- Mix of GGUF diffusion models + fp8 safetensors text encoders is acceptable

## Installed Custom Nodes (notable)
- `ComfyUI-GGUF` — provides `UnetLoaderGGUF` and `UnetLoaderGGUFAdvanced` nodes
- `ComfyUI-GGUF-FantasyTalking`

## Model Inventory

### diffusion_models
| File | Size | Notes |
|------|------|-------|
| `flux1-dev-fp8.safetensors` | 17GB | Flux1, large |
| `flux1-dev-kontext_fp8_scaled.safetensors` | 12GB | Flux1 Kontext |
| `flux1-dev-Q4_K_S.gguf` | 6.4GB | Flux1 GGUF, fits in VRAM |
| `flux2_dev_fp8mixed.safetensors` | 34GB | Flux2, too large for VRAM alone |
| `flux2-dev-Q4_K_M.gguf` | 5.3GB | Flux2 GGUF, preferred for VRAM |
| `qwen_image_edit_fp8_e4m3fn.safetensors` | 20GB | Qwen image edit |
| `wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors` | 14GB | Wan2.2 I2V |
| `wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors` | 14GB | Wan2.2 I2V |

### text_encoders
| File | Size | Notes |
|------|------|-------|
| `mistral_3_small_flux2_bf16.safetensors` | 34GB | Flux2 encoder, too large |
| `mistral_3_small_flux2_fp8.safetensors` | 5.3GB | Flux2 encoder, preferred |
| `qwen_2.5_vl_7b_fp8_scaled.safetensors` | 8.8GB | Qwen VL encoder |
| `t5xxl_fp8_e4m3fn_scaled.safetensors` | 4.9GB | T5XXL for Flux1 |
| `umt5_xxl_fp8_e4m3fn_scaled.safetensors` | 6.3GB | UMT5 for Wan |

### vae
| File | Notes |
|------|-------|
| `ae.safetensors` | Flux1 VAE |
| `flux2-vae.safetensors` | Flux2 VAE |
| `qwen_image_vae.safetensors` | Qwen VAE |
| `wan_2.1_vae.safetensors` | Wan VAE |

### checkpoints
- `RealVisXL_V4.0.safetensors`
- `flux/` (directory)

## Workflows (`user/default/workflows/`)
| File | Description |
|------|-------------|
| `image_flux2.json` | Flux2 image edit — updated to use GGUF + fp8 (see below) |
| `flux_lora_workflow.json` | Flux1 with LoRA |
| `flux_kontext_dev_basic.json` | Flux1 Kontext |
| `image_qwen_image_edit.json` | Qwen image editing |
| `image_qwen_image_edit_pose.json` | Qwen image edit with pose |
| `qwen_controlnet_pose.json` | Qwen + ControlNet pose |
| `qwen_multiangle_workflow.json` | Qwen multi-angle |
| `qwen_standalone_simple.json` | Qwen simple |
| `video_wan2_2_14B_flf2v.json` | Wan2.2 video (first/last frame) |
| `character_scene_workflow.json` | Character scene |
| `instantid_workflow.json` | InstantID |
| `liveportrait_expressions.json` | LivePortrait |
| `pulid_test.json` | PuLID test |

## Living Skills Protocol

After every image generation round, immediately update the relevant model skill file if any of the following occurred:
- A new prompting pattern worked (or failed)
- A model behavior was observed (anchoring, element loss, resistance to repositioning, etc.)
- A recovery strategy was found
- A guidance or parameter value produced notably better/worse results

Skill files by workflow:
- **Flux Kontext** → `.claude/skills/kontext-prompt/SKILL.md`
- **Flux2 edit/t2i** → `.claude/skills/comfy-prompt/SKILL.md` (Flux2 section)
- **Qwen** → `.claude/skills/comfy-prompt/SKILL.md` (Qwen section)

If a workflow doesn't have a dedicated skill section yet, add one. Skills are the primary memory for model behavior — keep them current.

## Workflow Changes Made

### `image_flux2.json` (2025-02-23)
Both subgraphs (`Image Edit (Flux.2 Dev)` and `Image Edit (Flux.2 Dev 8steps)`) were updated:
- `UNETLoader` → `UnetLoaderGGUF` with `flux2-dev-Q4_K_M.gguf`
- `CLIPLoader` → `mistral_3_small_flux2_fp8.safetensors` (was bf16)
- Reason: original models (34GB each) exceeded 24GB VRAM; GGUF+fp8 combo is ~11GB total
