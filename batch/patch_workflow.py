#!/usr/bin/env python3
"""
patch_workflow.py — override specific node inputs in a ComfyUI workflow JSON.

Useful for iterating on seeds, LoRA strengths, step counts, etc. without
maintaining separate workflow files for each variant.

Usage:
  python3 batch/patch_workflow.py <workflow.json> [NODE_ID.field=value ...]

  # Print patched workflow to stdout
  python3 batch/patch_workflow.py image_flux2_text_to_image.json 25.seed=400

  # Write to a temp file and submit
  python3 batch/patch_workflow.py flux_lora_workflow.json 42.strength=1.1 > /tmp/wf.json
  python3 batch/batch_comfy.py /tmp/wf.json runs.txt --wait

  # Pipe directly (Linux /dev/stdin)
  python3 batch/patch_workflow.py workflow.json 25.seed=400 | \\
      python3 batch/batch_comfy.py /dev/stdin runs.txt --wait

  # Multiple overrides
  python3 batch/patch_workflow.py workflow.json 25.seed=400 15.steps=20 42.strength=0.9

  # List node IDs and their inputs (for finding what to patch)
  python3 batch/patch_workflow.py workflow.json --list-nodes

Value type coercion:
  Values are cast to match the existing field type (int, float, bool, str).
  To force a string even if the current value is numeric, quote it:
    25.filename_prefix=my_output
"""

import argparse
import json
import sys


def coerce(new_val: str, existing):
    """Cast new_val string to match the type of the existing value."""
    if isinstance(existing, bool):
        return new_val.lower() in ("1", "true", "yes")
    if isinstance(existing, int):
        return int(new_val)
    if isinstance(existing, float):
        return float(new_val)
    return new_val


def parse_override(spec: str):
    """Parse 'NODE_ID.field=value' into (node_id, field, value_str)."""
    if "=" not in spec:
        sys.exit(f"Error: override {spec!r} must be in NODE_ID.field=value format")
    lhs, value_str = spec.split("=", 1)
    if "." not in lhs:
        sys.exit(f"Error: override {spec!r} must be in NODE_ID.field=value format")
    node_id, field = lhs.split(".", 1)
    return node_id, field, value_str


def apply_overrides(workflow: dict, overrides: list[tuple]) -> dict:
    for node_id, field, value_str in overrides:
        if node_id not in workflow:
            sys.exit(f"Error: node {node_id!r} not found in workflow")
        inputs = workflow[node_id].get("inputs", {})
        if field not in inputs:
            available = ", ".join(sorted(inputs.keys()))
            sys.exit(
                f"Error: node {node_id!r} has no input field {field!r}\n"
                f"  Available: {available}"
            )
        existing = inputs[field]
        inputs[field] = coerce(value_str, existing)
    return workflow


def list_nodes(workflow: dict):
    for node_id, node in sorted(workflow.items(), key=lambda x: x[0]):
        ct = node.get("class_type", "?")
        title = node.get("_meta", {}).get("title", "")
        inputs = node.get("inputs", {})
        label = f"  [{node_id:>4}] {ct}"
        if title:
            label += f"  ({title!r})"
        print(label)
        for field, val in inputs.items():
            # Skip linked inputs (they're lists like [node_id, output_slot])
            if isinstance(val, list):
                continue
            preview = repr(val)
            if len(preview) > 80:
                preview = preview[:77] + "..."
            print(f"           {field} = {preview}")


def main():
    parser = argparse.ArgumentParser(
        description="Patch ComfyUI workflow node inputs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("workflow", help="Workflow JSON in API format")
    parser.add_argument(
        "overrides",
        nargs="*",
        metavar="NODE_ID.field=value",
        help="One or more field overrides",
    )
    parser.add_argument(
        "--list-nodes", "-l",
        action="store_true",
        help="Print all nodes and their patchable inputs, then exit",
    )
    parser.add_argument(
        "--output", "-o",
        metavar="FILE",
        help="Write output to FILE instead of stdout",
    )
    args = parser.parse_args()

    with open(args.workflow) as f:
        workflow = json.load(f)

    if "nodes" in workflow and "links" in workflow:
        sys.exit(
            "Error: this looks like a UI-format workflow, not API format.\n"
            "In ComfyUI: Settings → Enable Dev Mode Options → Save (API Format)"
        )

    if args.list_nodes:
        list_nodes(workflow)
        return

    if not args.overrides:
        parser.print_help()
        sys.exit(0)

    overrides = [parse_override(s) for s in args.overrides]
    workflow = apply_overrides(workflow, overrides)

    out = json.dumps(workflow, indent=2)
    if args.output:
        with open(args.output, "w") as f:
            f.write(out)
        print(f"Written to {args.output}", file=sys.stderr)
    else:
        print(out)


if __name__ == "__main__":
    main()
