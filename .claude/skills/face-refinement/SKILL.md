---
name: face-refinement
description: Targeted facial feature editing (lip shape, eye shape, etc.) on an existing generated image while fully preserving identity. Use when the user wants to refine a specific facial feature without changing anything else. Trigger on requests like "fix the lips", "adjust the eyes", "refine facial features", "change lip shape".
---

# Face Refinement via Masked Inpainting

Targeted editing of specific facial features (lips, eyes, etc.) on an existing image. Only the masked region is touched — identity is fully preserved outside the mask.

---

## How It Works

1. Auto-generate a precise mask for the target feature using face parsing
2. Crop the face region, run BiSeNet to get a per-feature mask, project back to full image
3. Use InpaintCropImproved to create a 1024px context crop around the mask
4. Inpaint with SDXL at low denoise — NO Fooocus patch (see below)
5. Stitch back with InpaintStitchImproved for a seamless composite

This is fundamentally different from Flux2 image edit (which uses ReferenceLatent to anchor the whole composition) — inpainting leaves everything outside the mask completely unchanged.

---

## Installed Nodes

| Node | Package | Purpose |
|------|---------|---------|
| `BBoxDetectorLoader(FaceParsing)` | `comfyui_face_parsing` | YOLO face detection (required — face too small in full-body for BiSeNet directly) |
| `FaceParsing` | `comfyui_face_parsing` | BiSeNet per-feature segmentation mask |
| `InpaintCropImproved` / `InpaintStitchImproved` | `ComfyUI-Inpaint-CropAndStitch` | Crop around mask with context, stitch back with blend |
| `GrowMaskWithBlur` | KJNodes | Combined mask expand + blur |
| `INPAINT_LoadFooocusInpaint` | `comfyui-inpaint-nodes` (Acly) | Installed but NOT used — causes grey blob at denoise ≤0.6 |
| `FaceDetailer` | `comfyui-impact-pack` | Optional blend/cleanup pass over full face |

**Preferred mask source**: `comfyui_face_parsing` — exposes lips, upper lip, lower lip separately (BiSeNet model).

---

## Model

Use `RealVisXL_V4.0.safetensors` (already installed, SDXL checkpoint).
Do NOT use Flux2 for inpainting — Flux Kontext degrades identity and Flux2 ReferenceLatent absorbs fine changes.
Do NOT use Flux Kontext for any human face work.

---

## Confirmed Working Pipeline (`batch/face_inpaint_lips.json`)

```
LoadImage (full image)
  → BBoxDetectorLoader + BBoxDetect (face_yolov8m.pt) → BBoxListItemSelect
  → ImageCropWithBBox → ImageScale (512x512)
  → FaceParsingModelLoader + FaceParsingProcessorLoader → FaceParse
  → FaceParsingResultsParser (mouth=true, u_lip=true, l_lip=true)
  → GrowMaskWithBlur (expand=4, blur_radius=0)
  → MaskInsertWithBBox (projects mask back to full image coords)
  → InpaintCropImproved (context_from_mask_extend_factor=5.0, mask_blend_pixels=20, output 1024x1024)
  → VAEEncodeForInpaint (grow_mask_by=6)
  → KSampler (model direct from CheckpointLoaderSimple — NO Fooocus patch)
  → VAEDecode → InpaintStitchImproved → SaveImage
```

**Submit with**: `python3 batch/batch_comfy.py batch/face_inpaint_lips.json <runs.csv> --node 11 --wait`
- Node 11 = positive CLIPTextEncode; `--node 11` flag required because there are two text nodes
- Prompt goes in the CSV file (not the JSON) when using `--node 11`

---

## Key Parameters

| Parameter | Value | Notes |
|-----------|-------|-------|
| Denoise | 0.6 | Working sweet spot — reshapes without artifacts. Higher (0.78+) causes nose doubling and tearing |
| Mask expand | 4px | At 512px face scale |
| Mask blur | 0 | Keep at 0 at face scale — blur applied here gets magnified through the scale chain |
| context_from_mask_extend_factor | 5.0 | Critical — gives model enough face context around the lip mask. Lower values cause grey blob or mask coverage of entire face area in the crop |
| mask_blend_pixels | 20 | InpaintCropImproved edge blend |
| CFG | 7 | Higher CFG (10) makes color drift worse, not better |

