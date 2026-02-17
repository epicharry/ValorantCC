from PIL import Image, ImageDraw, ImageFont
import math, os, tempfile, subprocess, sys

SCALE = 5
CANVAS_SIZE = 300
CENTER = CANVAS_SIZE // 2
BG_COLOR = (18, 18, 22, 255)
GRID_COLOR = (40, 40, 48, 255)
GRID_DOT_COLOR = (55, 55, 65, 255)


def _draw_background(img):
    draw = ImageDraw.Draw(img, "RGBA")
    for x in range(0, CANVAS_SIZE, 20):
        draw.line([(x, 0), (x, CANVAS_SIZE)], fill=GRID_COLOR, width=1)
    for y in range(0, CANVAS_SIZE, 20):
        draw.line([(0, y), (CANVAS_SIZE, y)], fill=GRID_COLOR, width=1)
    r = 2
    draw.ellipse([CENTER - r, CENTER - r, CENTER + r, CENTER + r], fill=GRID_DOT_COLOR)


def _resolve_color(section):
    if section.get("bUseCustomColor", False):
        c = section["colorCustom"]
    else:
        c = section["color"]
    return (c["r"], c["g"], c["b"], c["a"])


def _draw_arms(draw, lines_cfg, color, outline_expand=0):
    if not lines_cfg.get("bShowLines", False):
        return

    s = SCALE
    e = outline_expand * s

    thickness = lines_cfg["lineThickness"] * s + e * 2
    length = lines_cfg["lineLength"] * s + e
    offset = max(0, lines_cfg["lineOffset"] * s - e)
    opacity = lines_cfg.get("opacity", 1)
    alpha = int(opacity * color[3])
    c = (*color[:3], alpha)

    if thickness < 1 or length < 1:
        return

    ht = thickness / 2
    cx, cy = CENTER, CENTER

    draw.rectangle([cx + offset, cy - ht, cx + offset + length, cy + ht], fill=c)
    draw.rectangle([cx - offset - length, cy - ht, cx - offset, cy + ht], fill=c)

    vert_len = length
    if lines_cfg.get("bAllowVertScaling", False):
        vert_len = lines_cfg["lineLengthVertical"] * s + e

    draw.rectangle([cx - ht, cy + offset, cx + ht, cy + offset + vert_len], fill=c)
    draw.rectangle([cx - ht, cy - offset - vert_len, cx + ht, cy - offset], fill=c)


def _draw_dot(draw, section, color, outline_expand=0):
    if not section.get("bDisplayCenterDot", False):
        return

    s = SCALE
    e = outline_expand * s
    size = section["centerDotSize"] * s + e * 2
    opacity = section.get("centerDotOpacity", 1)
    alpha = int(opacity * color[3])
    c = (*color[:3], alpha)

    if size < 1:
        return

    hr = size / 2
    cx, cy = CENTER, CENTER
    draw.ellipse([cx - hr, cy - hr, cx + hr, cy + hr], fill=c)


def _draw_section(img, section):
    color = _resolve_color(section)

    has_outline = section.get("bHasOutline", False)
    outline_thick = section.get("outlineThickness", 1)

    if has_outline and outline_thick > 0:
        oc = section.get("outlineColor", {"r": 0, "g": 0, "b": 0, "a": 255})
        o_opacity = section.get("outlineOpacity", 0.5)
        o_alpha = max(1, int(o_opacity * 255))
        outline_color = (oc["r"], oc["g"], oc["b"], o_alpha)

        outline_layer = Image.new("RGBA", (CANVAS_SIZE, CANVAS_SIZE), (0, 0, 0, 0))
        od = ImageDraw.Draw(outline_layer, "RGBA")
        _draw_arms(od, section.get("innerLines", {}), outline_color, outline_expand=outline_thick)
        _draw_arms(od, section.get("outerLines", {}), outline_color, outline_expand=outline_thick)
        _draw_dot(od, section, outline_color, outline_expand=outline_thick)
        img.alpha_composite(outline_layer)

    main_layer = Image.new("RGBA", (CANVAS_SIZE, CANVAS_SIZE), (0, 0, 0, 0))
    md = ImageDraw.Draw(main_layer, "RGBA")
    _draw_arms(md, section.get("innerLines", {}), color)
    _draw_arms(md, section.get("outerLines", {}), color)
    _draw_dot(md, section, color)
    img.alpha_composite(main_layer)


def _draw_label(img, text):
    draw = ImageDraw.Draw(img, "RGBA")
    try:
        font = ImageFont.truetype("arial.ttf", 14)
    except (OSError, IOError):
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
        except (OSError, IOError):
            font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    x = (CANVAS_SIZE - tw) // 2
    y = CANVAS_SIZE - 24

    draw.rectangle([x - 6, y - 2, x + tw + 6, y + 18], fill=(0, 0, 0, 160))
    draw.text((x, y), text, fill=(220, 220, 220, 255), font=font)


def render_crosshair(profile, show_label=True):
    img = Image.new("RGBA", (CANVAS_SIZE, CANVAS_SIZE), BG_COLOR)
    _draw_background(img)

    primary = profile.get("primary", {})
    if not primary.get("bHideCrosshair", False):
        _draw_section(img, primary)

    if show_label:
        name = profile.get("profileName", "Unnamed")
        _draw_label(img, name)

    return img


def render_grid(profiles, columns=3):
    count = len(profiles)
    rows = math.ceil(count / columns)
    pad = 4
    cell = CANVAS_SIZE + pad
    grid_w = columns * cell + pad
    grid_h = rows * cell + pad

    grid_img = Image.new("RGBA", (grid_w, grid_h), (10, 10, 14, 255))

    for i, profile in enumerate(profiles):
        col = i % columns
        row = i // columns
        tile = render_crosshair(profile, show_label=True)
        x = pad + col * cell
        y = pad + row * cell
        grid_img.paste(tile, (x, y))

    return grid_img


def show_image(img):
    tmp = os.path.join(tempfile.gettempdir(), "crosshair_preview.png")
    img.save(tmp, "PNG")

    if sys.platform == "win32":
        os.startfile(tmp)
    elif sys.platform == "darwin":
        subprocess.Popen(["open", tmp])
    else:
        subprocess.Popen(["xdg-open", tmp])

    print(f"  Preview saved to: {tmp}")


def save_image(img, path):
    img.save(path, "PNG")
    print(f"  Image saved to: {path}")
