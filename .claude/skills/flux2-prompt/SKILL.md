---
name: flux2-prompt
description: Write or revise prompts for Flux2 ComfyUI workflows (image_flux2.json for image editing, image_flux2_text_to_image.json for text-to-image). Use for style/aesthetic edits on existing images or new compositions.
---

# Flux2 Prompt Writing

Use this skill when writing prompts for `image_flux2.json` (image edit) or `image_flux2_text_to_image.json` (text-to-image).

---

## Prompt Structure

**Critical info goes first** — Flux2 weighs earlier tokens more heavily. Lead with what matters most.

**Text-to-image:**
```
[subject and layout], [specific counts and spatial relationships], [materials and surface details], [setting and architecture], [lighting], [art style and quality tags]
```

**Image editing (with reference):**
Describe *only what should change* — do not redescribe the whole scene. The model preserves context automatically.

**Negative prompts**: not required for Flux2. Skip them.

---

## Guidance Values (FluxGuidance node)

- Default `4` — good baseline
- Lower (`1.0–1.5`) — more creative, less literal; useful for longer prompts or style blending
- Higher (`6–8`) — tighter adherence; useful when a specific element needs precise placement
- Do NOT assume higher = better. For image editing with a reference, lower guidance often blends better.

---

## Key Behaviors

- `image_flux2.json` uses `ReferenceLatent` conditioning — the input image is a strong structural anchor. If the model keeps producing the source image unchanged, switch to text-to-image rather than raising guidance.
- Layout changes, adding/removing elements, new compositions: use text-to-image, not image edit.

---

## Prompt Writing Tips

1. Lead with what changes, not what to preserve
2. Name counts explicitly — "four units", "two windows"
3. Describe spatial relationships — "standing along the back wall", "centered on the door"
4. Describe materials and surfaces specifically — "polished beige tile", "brushed chrome frame"
5. Exclude by naming — "no people", "no extra fixtures"

---

## Known Failure Modes

| Failure | Cause | Fix |
|---------|-------|-----|
| Source image unchanged despite prompt | ReferenceLatent anchors layout strongly | Switch to text-to-image for layout/composition changes |

---

## Output Format

```
# Round N: [description]
"[prompt]"
```

For image edit, prefix with image path:
```
# Round N: [description]
/path/to/image.png, "[prompt]"
```
