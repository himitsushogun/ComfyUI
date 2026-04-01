"""
Post-process eyeshadow color transfer using PIL only.

Uses the BiSeNet iris mask (from ComfyUI MaskDebug output) to locate each eye
precisely, then shifts that mask upward to cover the eyelid/eyeshadow area.
Blends a target pink onto the eyelid region while preserving shadow depth.

Usage: python3 batch/apply_eye_color.py <input> <output> [iris_mask]
"""

import sys
from PIL import Image, ImageFilter, ImageChops

def apply_eyeshadow(source_path, output_path, iris_mask_path,
                    target_rgb=(210, 85, 140),
                    blend_strength=0.60,
                    upward_shift_frac=0.025,
                    expand_frac=0.02,
                    brow_ceiling_frac=0.28):
    img = Image.open(source_path).convert('RGB')
    w, h = img.size

    # Load the precise iris mask from ComfyUI face parsing
    iris = Image.open(iris_mask_path).convert('L').resize((w, h), Image.LANCZOS)

    # Shift mask upward to cover eyelid above the iris
    shift_px = int(h * upward_shift_frac)
    expand_px = int(h * expand_frac)

    # Translate upward
    shifted = Image.new('L', (w, h), 0)
    shifted.paste(iris, (0, -shift_px))

    # Small expansion for eyelid width
    for _ in range(max(1, expand_px // 4)):
        shifted = shifted.filter(ImageFilter.MaxFilter(5))

    # Soft blur
    shifted = shifted.filter(ImageFilter.GaussianBlur(radius=6))

    # Hard ceiling: zero out everything above brow_ceiling_frac of image height
    # so the mask can never bleed into the forehead/hair
    ceiling_y = int(h * brow_ceiling_frac)
    pixels = list(shifted.getdata())
    for i in range(len(pixels)):
        y = i // w
        if y < ceiling_y:
            pixels[i] = 0
    shifted.putdata(pixels)

    # Scale blend strength
    mask = shifted.point(lambda p: int(p * blend_strength))

    # Pink overlay
    pink = Image.new('RGB', (w, h), target_rgb)

    # Composite: mask controls how much pink replaces original
    result = Image.composite(pink, img, mask)

    result.save(output_path, quality=95)
    print(f"Saved → {output_path}")


if __name__ == '__main__':
    src       = sys.argv[1] if len(sys.argv) > 1 else 'output/FaceRefine__00020_.png'
    out       = sys.argv[2] if len(sys.argv) > 2 else 'output/EyeColor__00003_.png'
    iris_mask = sys.argv[3] if len(sys.argv) > 3 else 'output/MaskDebug__00012_.png'
    apply_eyeshadow(src, out, iris_mask)