---

## Why No Fooocus Patch

`VAEEncodeForInpaint` fills the masked region with grey before encoding. The Fooocus patch conditions the model on that grey fill to understand the inpaint region. But at denoise ≤0.6, the sampler doesn't run enough steps to overcome the grey signal → grey blob output.

**Fix**: bypass Fooocus entirely. Connect KSampler's `model` input directly to `CheckpointLoaderSimple` output slot 0 (not through `INPAINT_ApplyFooocusInpaint`). At denoise=0.6, the sampler reshapes the existing latent without needing inpaint conditioning.

The `INPAINT_LoadFooocusInpaint` and `INPAINT_ApplyFooocusInpaint` nodes remain in the JSON but are disconnected from the KSampler.

---

## Scale Chain — The Blur Magnification Problem

The mask is generated at 512px face crop scale, then projected back to full image coords via `MaskInsertWithBBox`, then `InpaintCropImproved` creates a 1024px context crop. Any blur applied at the 512px face level gets magnified ~2x when projected back. With small context (factor=1.5), a 6px blur at 512px was enough to cover the entire lower face in the 1024px crop.

**Rule**: Apply zero blur at the face-scale mask. The `mask_blend_pixels=20` in InpaintCropImproved handles edge softening at the correct scale.

---

## Prompt Structure

Describe only the target feature. Shape changes are subtle — the model resists large geometric reshaping:

- `"full pouty lips, rounded cupid's bow, soft natural pout, slightly fuller upper lip, natural skin tone"` → subtle pout improvement (confirmed working, 00011)
- `"duck lips pout, pursed protruding lips, rounded forward pout"` → slight additional duck shape (confirmed working, 00013)

Keep it narrow — the mask handles context preservation, not the prompt.

---

## What Works and What Doesn't

