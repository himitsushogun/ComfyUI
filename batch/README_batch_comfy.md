# batch_comfy.py

Batch-submit prompts (and optionally images) to a ComfyUI workflow from a file, using the ComfyUI REST API. No clicking required.

## Requirements

- ComfyUI running locally (default: `http://localhost:8188`)
- Python 3 — stdlib only, no extra packages needed
- Your workflow exported in **API format** (see below)

## Getting the API-format workflow

The workflow files saved by the ComfyUI UI are in graph format and won't work directly. You need to export the API format once:

1. Open ComfyUI in your browser
2. **Settings** (gear icon) → enable **Dev Mode Options**
3. Load your workflow
4. Click **Save (API Format)** in the bottom toolbar
5. Save the resulting `.json` somewhere convenient

## Runs file formats

### Prompts only

One prompt per line. Blank lines and lines starting with `#` are ignored.

```
# prompts.txt

a majestic wolf on a snowy peak, cinematic, 8k
a futuristic city at night, neon reflections, cyberpunk
a serene Japanese garden in autumn, soft morning light
```

### Image + prompt pairs (CSV)

For image-editing workflows. One or more image paths come first (up to 3), then the prompt. Images are matched to `LoadImage` nodes in the order they appear in the workflow. If a prompt contains commas, wrap it in quotes.

```
# runs.csv

# Single image:
/home/derek/ComfyUI/input/photo1.jpg, remove the background, replace with snowy mountains
/home/derek/ComfyUI/input/photo2.jpg, "change lighting to golden hour, warm tones"

# Two images (subject + reference):
/home/derek/ComfyUI/input/subject.jpg, /home/derek/ComfyUI/input/style.jpg, apply the style of the second image to the subject

# Three images:
/home/derek/ComfyUI/input/a.jpg, /home/derek/ComfyUI/input/b.jpg, /home/derek/ComfyUI/input/c.jpg, "blend all three, surreal composite"
```

Image paths can be absolute or relative to where you run the script. Images are uploaded to ComfyUI's input directory automatically. If a path doesn't exist as a file, it's assumed to already be in the input directory and used as-is.

## Usage

```bash
# Prompts only — auto-detect the prompt node
python batch_comfy.py workflow_api.json prompts.txt

# Image + prompt pairs — auto-detect both nodes
python batch_comfy.py workflow_api.json runs.csv

# Inspect the workflow — shows detected text and image nodes
python batch_comfy.py workflow_api.json --list-nodes

# Specify nodes by ID or title (set in the ComfyUI node header)
python batch_comfy.py workflow_api.json runs.csv -n "Positive Prompt" -i "Input Image"
python batch_comfy.py workflow_api.json runs.csv -n 42 -i 7

# Multiple image nodes (repeat -i for each node, in column order)
python batch_comfy.py workflow_api.json runs.csv -i "Subject Image" -i "Style Image"

# Run one at a time (recommended for large models / memory-constrained setups)
python batch_comfy.py workflow_api.json runs.csv --wait

# Point at a non-default server
python batch_comfy.py workflow_api.json runs.csv --url http://localhost:8188
```

## Options

| Flag | Short | Description |
|------|-------|-------------|
| `--list-nodes` | `-l` | Show text and image nodes in the workflow and exit |
| `--node ID_OR_TITLE` | `-n` | Text node to inject the prompt into |
| `--image-node ID_OR_TITLE` | `-i` | LoadImage node to inject an image into (repeat for multiple) |
| `--field NAME` | `-f` | Input field name on the text node (default: `text`) |
| `--wait` | `-w` | Wait for each job to complete before queuing the next |
| `--url URL` | `-u` | ComfyUI server address (default: `http://localhost:8188`) |

## Node selection

The script auto-detects `CLIPTextEncode` nodes (and common variants) for text, and `LoadImage` nodes for images. If your workflow has multiple text nodes, it will list them and ask you to pick with `-n`. For image nodes, multiple `LoadImage` nodes are used automatically in the order they appear in the workflow JSON, mapped to image columns left-to-right. Use `-i` (repeatable) to specify the order explicitly.

You can title any node in the ComfyUI UI by double-clicking its header, then reference it by name instead of ID.

## Tips

- **`--wait`** runs one job at a time. Recommended when using large models with `--lowvram`, since back-to-back queue entries trigger repeated model unload/reload cycles that can cause memory issues.
- Everything not in your runs file stays exactly as saved in the API JSON — model, sampler, resolution, seed, etc.
- To vary other parameters (seeds, steps, etc.), edit the API JSON directly before running — all node inputs are plain JSON values.
