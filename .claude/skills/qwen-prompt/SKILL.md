---
name: qwen-prompt
description: Write or revise prompts for Qwen-based ComfyUI workflows (qwen_standalone_simple.json, etc). Use when working with two-image subject+style blending or Qwen image editing.
---

# Qwen Prompt Writing

Use this skill when writing prompts for `qwen_standalone_simple.json` or other Qwen-based workflows.

---

## Workflows

| File | Inputs | Use case |
|------|--------|----------|
| `qwen_standalone_simple.json` | 2 images + prompt | Subject + reference/style blending |

**Node layout:**
- Node 21 (image1): the base/subject — treated as the primary image to edit
- Node 27 (image2): the reference/style source
- Node 7: prompt text field — overridden by the runs file via batch_comfy.py
- Output dimensions come from image2's size

---

## Key Behaviors

- **image1 is the base** — Qwen treats image1 as the subject to edit, not image2
- **For makeup transfer**: image1 = person to apply makeup to, image2 = makeup reference
- **Minimal prompts work best** — explicit long prompts cause black (NaN) output. Short or minimal instruction lets Qwen infer from the images
- **"run" as prompt works** — Qwen infers the edit task from the two images with a minimal/meaningless prompt. Use this as a baseline before trying explicit prompts
- VRAM-heavy model: back-to-back runs cause fragmentation → black output → segfault on restart → full system reboot required. **Restart ComfyUI between heavy Qwen sessions.**

---

## Prompt Writing Tips

- Keep prompts short — under ~20 words
- Explicit long instructions (50+ words) cause black NaN output — confirmed 2026-03-22
- "run" as prompt is a valid baseline: model infers from images
- Vary the seed between runs for different outputs with the same prompt
- Do NOT queue multiple Qwen runs back-to-back without restarting ComfyUI between them

---

## Makeup Transfer — Confirmed Working (2026-03-22)

**Setup:**
- image1 = `input/Flux2_00025_.png` (clean headshot, target)
- image2 = `input/face_reference_clean.png` (makeup reference, inner corners cleaned)
- prompt = `"run"` (inferred from images)
- seed = `528173808216037`

**Best result**: `output/qwen_output_00002_.png` — good eyeshadow transfer, clean eye shape preserved, natural lip color (didn't pick up reference lip pink)

**Known gap**: Lip color not transferred from reference — Qwen inferred eye makeup but ignored the lip color difference. Next to try: use a reference with more dramatic lip color, or separate lip pass.

---

## VRAM Management

Qwen loads ~20GB of models. After 3-4 consecutive runs:
- Black output (NaN) with no error in logs
- Restart ComfyUI → segfault (exit 139)
- Fix: **full system reboot** to recover

**Prevention**: Restart ComfyUI after each Qwen generation session, before switching to other heavy models (Flux2, WanVAE).

---

## Two-Image Order — Image Order in CSV Matters

When submitting via batch_comfy.py with a 2-image CSV, the images map positionally to LoadImage nodes in JSON key order. For `qwen_standalone_simple.json`:
- CSV column 1 → Node 21 (image1, base/subject)
- CSV column 2 → Node 27 (image2, reference/style)

**If the transfer goes in the wrong direction** (reference becomes base, subject becomes style donor), swap the two image paths in the CSV. The prompt language alone ("apply from second to first") is not reliable enough to override the positional mapping — swapping paths is required.

**Confirmed 2026-03-27:** Hair style transfer from reference onto character went backwards (character's thin hair applied to the reference) until image paths were swapped in CSV.

---

## Qwen cannot reliably transfer subtle hair volume/texture changes

Qwen two-image is effective for distinct style differences (makeup, outfit, color). It fails to transfer subtle spatial/volumetric hair properties like thickness, fullness, or layering — even with explicit prompt instructions and swapped image order.

**Why:** The model anchors to one image's overall scene/background and treats hair volume as too subtle to enforce.

**Fix:** Use Flux2 image edit with a text description instead (e.g. "thicker, more voluminous, layered waves"). Flux2 can modify hair characteristics from text without requiring a visual reference.

---

## Known Failure Modes

| Failure | Cause | Fix |
|---------|-------|-----|
| Transfer goes in wrong direction | Image order in CSV maps to wrong nodes | Swap the two image paths in CSV |
| Subtle hair volume/texture not transferred | Too subtle for visual matching; model anchors to scene | Use Flux2 text edit instead |
| Subject design not transplanted into scene | Qwen treats scene as base, not subject | Use single-image input + descriptive prompt instead |
| Black output (NaN) from explicit prompt | Long prompt overflows text encoder or triggers safety filter | Use shorter prompt (≤20 words) or "run" |
| Black output after multiple runs | VRAM fragmentation from consecutive heavy runs | Restart ComfyUI (clean restart only — segfault requires full reboot) |
| Lip color not transferred | Model infers most prominent makeup difference (eyes) and ignores subtler changes (lips) | Use reference with more dramatic lip color, or do separate lip pass |

---

## Output Format

```
# Round N: [description]
image1=/path/to/person.png, image2=/path/to/reference.png, prompt="[short instruction or run]"
```