| Goal | Result |
|------|--------|
| Subtle lip shape shift (pout, cupid's bow) | Works — seamless, noticeable improvement |
| Dramatic lip reshaping (major size/shape change) | Resists — model anchors to original geometry |
| Lip color change (red lipstick) | Unreliable — drifts to dark/gothic tones, skin around lips darkens. Higher CFG makes it worse (went teal at CFG=10) |
| Iterative stacking (pass on already-inpainted image) | Artifacts — lip position drifts, visible tearing |
| Eye symmetry correction (geometric) | Does NOT work via inpainting — model cannot reshape eye geometry at safe denoise levels |
| Eye color correction | Unreliable — Juggernaut defaults to blue eyes for blonde archetype; negative prompt partially helps |

**For color changes**: use post-process hue shift instead — take the lip mask from the inpaint pipeline and apply a HSV/color transform in Python/PIL. Deterministic and pixel-accurate.

---

## Eye Refinement — Lessons Learned (2026-03-20)

Eye geometry correction is fundamentally harder than lip shape correction. The inpainting pipeline hits two failure modes:

- **Denoise ≥ 0.6**: enough steps to clear grey fill, but model drifts heavily — wrong eye color (blue), wrong size/shape ("SDXL-standard" eyes that don't fit the face)
- **Denoise ≤ 0.3**: not enough steps to overcome `VAEEncodeForInpaint` grey fill → grey bleed-through in output

**Mask scope**: Use `r_eye + l_eye` only. Adding `r_brow + l_brow + eye_g` makes the mask too large and gives the model too much geometry to regenerate.

**Juggernaut XL Inpainting XI behavior**: Strong bias toward generating blue eyes for blonde characters, even with `"dark brown eyes"` in the positive prompt and blue eyes in the negative prompt.

**Recommended model**: `juggernautXLInpainting_xiInpainting.safetensors` (in `models/checkpoints/`) is the correct choice for face inpainting — better than RealVisXL V4 for face coherence in general, but still insufficient for geometric eye reshaping.

**Better strategy for eye asymmetry**: Use a high-quality face crop image and stitch it into the portrait rather than inpainting. Inpainting is a texture/color tool at safe denoise levels — geometric reshaping requires a different approach.

---

## What Doesn't Work for Fine Facial Edits

| Tool | Why it fails |
|------|-------------|
| Flux2 `image_flux2.json` | ReferenceLatent absorbs fine feature changes — confirmed |
| Flux Kontext | Degrades human identity even on subtle edits — confirmed |
| Flux2 text-to-image | Loses identity entirely (no anchor) |
| Denoise > 0.6 | Artifacts: nose doubling, face darkening, tearing — confirmed at 0.78 |
| CFG > 7 for color | Makes color drift worse, not better — confirmed at CFG=10 |
| Stacked inpaint passes | Lip position drift + visible tearing on second pass |
| Fooocus patch at denoise ≤0.6 | Grey blob — sampler can't overcome grey fill at low denoise |

---

## Status (as of 2026-03-20)

- Batch workflow: `batch/face_inpaint_lips.json` — confirmed working
- Best shape result: `output/FaceRefine__00011_.png` (subtle pout improvement, seamless blend)
- Duck lips variant: `output/FaceRefine__00013_.png` (slight further duck shape from original base)
- Color changes: logged as unsolved — try post-process hue shift as next approach
- Input base: `input/portrait_for_refinement.png` (copy of `output/Flux2_00022_.png`)

---

## StableMakeup Transfer — Confirmed Working (2026-03-20)

Diffusion-based makeup transfer via `ComfyUI_Stable_Makeup` (SIGGRAPH 2025). Transfers full makeup look (eyeshadow, lips, etc.) from a reference photo onto a target face.

### Workflow
- File: `batch/stable_makeup_transfer.json`
- Submit: `python3 batch/batch_comfy.py batch/stable_makeup_transfer.json /tmp/stable_makeup_run.txt --wait`
- Node 1: target face (id_image) — must be in `input/`
- Node 2: makeup reference (makeup_image) — `input/face_reference.png`

### Confirmed Parameters
| Parameter | Value | Notes |
|-----------|-------|-------|
| cfg | 1.6 | Sweet spot — plateaus quickly above this, oversaturated at 5+ |
| steps | 30 | Default, working |
| facedetector | resnet | Better than mobilenet |
| dataname | wflw | 98 landmarks — better alignment than 300wpublic (68 pts) |
| width/height | 512×512 | Node max — full-body images need crop/stitch workaround |

### Key Lessons
- **Clean the target first**: removing heavy existing makeup (smoky eye, dark liner) before transfer dramatically improves result quality. Heavy dark base makeup competes with the transferred colors.
- **Use Flux2 image edit to clean**: `image_flux2.json` with prompt "natural eyes, clean eyelids, no eyeshadow, soft natural lashes" worked at default guidance (4).
- **wflw > 300wpublic**: 98 landmarks produce better edge alignment, less makeup bleed at boundaries.
- **CFG ceiling**: model plateaus around 2.5, oversaturates at 5+. 1.6 is optimal.
- **Remaining issue**: inner-corner eye bleed — reference shimmer/glitter transfers literally into sclera area. Pending fix.

### Diffusers 0.36 / Transformers 5.x Compatibility Patches Applied
- `stable_makeup_nodes.py`: added `transformers.CLIPFeatureExtractor = transformers.CLIPImageProcessor` shim at top
- `pipeline_sd15.py`: swapped import order to use `diffusers.models.controlnets.multicontrolnet.MultiControlNetModel` first (old path raises ValueError at 0.36+)
- `models/stable_makeup/spiga_wflw.pt`: downloaded from `https://huggingface.co/aprados/spiga/resolve/main/spiga_wflw.pt`

### Best Results
- `output/StableMakeup_00008_.png` — clean headshot (`Flux2_00025_.png`) + `face_reference.png` makeup, wflw, cfg=1.6
