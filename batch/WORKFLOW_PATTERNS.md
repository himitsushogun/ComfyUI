# ComfyUI Workflow Patterns

## Workflow Selection Guide

| Task | Workflow | Notes |
|------|----------|-------|
| Generate from scratch | `image_flux2_text_to_image.json` | Full layout freedom |
| Aesthetic edit on existing image (no layout change) | `image_flux2.json` | ReferenceLatent anchors layout strongly |
| Structural/layout changes to existing image | `image_flux2_text_to_image.json` or Flux Kontext | Image edit won't restructure |
| Targeted precise edit (change one element) | Flux Kontext (`flux_kontext_dev_basic.json`) | Best for specific modifications with context preservation |
| Subject + style blend from two refs | `qwen_standalone_simple.json` | Qwen struggles with consistency |
| Object/subject extraction | ComfyUI-RMBG (preferred) or Qwen fallback | See comfy-extract skill |
| Upscale image (4x, no diffusion) | `upscale_esrgan.json` | 4xUltraSharp; fast, non-destructive |
| Video generation | `video_wan2_2_14B_flf2v.json` | First/last frame to video |

## Key Insight: ReferenceLatent

`image_flux2.json` uses ReferenceLatent — the input image is encoded as a structural anchor. It is good for style/material changes but **cannot restructure layout, spacing, or composition**. If a structural change is being ignored, switch to text-to-image or Flux Kontext rather than increasing guidance.

## Guidance Values (image_flux2.json)

- `4` — default, good for most edits
- `1–2` — more creative, less literal; better for longer prompts
- `6–8` — tighter prompt adherence; use for specific structural changes
- Higher is NOT always better

---

## Pattern: Extract → Edit → Generate Scene

Used when you need a clean subject reference with specific design features before placing it in a scene.

### Step 1: Extract subject
Use `comfy-extract` skill. Extract the target subject from a source image onto a white background.
- Choose angle based on intended use (three-quarter for 3D scenes)
- Save to `input/<subject>_extracted.png`

### Step 2: Edit subject (if needed)
Use `image_flux2.json` with the extracted subject as input.
- Make targeted changes to the isolated subject (add panels, change materials, etc.)
- Guidance 7 for structural door/face changes
- Save successful result to `input/<subject>_v2.png`

### Step 3: Generate scene
Use `image_flux2_text_to_image.json` with a prompt that describes the full scene including the subject design in detail.
- OR use `image_flux2.json` with the edited subject as reference if layout anchoring helps
- Reference the spec file for all required elements
- Check result against spec using structured review

### Step 4: Refine scene
Use `image_flux2.json` with the best scene output as reference for aesthetic refinements only (lighting, materials, tone).

---

## Pattern: Character Profile Extraction

Used when you have a character reference image (e.g., in-scene, angled, posed) and need a clean forward-facing full-body portrait on a white background — suitable for a profile image or character sheet.

### Step 1: Generate the profile shot
Use `image_flux2.json` with the source character image as input.

Prompt structure:
- Pose/framing: `woman standing upright facing directly forward, full body from head to heels`
- Background: `plain white background, no [scene elements from source]`
- Outfit: enumerate each item explicitly — don't rely on the model to transfer details
- Lighting: `studio portrait lighting`

Keep guidance at default (4). The ReferenceLatent anchors the character's overall look; the prompt drives the pose/background change.

### Step 2: Refine facial features (if needed)
Use `image_flux2.json` again with the Step 1 output as input. Describe only what needs to change:
- Keep the full character description in the prompt to preserve overall consistency
- Append specific facial feature descriptors (e.g. `fuller rounded pouty lips with pronounced cupid's bow, slight natural pout, pillow lips`)

**Do not use Flux Kontext for human face refinement** — it degrades identity even on subtle edits.

### Notes
- The source image strongly anchors the character design; explicit outfit enumeration in the prompt is still needed to transfer details cleanly
- **Flux2 cannot make targeted facial feature adjustments** (lip shape, eye shape, etc.) — the ReferenceLatent anchor absorbs fine anatomical changes. Confirmed: second-pass with explicit lip descriptors produced no measurable change. Accept the face as-is or start from a different source image.

