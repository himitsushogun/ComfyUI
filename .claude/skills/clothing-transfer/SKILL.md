---
name: clothing-transfer
description: Workflow selection and setup guide for transferring an outfit from a reference image onto a person, preserving identity. Covers all available methods ranked by identity preservation quality.
type: reference
---

# Clothing Transfer — Workflow Guide

Use this skill when the task is: **put the outfit from image A onto the person in image B**.

---

## Method Comparison

| Method | Identity | Outfit Accuracy | Speed | Notes |
|--------|----------|-----------------|-------|-------|
| **CatVTON** | ★★★★★ | ★★★★☆ | Medium | Inpainting-based — only the clothing region is regenerated. Best identity preservation. |
| **IDM-VTON** | ★★★★★ | ★★★★★ | Slow | Best fabric/texture fidelity. Needs ROCm compat testing. |
| **Kontext two-image** | ★★★☆☆ | ★★★★☆ | Medium | Full scene regeneration — identity drifts toward model's preferred body type |
| **Qwen two-image** | ★★☆☆☆ | ★★★☆☆ | Medium | Treats reference as style, not target — outfit transfer is inconsistent |
| **Flux2 image edit** | ★★★★☆ | ★★☆☆☆ | Fast | Describe outfit in prompt only — good identity, poor outfit accuracy without reference |

**Key insight**: CatVTON/IDM-VTON use inpainting masks — they replace only the clothing region and never touch the face or background. Flux/Qwen/Kontext regenerate the full scene, which is why identity drifts.

---

## CatVTON (Recommended)

**Status**: Installed 2026-03-15. Models need to be downloaded (see below).

**Node**: `CatVTONWrapper`
**Custom node**: `custom_nodes/ComfyUI_CatVTON_Wrapper` (chflame163)
**Original paper**: ICLR 2025 — https://github.com/Zheng-Chong/CatVTON

### Required Models

Download from Google Drive and place in `models/CatVTON/`:
https://drive.google.com/drive/folders/1TJNNql7UfDPVgHJuItDDjowycN5jpC5o

### Required Dependency Node: LayerMask: HumanPartsUltra

The example workflow uses `LayerMask: HumanPartsUltra` from **ComfyUI_LayerStyle** for automatic clothing segmentation (generates the inpainting mask).
- Install via Manager: search "ComfyUI_LayerStyle"
- **AMD caveat**: the node defaults to `cuda` device — may need to change to `cpu` on ROCm

**Alternative**: Draw a mask manually in the ComfyUI UI using the mask editor (right-click LoadImage → "Open in MaskEditor"). Slower but avoids the LayerStyle dependency.

### Workflow Structure

```
LoadImage (person) ──────────────────────────────► CatVTONWrapper.image
       │                                                    ▲
       └──► LayerMask: HumanPartsUltra (clothing mask) ──► CatVTONWrapper.mask
                                                            ▲
LoadImage (outfit reference) ───────────────────────────► CatVTONWrapper.refer_image
                                                            │
                                                            ▼
                                                       SaveImage
```

### Node Parameters (CatVTONWrapper)

| Param | Default | Notes |
|-------|---------|-------|
| `mask_grow` | 25 | Expand mask boundary — increase if outfit edge artifacts |
| `mixed_precision` | fp16 | fp16 works on ROCm; use bf16 if NaN errors |
| `steps` | 50 | Default 50; 30 is fast enough for testing |
| `cfg` | 3 | Low CFG — don't increase much |

### Batch API Workflow

TODO: Export API-format workflow once confirmed working in UI. Save to `batch/catvton_outfit.json`.
Will require: 2 image inputs (person, outfit ref) + mask source.

---

## IDM-VTON (Not yet installed)

**Status**: Not installed. Needs testing for ROCm compatibility.

**Install**:
```bash
cd custom_nodes
git clone https://github.com/TemryL/ComfyUI-IDM-VTON.git
cd ComfyUI-IDM-VTON
python3 install.py
# If huggingface-hub error:
pip install huggingface-hub==0.25.2
```

Models (~5–6 GB) download from `yisol/IDM-VTON` on HuggingFace on first run.

**Known issue**: bundles CUDA extensions — goes through HIP translation on ROCm. Test before relying on it.

---

## CatV2TON / Flux-based VTON (Future)

**Status**: Not installed. Requires `FLUX.1-Fill-dev` model (not the same as `flux1-dev`).

**Node**: `lujiazho/ComfyUI-CatvtonFluxWrapper`
**Extra model needed**: `black-forest-labs/FLUX.1-Fill-dev` (~17 GB fp16, or GGUF quantized)

Hold until Fill model is acquired.

---

## Existing Workflows (non-VTON)

These live in `batch/` and use full-scene regeneration. Use when VTON isn't available or for quick tests:

| Workflow | Command |
|----------|---------|
| `batch/kontext_outfit_transfer.json` | 2 images (ref left, person right) + prompt. Guidance 4.0 for best identity. See kontext-prompt skill. |
| `batch/image_flux2.json` | 1 image (person) + prompt describing outfit. Fast, good identity, poor outfit accuracy. |
| `batch/qwen_standalone_simple.json` | 2 images + prompt. Inconsistent outfit transfer. |

---

## Startup Time Notes (2026-03-15)

ComfyUI startup on this machine:
- Initial HTTP ready: ~60 seconds after `bash start_comfyui.sh`
- **Recommended wait pattern**: 60s initial sleep, then 5s polling loop
- First Kontext run after Triton cache clear: adds ~3–5 min for kernel recompile
- Inference time per image (Kontext, 20 steps): ~2.5 min
