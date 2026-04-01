# Flux Kontext Prompt Writing

Use this skill when writing or revising prompts for the `image_flux_kontext.json` workflow.

Auto-trigger when: iterating on a single image with targeted edits using Kontext.

---

## What Kontext Is Good At

- **Targeted appearance changes**: changing materials, colors, textures, surface details
- **Adding or removing discrete elements**: removing a window, adding a label
- **Style adjustments**: lighting, finish, surface quality
- **Small positional nudges**: slight adjustments to existing elements

## What Kontext Resists

- **Repositioning existing elements** — asking to "move X to Y" rarely works; the model anchors to the source layout
- **Restoring lost details** — once a detail (e.g. a bezel/frame) is lost in a generation, trying to restore it from that output usually fails; go back to an earlier base image that still has the detail
- **Multiple simultaneous layout changes** — combining repositioning of several elements in one prompt reduces success rate

---

## Core Prompting Patterns

### Removing and re-placing (not "moving")
Instead of: `"Move the handle to the center of the door"`
Use: `"Remove the existing door handle. Add a new [description] handle on the left side at the vertical midpoint of the door."`

The model treats "move" as a weak instruction. "Remove + add new" is a stronger signal.

### Preserving details during edits
When removing an element adjacent to a detail you want to keep, explicitly reinforce the detail:
`"Remove the window. The touchscreen terminal must keep its thick dark gray rectangular bezel framing all four sides of the screen."`

Without reinforcement, adjacent details (bezels, frames, trim) tend to get simplified or lost.

### Going back to an earlier base
If a detail is lost in a generation (e.g. bezel disappears after a window removal), do NOT try to restore it from the output. Instead:
1. Identify the last output where the detail was intact
2. Use that as the new base image
3. Combine the missing edit with explicit preservation of the detail in one prompt

### Combining related edits
Edits that affect the same region of the image should be combined into one prompt. Chaining them as separate passes causes the model to anchor to each intermediate state and resist further changes.

---

## Prompt Structure for Kontext

```
"[Remove X / Add new Y at location Z.] [Describe Y's appearance explicitly.] [Reinforce any adjacent details at risk.] Keep everything else unchanged."
```

- Lead with the removal/addition
- Be explicit about position using absolute landmarks ("vertical midpoint of the door", "top edge near the top of the door")
- Name counts and sides explicitly ("left side", "all four sides")
- End with "Keep everything else unchanged" — this helps anchor the rest of the image

---

## Base Image Selection

The choice of base image matters as much as the prompt.

- Start from the **earliest image that has all the details you want to keep**
- After a successful edit, save the output to `input/` as a new named file if it's a significant milestone
- When a detail is lost, trace back through outputs to find where it was last correct

---

## Guidance Values

- Default `2.5` — works well for targeted edits
- Lower (`1.5–2.0`) — more creative interpretation; useful if the model is being too literal
- Higher (`3.0–4.0`) — tighter adherence; try if edits aren't landing

---

## Known Failure Modes (from sessions)

| Failure | Cause | Fix |
|---------|-------|-----|
| Terminal bezel lost after window removal | Adjacent element removal simplified nearby detail | Go back to pre-removal base, add explicit bezel preservation to prompt |
| Handle won't reposition with "move" | Model anchors to source layout | Use "remove existing handle, add new one at [location]" |
| Background noise accumulates over chained passes | Each generation adds minor artifacts; they compound | After ~4–5 passes on the same lineage, go back to a clean early base and combine all remaining edits into one prompt |
| "Flat vertical handle" renders as horizontal or stays unchanged | Model's "door handle" schema resists shape changes across repeated passes | Avoid the word "handle"; describe the visual: "a small flat rectangular metal plate, taller than it is wide, mounted flush to the door surface" |
| Multiple passes on same image stop working | Model gets locked into intermediate layout | Go back 1–2 generations to a less-anchored base |
| Batch workflow produces all-black output (NaN) | Triton kernel cache corruption after system crash | **Confirmed fix (2026-03-15)**: `rm -rf ~/.triton/cache/` then restart ComfyUI. Kernels recompile on first Kontext run (first job takes a few extra minutes). If still broken after cache clear, set `FLASH_ATTENTION_TRITON_AMD_ENABLE=FALSE` in start_comfyui.sh temporarily. |

## Batch Workflow Status

`batch/image_flux_kontext.json` — single-image self-stitch workflow, working as of 2026-03-15 (Triton cache was cleared after crash, kernels recompiled cleanly).

`batch/kontext_outfit_transfer.json` — two-image stitch workflow (image1=reference, image2=person-to-edit). Created 2026-03-15 for outfit transfer. node 4=LoadImage1, node 15=LoadImage2, stitched left→right.

When the batch workflow is broken, fall back to Flux2 image edit (`batch/image_flux2.json`) for aesthetic edits, or Flux2 text-to-image for layout changes.

## Two-Image Kontext (outfit/style transfer)

`batch/kontext_outfit_transfer.json` takes two images: image1 (left in stitch) = reference style/outfit, image2 (right in stitch) = person to edit. Output is the full stitched image (both halves).

Prompt pattern for outfit transfer:
```
"The woman on the right is wearing [describe original outfit]. Remove her [original outfit]. Dress her in [new outfit description matching the left image]. Preserve her face, [hair description], skin tone, body proportions, and pose exactly. Full body portrait from head to feet. White background. Keep everything else unchanged."
```

- Guidance 4.0 recommended for tighter identity preservation
- "Remove X, replace with Y" lands better than just describing Y

---

## Output Format

```
# Round N[letter]: [one-line description]
/path/to/base_image.png, "[prompt]"
```

Update `batch/auto_closet_extract_runs.csv` (or relevant CSV) with the new line before submitting.
