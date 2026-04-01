#!/usr/bin/env python3
"""
inspect_workflow.py — print a readable summary of a ComfyUI workflow JSON.

Usage:
  python3 batch/inspect_workflow.py <workflow.json>
  python3 batch/inspect_workflow.py batch/blondiebimbo_test.json
"""

import json
import sys
from pathlib import Path

# Fields worth showing when present
KEY_FIELDS = [
    "text", "lora_name", "strength_model", "strength_clip",
    "gguf_name", "unet_name", "vae_name", "ckpt_name",
    "clip_name1", "clip_name2", "clip_name",
    "image", "filename_prefix",
    "seed", "steps", "cfg", "sampler_name", "scheduler", "denoise",
    "width", "height", "batch_size",
]

def summarise(inputs: dict) -> str:
    parts = []
    for field in KEY_FIELDS:
        if field in inputs:
            val = inputs[field]
            if isinstance(val, list):
                continue  # skip node-link refs
            if isinstance(val, str) and len(val) > 80:
                val = val[:77] + "..."
            parts.append(f"{field}={val!r}")
    return "  |  ".join(parts) if parts else ""

def load_workflow(path: Path) -> dict:
    with open(path) as f:
        d = json.load(f)
    # Support both API format (dict of node_id -> node) and
    # UI format (dict with top-level "nodes" list)
    if "nodes" in d and isinstance(d["nodes"], list):
        return {str(n["id"]): {"class_type": n.get("type", "?"),
                                "inputs": {w["name"]: w.get("widget", {})
                                           for w in n.get("inputs", [])
                                           if "widget" in w},
                                "_meta": {"title": n.get("title", "")}}
                for n in d["nodes"]}
    return d

def main():
    if len(sys.argv) < 2:
        print("Usage: inspect_workflow.py <workflow.json>")
        sys.exit(1)

    path = Path(sys.argv[1])
    if not path.exists():
        # Try relative to batch/ or ComfyUI root
        for base in [Path(__file__).parent, Path(__file__).parent.parent]:
            candidate = base / path
            if candidate.exists():
                path = candidate
                break
        else:
            print(f"File not found: {sys.argv[1]}")
            sys.exit(1)

    nodes = load_workflow(path)
    print(f"\n{path.name}  ({len(nodes)} nodes)\n")
    print(f"  {'ID':<6}  {'Type':<30}  {'Title':<28}  Key values")
    print(f"  {'-'*6}  {'-'*30}  {'-'*28}  {'-'*40}")

    for node_id in sorted(nodes.keys(), key=lambda x: int(x) if x.isdigit() else 0):
        node = nodes[node_id]
        ct    = node.get("class_type", "?")
        title = node.get("_meta", {}).get("title", "")
        summary = summarise(node.get("inputs", {}))
        print(f"  {node_id:<6}  {ct:<30}  {title:<28}  {summary}")

    print()

if __name__ == "__main__":
    main()
