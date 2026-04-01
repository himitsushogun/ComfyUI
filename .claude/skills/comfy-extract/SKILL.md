---
name: comfy-extract
description: Extract or isolate a specific object or subject from an image for use as a reference in subsequent generation. Use when the user wants to isolate a product, character, object, or element from a scene image. Trigger when asked to "extract", "isolate", "get a clean shot of", or "use X as a reference" where X needs to be separated from its background.
---

# ComfyUI Subject Extraction

Extract a specific subject from a scene image to use as a clean reference for subsequent generation.

---

## Preferred Method: ComfyUI-RMBG (Background Removal Node)

**Status**: NOT YET INSTALLED — needs installation via ComfyUI Manager.

`ComfyUI-RMBG` uses dedicated segmentation models (BEN2, BiRefNet, RMBG-2.0) for clean, precise background removal. This is far superior to asking a generative model to remove backgrounds via text prompt.

**To install**: Open ComfyUI Manager → Search "ComfyUI-RMBG" → Install. Models download automatically on first use.

**Recommended model**: BEN2 or BiRefNet-HR (test both; BiRefNet-HR occasionally over-corrects).

Until installed, use the **Qwen fallback** below.

---

## Fallback Method: Qwen Extraction Prompt

Use `qwen_standalone_simple.json` with the source image passed for both image slots.

### Runs CSV format
```
# Extract <subject> — <angle>, white background
/path/to/source.png, /path/to/source.png, "Isolate the <subject> from the image. Show only that subject, centered in frame, against a plain white background. Remove all other elements — background, other objects, floor, walls. <angle description>. Product shot style, photorealistic, high detail, sharp focus."
```

### Angle guidance

**Choose angle based on intended use:**

| Intended use | Angle to extract |
|---|---|
| Flat reference only (color, texture, label) | Straight-on front view |
| Reference for 3D scene generation | Three-quarter angle showing depth and side face |
| Character reveal | Three-quarter or slight angle |
| Architectural/environment element | Three-quarter showing depth |

For lobby_autoclosets.png: three-quarter angle is needed so the generated scene shows the unit with depth.

### Example — three-quarter extraction
```
# Extract single Auto-Closet unit — three-quarter angle, white background
/home/derek/ComfyUI/input/source.png, /home/derek/ComfyUI/input/source.png, "Isolate the leftmost Auto-Closet unit from the image. Show only that single unit at a three-quarter angle revealing its front face and one side, centered against a plain white background. Remove all other units, walls, floor, and lobby elements. Full unit visible top to bottom. Product shot style, photorealistic, high detail, sharp focus."
```

---

## After Extraction

1. Review the result — check for clean edges, no background bleed, correct subject isolated
2. Save to `input/` with a descriptive name: `cp output/qwen_output_XXXXX_.png input/<subject_name>.png`
3. Note the angle in the filename if relevant: `auto_closet_single_3q.png`

---

## Multi-Step Workflow Reference

See `batch/WORKFLOW_PATTERNS.md` for the full extract → edit → generate lobby pattern.