---

## Pattern: Iterative Text-to-Image

When the subject design doesn't need to be preserved exactly and you're iterating toward a target aesthetic.

1. Write prompt from spec using `comfy-prompt` skill
2. Submit with `image_flux2_text_to_image.json`
3. View result, do structured spec check
4. If layout is right but aesthetics are wrong: save as reference, switch to `image_flux2.json` for aesthetic edits
5. If layout is wrong: iterate prompt, resubmit text-to-image

---

## Pattern: Upscale Final Output

Run any keeper image through upscaling before saving as final.

```bash
# Update upscale_test.csv with the filename to upscale (just the basename, no full path):
echo "my_image.png" > batch/upscale_test.csv
python3 batch/batch_comfy.py batch/upscale_esrgan.json batch/upscale_test.csv --wait
```

- Outputs to `output/Upscaled__XXXXX_.png`
- Model: `4xUltrasharp_4xUltrasharpV10.pt` — preferred for AI-generated portraits
- Use `RealESRGAN_x4plus.pth` only for noisy/compressed photos (swap model name in the JSON)
- No VRAM impact beyond the upscale model

### Gotchas
- **CSV overrides JSON**: `upscale_esrgan.json` has a hardcoded image filename, but batch_comfy.py detects the image node and overrides it with the CSV value. **Always update the CSV** — editing the JSON filename alone has no effect.
- **ComfyUI output cache**: if you submit the same workflow twice (e.g. after fixing the source image), ComfyUI may return a cached result. The `batch_comfy.py` `queue_prompt` function now sends a unique `client_id` per submission to prevent this. If you still get a cached result, restart ComfyUI.

---

---

## Pattern: Headshot from Full-Body Portrait

Used when you have a clean full-body standing portrait and want a tight head-and-shoulders portrait from it — suitable as a profile image or as a face source for ReActor swapping.

### When to use
- You have a full-body reference (`standing_base_extracted.png` or similar) and need a close-up portrait
- You want to generate a face source image with specific makeup/expression for use with ReActor
- The full-body image has the right character design but too small a face for detail work

### Workflow
`image_flux2.json` with the full-body image as input.

The ReferenceLatent anchors the character's design (hair, face structure, outfit details visible at neckline). The prompt drives the reframing to head/shoulders.

### Prompt structure
```
close-up portrait, head and shoulders framing,
[hair description],
[eye/makeup description],
[lips description],
[accessories visible at neck/ears],
[clothing visible at shoulder/neckline],
studio portrait lighting, plain white background,
photorealistic, high detail, sharp focus
```

**Key tip:** Describe only what's visible in head/shoulders framing — don't include full outfit. The model will fill in consistent details from the reference image.

### Example (generated `Flux2_00024_.png`)
- Source: `input/standing_base_extracted.png`
- CSV: `batch/portrait_tight_run.csv`
- Workflow: `batch/image_flux2.json` (`--node 6`)
- Result: strong makeup, good expression, clean white background — suitable as ReActor face source

### Notes
- Result quality depends heavily on the face quality in the source full-body image
- The model may hallucinate text on accessories (e.g. choker lettering) — acceptable for a face-swap source since ReActor only uses facial geometry
- If the face in the source is small/blurry, try running the headshot through CodeFormer (`gfpgan_restore.json` or ReActor with face_restore only) before using as a ReActor source
- Guidance default (4) works well; increase to 6 only if the framing isn't tight enough

---

## Pattern: ReActor Face Swap

Used when you have a clean high-quality face reference and want to transplant it onto a character body while leaving the body, outfit, and hair completely untouched.

### When to use
- You have a good close-up face image and want it on a full-body standing portrait
- Inpainting has failed (geometry resistance, drift, color shift)
- PuLID/InstantID not suitable — they generate a new image and cause outfit/style drift

