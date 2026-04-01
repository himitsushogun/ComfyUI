#!/usr/bin/env python3
"""
batch_comfy.py — batch-submit prompts (and optionally images) to a ComfyUI workflow.

Quickstart:
  1. Export your workflow in API format (see below)
  2. Create a runs file (prompts only, or image+prompt pairs)
  3. Run: python batch_comfy.py workflow_api.json runs.txt

Getting API format from ComfyUI:
  - Settings (gear icon) → Enable Dev Mode Options
  - A "Save (API Format)" button appears in the bottom toolbar
  - Export and save the .json file

Runs file formats:

  Prompts only (one per line):
    a beautiful sunset over mountains, cinematic, 8k
    a futuristic city at night, neon lights

  Image + prompt pairs (CSV — up to 3 image columns before the prompt):
    /path/to/photo1.jpg, a photo of a dog wearing a hat
    /path/to/photo1.jpg, /path/to/photo2.jpg, apply style of second to first
    /path/to/a.jpg, /path/to/b.jpg, /path/to/c.jpg, "blend all three, artistically"

  Lines starting with # and blank lines are ignored in both formats.

Usage:
  python batch_comfy.py workflow_api.json runs.txt
  python batch_comfy.py workflow_api.json runs.txt --wait
  python batch_comfy.py workflow_api.json runs.txt -n "Positive Prompt" -i "Input A" -i "Input B"
  python batch_comfy.py workflow_api.json --list-nodes
"""

import argparse
import copy
import csv
import io
import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.request

DEFAULT_SERVER = "http://localhost:8188"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tiff", ".tif"}
MAX_IMAGES = 3


# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------

def api_get(path, server):
    with urllib.request.urlopen(f"{server}{path}") as r:
        return json.loads(r.read())


