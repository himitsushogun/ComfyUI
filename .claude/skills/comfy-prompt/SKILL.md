---
name: comfy-prompt
description: Write or revise a ComfyUI image generation prompt for the Boutique game or any other image task. Auto-trigger when the user asks to generate an image, write a prompt, iterate on a generated image, or fix a prompt that isn't producing the right result. Also trigger when viewing a generated image and deciding what to change for the next round.
---

# ComfyUI Prompt Writing — Index

## Workflow Selection

| Situation | Workflow | Skill |
|-----------|----------|-------|
| Targeted edits to a single image (appearance, materials, element removal/addition) | `image_flux_kontext.json` | `kontext-prompt` |
| Iterating from a good existing image (style/aesthetic only, no layout changes) | `image_flux2.json` | `flux2-prompt` |
| Layout changes, new composition, adding/removing elements | `image_flux2_text_to_image.json` | `flux2-prompt` |
| Subject + style blending from two references | `qwen_standalone_simple.json` | `qwen-prompt` |
| **Outfit/clothing transfer onto a person** | CatVTON or Kontext | `clothing-transfer` |

When in doubt between Kontext and Flux2 edit: if the change is to an existing element in-place, use Kontext. If the overall composition needs to change, use Flux2 text-to-image.

---

## Living Skills Protocol

After every generation round, update the relevant model skill file if:
- A new prompting pattern worked or failed
- A model behavior was observed
- A recovery strategy was found
- A parameter value produced notably better/worse results

Only update after seeing results — not before.

---

## Image Review Protocol

After viewing any generated image, do a structured spec check before writing the next prompt:

1. Read the spec file for the asset
2. For each spec item, assess: ✓ passing / ✗ failing / ~ partially
3. Report as a table — do not skip items or give a general impression
4. Only include passing items in the next prompt if they are at risk of being lost
5. Update the spec status after each round

---

## Target Spec Protocol

Every asset being iterated on should have a spec file at `batch/<asset_name>_spec.md`.

- **On first use**: create the spec from the stated requirements
- **Before each prompt**: read the spec and use it as source of truth
- **After each round**: update to reflect what's working and what still needs fixing

### Spec format

```markdown
# <asset_name> — Target Spec

## Camera
## Subject
## Layout
## Environment
## Style

## Status (updated each round)
Working: [list]
Still needed: [list]
```

---

## Style Anchors

- **Environment/establishing shots:** `cinematic still, photorealistic, high detail, sharp focus`
- **Character reveals:** `realistic, photorealistic, soft studio lighting, high detail, sharp focus`
- **Product/object isolation:** `product shot, plain white background, photorealistic, high detail, sharp focus`

---

## Project Context (Boutique Game)

If working on a Boutique game asset, read before writing:
- `/home/derek/Twine/Boutique/docs/ART_PROMPTS.md` — canonical prompts and asset list
- `/home/derek/Twine/Boutique/.claude/agents/art.md` — full art direction guide

**Visual tone**: Corporate realism tipping into adult fantasy. No anime, no painterly, no fantasy. Clinical and mechanical for transformation scenes; clean corporate for environment shots.

If working on `lobby_autoclosets.png`, also read:
- `/home/derek/ComfyUI/batch/lobby_autoclosets_spec.md`

---

## Output Format

```
# Round N: [one-line description of what changed]
"[full positive prompt]"
```

For image+prompt workflows:
```
# Round N: [description]
/path/to/image.png, "[prompt]"
```