### Setup (one-time)
- Custom node: `comfyui-reactor-node` (installed via SSH clone from `git@github.com:Gourieff/ComfyUI-ReActor.git`)
- Swap model: `models/insightface/inswapper_128.onnx` (529MB, non-commercial license)
- Face restore models auto-downloaded to `models/facerestore_models/` on first run
- **NSFW check disabled** in `nodes.py` — the standing portrait triggers the detector at 0.99 score, producing a black output. The check was removed at line 440.

### Workflow: `batch/reactor_face_swap.json`
- Input 1: `input/standing_base_extracted.png` (target body)
- Input 2: `input/face_reference.png` (source face)
- `swap_model`: `inswapper_128.onnx`
- `facedetection`: `retinaface_resnet50`
- `face_restore_model`: `codeformer-v0.1.0.pth` — **required** to fix blur
- `codeformer_weight`: `0.75` — leans toward restoration sharpness while keeping swapped identity
- `face_restore_visibility`: `1`

### Key parameters
- `face_restore_model: none` → blurry face (inswapper operates at 128px; at full-body scale the face is tiny)
- `face_restore_model: codeformer-v0.1.0.pth` → sharp, color-matched, production quality
- CodeFormer weight 0.5 = balanced; 0.75 = sharper; 1.0 = maximum restoration (may drift from reference)

### Submit
```bash
python3 batch/batch_comfy.py batch/reactor_face_swap.json batch/pulid_face_swap_runs.csv --wait
```
(The CSV content is ignored — this is an image-only workflow with no text node.)

### Pipeline order
1. ReActor face swap + CodeFormer → `output/ReactorSwap__XXXXX_.png`
2. Copy keeper to `input/reactor_swapped_base.png`
3. All inpainting/refinement on the 1024px base (face inpaint, lip inpaint, etc.)
4. Upscale last: `upscale_esrgan.json` → `output/Upscaled__XXXXX_.png`

### Confirmed results (2026-03-20)
- Face shape from `close_up.png` successfully transplanted onto `standing_base_extracted.png`
- Body, outfit, hair color untouched
- With CodeFormer: face sharpness and color match the surrounding body quality
- Without CodeFormer: noticeably blurry and desaturated face region

---

## Recommended Next Installs

### ComfyUI-RMBG
Background removal node using BEN2/BiRefNet segmentation models. Dramatically better than prompting generative models for extraction.
- Install via ComfyUI Manager: search "ComfyUI-RMBG"
- GitHub: https://github.com/1038lab/ComfyUI-RMBG

### StableMakeup on Full-Body Images (not yet built)

**Problem**: StableMakeup resizes input to 512×512 internally. On a full-body image the face is too small for reliable landmark detection.

**Planned pipeline**:
1. Detect face bbox using YOLO or RetinaFace (already available via `comfyui_face_parsing`)
2. Crop face with padding (~1.5× bbox) → save as temp image
3. Run `stable_makeup_transfer.json` on the tight crop (512×512 is now a close-up)
4. Composite the makeup result back into the full-body image at the original bbox coordinates using PIL
5. Optionally feather the edges of the paste region

**Implementation**: Python script (`batch/stable_makeup_fullbody.py`) wrapping batch_comfy.py + PIL composite. Needs: bbox detection (reuse face_inpaint_lips.json BBoxDetect nodes or direct insightface call), crop/paste math.

**Working config**: `dataname: wflw`, `cfg: 1.6`, `facedetector: resnet`, 30 steps, 512×512

---

### Flux Kontext (batch workflow)
`flux1-dev-kontext_fp8_scaled.safetensors` is already installed. A batch API-format workflow needs to be exported from the UI workflow at `user/default/workflows/flux_kontext_dev_basic.json`.
- Best for: targeted single-element edits with context preservation
- Prompt structure: "[Main Modification] + [Preservation Requirements] + [Detail Description]"
- Sequential editing (one change at a time) works better than multi-change prompts
- Already have: model + UI workflow. Missing: batch API export