def api_post(path, data, server):
    body = json.dumps(data).encode()
    req = urllib.request.Request(
        f"{server}{path}", data=body, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


def upload_image(filepath, server, overwrite=False):
    """Upload an image file to ComfyUI's input directory via multipart POST."""
    boundary = "ComfyBatchUploadBoundary"
    filename = os.path.basename(filepath)
    mime_type = mimetypes.guess_type(filepath)[0] or "image/png"

    with open(filepath, "rb") as f:
        file_data = f.read()

    def field(name, value):
        return (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{name}"\r\n'
            f"\r\n"
            f"{value}\r\n"
        ).encode()

    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="image"; filename="{filename}"\r\n'
        f"Content-Type: {mime_type}\r\n"
        f"\r\n"
    ).encode() + file_data + b"\r\n"
    body += field("type", "input")
    body += field("overwrite", "true" if overwrite else "false")
    body += f"--{boundary}--\r\n".encode()

    req = urllib.request.Request(
        f"{server}/upload/image",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


def queue_prompt(workflow, server):
    import uuid
    return api_post("/prompt", {"prompt": workflow, "client_id": str(uuid.uuid4())}, server)


def wait_for_completion(prompt_id, server, poll_interval=2):
    while True:
        history = api_get(f"/history/{prompt_id}", server)
        if prompt_id in history:
            return history[prompt_id]
        time.sleep(poll_interval)


# ---------------------------------------------------------------------------
# Workflow introspection
# ---------------------------------------------------------------------------

TEXT_NODE_TYPES = {
    "CLIPTextEncode", "CLIPTextEncodeFlux", "CLIPTextEncodeSD3",
    "CLIPTextEncodeHunyuan", "CLIPTextEncodeWan", "smZ CLIPTextEncode",
    "ImpactWildcardProcessor", "WildcardProcessor",
    "TextEncodeQwenImageEditPlus",
}


def find_text_nodes(workflow):
    """Return [(node_id, title, class_type, field)] for prompt-text nodes."""
    results = []
    for node_id, node in workflow.items():
        ct = node.get("class_type", "")
        title = node.get("_meta", {}).get("title", "")
        inputs = node.get("inputs", {})
        if ct in TEXT_NODE_TYPES:
            field = "text" if "text" in inputs else next(
                (k for k, v in inputs.items() if isinstance(v, str)), None
            )
            if field:
                results.append((node_id, title or ct, ct, field))
        elif "text" in inputs and isinstance(inputs.get("text"), str) and len(inputs["text"]) > 5:
            results.append((node_id, title or ct, ct, "text"))
    return results


def find_image_nodes(workflow):
    """Return [(node_id, title, class_type, field)] for LoadImage nodes."""
    results = []
    for node_id, node in workflow.items():
        ct = node.get("class_type", "")
        title = node.get("_meta", {}).get("title", "")
        if ct == "LoadImage":
            results.append((node_id, title or "LoadImage", ct, "image"))
    return results


def resolve_node(workflow, spec, candidates_fn, kind="text"):
    """Return (node_id, field) given a node ID string or title."""
    if spec in workflow:
        node = workflow[spec]
        inputs = node.get("inputs", {})
        default_field = "image" if kind == "image" else "text"
        field = default_field if default_field in inputs else next(
            (k for k, v in inputs.items() if isinstance(v, str) and len(v) > 2), None
        )
        if field is None:
            sys.exit(f"Error: node {spec!r} has no obvious {kind} input field")
        return spec, field

    for node_id, node in workflow.items():
        title = node.get("_meta", {}).get("title", "")
        if title.lower() == spec.lower():
            inputs = node.get("inputs", {})
            default_field = "image" if kind == "image" else "text"
            field = default_field if default_field in inputs else next(
                (k for k, v in inputs.items() if isinstance(v, str)), None
            )
            return node_id, field or default_field

    sys.exit(f"Error: no node with ID or title {spec!r}. Use --list-nodes to inspect.")


# ---------------------------------------------------------------------------
# Runs file parsing
# ---------------------------------------------------------------------------

def _is_image_path(s):
    return os.path.splitext(s.strip())[1].lower() in IMAGE_EXTENSIONS


def load_runs(filepath):
    """
    Parse a runs file. Returns a list of (images: list[str], prompt_text: str).

    Supports two formats:
      - Plain text: one prompt per line → images=[]
      - CSV: up to MAX_IMAGES leading image-path columns (detected by extension),
             then the remaining columns form the prompt text.

    Lines starting with # and blank lines are ignored.
    """
    with open(filepath, newline="") as f:
        raw = f.read()

    # Strip comment and blank lines for format detection
    content_lines = [
        l for l in raw.splitlines()
        if l.strip() and not l.strip().startswith("#")
    ]
    if not content_lines:
        return []

    # Detect CSV format: first field of first line looks like an image path
    first_fields = next(csv.reader([content_lines[0]]))
    is_csv = _is_image_path(first_fields[0])

    runs = []
    reader = csv.reader(io.StringIO(raw))
    for line_num, row in enumerate(reader, 1):
        if not row:
            continue
        raw_line = ",".join(row).strip()
        if raw_line.startswith("#"):
            continue
        if not raw_line:
            continue

        if is_csv:
            # Consume leading fields that look like image paths (up to MAX_IMAGES)
            images = []
            i = 0
            while i < len(row) and i < MAX_IMAGES and _is_image_path(row[i]):
                images.append(row[i].strip())
                i += 1
            prompt = ",".join(row[i:]).strip() if i < len(row) else ""
            runs.append((images, prompt))
        else:
            runs.append(([], raw_line))

    return runs


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Batch-submit prompts (and images) to ComfyUI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("workflow", help="Workflow JSON in API format")
    parser.add_argument("runs", nargs="?",
                        help="Runs file: prompts.txt or image_prompt.csv")
    parser.add_argument("--node", "-n", metavar="ID_OR_TITLE",
                        help="Text node to inject the prompt into")
    parser.add_argument("--image-node", "-i", metavar="ID_OR_TITLE",
                        action="append", dest="image_nodes",
                        help="LoadImage node to inject an image into (repeat for multiple nodes)")
    parser.add_argument("--field", "-f", default=None,
                        help="Input field name on the text node (default: 'text')")
    parser.add_argument("--url", "-u", default=DEFAULT_SERVER,
                        help=f"ComfyUI server URL (default: {DEFAULT_SERVER})")
    parser.add_argument("--wait", "-w", action="store_true",
                        help="Wait for each job to finish before submitting the next")
    parser.add_argument("--list-nodes", "-l", action="store_true",
                        help="Show text and image nodes in the workflow and exit")
    args = parser.parse_args()

    server = args.url.rstrip("/")

    with open(args.workflow) as f:
        workflow = json.load(f)

    if "nodes" in workflow and "links" in workflow:
        sys.exit(
            "Error: this looks like a UI-format workflow, not API format.\n"
            "In ComfyUI: Settings → Enable Dev Mode Options → Save (API Format)"
        )

    # --list-nodes
    if args.list_nodes:
        text_nodes = find_text_nodes(workflow)
        image_nodes = find_image_nodes(workflow)
        if text_nodes:
            print("Text nodes:")
            for nid, title, ct, field in text_nodes:
                val = workflow[nid]["inputs"].get(field, "")
                print(f"  [{nid:>4}] {ct}  title={title!r}  field={field!r}")
                print(f"           current: {str(val)[:100]!r}")
        else:
            print("No text nodes auto-detected.")
        if image_nodes:
            print("\nImage nodes (LoadImage):")
            for nid, title, ct, field in image_nodes:
                val = workflow[nid]["inputs"].get(field, "")
                print(f"  [{nid:>4}] {ct}  title={title!r}  field={field!r}")
                print(f"           current: {val!r}")
        else:
            print("No LoadImage nodes found.")
        if not text_nodes and not image_nodes:
            print("\nAll nodes:")
            for nid, node in workflow.items():
                print(f"  [{nid:>4}] {node.get('class_type','?')}  "
                      f"title={node.get('_meta',{}).get('title','')!r}")
        return

    if not args.runs:
        parser.error("runs file is required (or use --list-nodes)")

    runs = load_runs(args.runs)
    if not runs:
        sys.exit("Error: no runs found in file")

    has_images = any(imgs for imgs, _ in runs)

    # Resolve text node
    text_node_id = None
    text_field = "text"
    if args.node:
        text_node_id, text_field = resolve_node(workflow, args.node,
                                                find_text_nodes, kind="text")
        if args.field:
            text_field = args.field
    else:
        candidates = find_text_nodes(workflow)
        if len(candidates) == 0:
            pass  # image-only workflow — text injection skipped
        elif len(candidates) > 1:
            print("Multiple text nodes — specify one with --node:", file=sys.stderr)
            for nid, title, ct, _ in candidates:
                print(f"  [{nid}] {ct}  title={title!r}", file=sys.stderr)
            sys.exit(1)
        else:
            text_node_id, _, _, text_field = candidates[0]
            if args.field:
                text_field = args.field

    # Resolve image nodes (ordered list, mapped to image columns by position)
    image_node_specs = []  # [(node_id, field), ...]
    if has_images:
        if args.image_nodes:
            for spec in args.image_nodes:
                nid, fld = resolve_node(workflow, spec, find_image_nodes, kind="image")
                image_node_specs.append((nid, fld))
        else:
            candidates = find_image_nodes(workflow)
            if len(candidates) == 0:
                sys.exit("Runs file has image paths but no LoadImage node found in workflow.")
            for nid, _title, _ct, fld in candidates[:MAX_IMAGES]:
                image_node_specs.append((nid, fld))
            if len(candidates) > MAX_IMAGES:
                print(f"Note: workflow has {len(candidates)} LoadImage nodes; "
                      f"using first {MAX_IMAGES}.", file=sys.stderr)

    if text_node_id:
        print(f"Text node  [{text_node_id}] field={text_field!r}")
    else:
        print("Text node  (none — image-only workflow)")
    if image_node_specs:
        for idx, (nid, fld) in enumerate(image_node_specs, 1):
            label = f"Image node {idx}" if len(image_node_specs) > 1 else "Image node"
            print(f"{label:11}[{nid}] field={fld!r}")
    print(f"Submitting {len(runs)} run(s) to {server}")
    print()

    width = len(str(len(runs)))
    for i, (images, prompt_text) in enumerate(runs, 1):
        wf = copy.deepcopy(workflow)
        if text_node_id:
            wf[text_node_id]["inputs"][text_field] = prompt_text

        # Upload and inject each image into its corresponding node
        if images and len(images) > len(image_node_specs):
            print(f"  Warning: run {i} has {len(images)} image(s) but only "
                  f"{len(image_node_specs)} image node(s); extra images ignored.")

        for img_path, (img_node_id, img_field) in zip(images, image_node_specs):
            if os.path.isfile(img_path):
                try:
                    result = upload_image(img_path, server, overwrite=True)
                    uploaded_name = result["name"]
                except Exception as e:
                    sys.exit(f"Failed to upload {img_path!r}: {e}")
            else:
                # Assume it's already a filename in the ComfyUI input directory
                uploaded_name = os.path.basename(img_path)
            wf[img_node_id]["inputs"][img_field] = uploaded_name

        try:
            result = queue_prompt(wf, server)
        except urllib.error.URLError as e:
            sys.exit(f"Connection error — is ComfyUI running at {server}?\n{e}")

        pid = result.get("prompt_id", "?")
        print(f"[{i:{width}}/{len(runs)}] {pid}")
        for idx, img_path in enumerate(images, 1):
            label = f"image {idx}" if len(images) > 1 else "image "
            print(f"         {label}: {os.path.basename(img_path)}")
        if prompt_text:
            print(f"         prompt: {prompt_text[:100]}")

        if args.wait:
            wait_for_completion(pid, server)
            print(f"         done")

    print(f"\nAll {len(runs)} runs queued.")
    if not args.wait:
        try:
            qs = api_get("/queue", server)
            running = len(qs.get("queue_running", []))
            pending = len(qs.get("queue_pending", []))
            print(f"Queue status: {running} running, {pending} pending")
        except Exception:
            pass


if __name__ == "__main__":
    main()
