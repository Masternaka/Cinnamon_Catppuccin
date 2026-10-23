#!/usr/bin/env python3
"""Build the Catppuccin Cinnamon themes from the official palette.

Only the Python standard library is required. The script produces:

  dist/Catppuccin-<Flavor>/
      index.theme
      cinnamon/cinnamon.css
      cinnamon/thumbnail.png
      cinnamon/<svg assets + corner-ripple.png>
      LICENSE
  dist/Catppuccin-<Flavor>.zip
  dist/Catppuccin-Cinnamon-all-flavors.zip
  previews/Catppuccin-<Flavor>.svg
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import shutil
import struct
import sys
import time
import zipfile
import zlib
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
PALETTE_PATH = ROOT / "palette.json"
CSS_TEMPLATE_PATH = ROOT / "src" / "cinnamon.css.in"
INDEX_TEMPLATE_PATH = ROOT / "src" / "index.theme.in"
OVERVIEW_TEMPLATE_PATH = ROOT / "src" / "overview.html.in"
DIST_DIR = ROOT / "dist"
PREVIEW_DIR = ROOT / "previews"

TOKEN_RE = re.compile(r"@([a-z0-9_]+)@")
STRAY_TOKEN_RE = re.compile(r"@[A-Za-z0-9_-]+@")
HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")

# Archives must be byte-identical between runs so that the tracked dist/*.zip
# files only change when the theme itself changes. ZipInfo date_time is limited
# to 1980-2107; SOURCE_DATE_EPOCH is honoured when set.
DEFAULT_ZIP_DATE_TIME = (1980, 1, 1, 0, 0, 0)

ALPHAS = [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 60, 70, 80, 85, 90, 95]

# WCAG 2.1: 4.5:1 for normal text, 3:1 for large text and UI boundaries.
WCAG_TEXT = 4.5

# Cinnamon displays cinnamon/thumbnail.png at 125 px wide; the Mint themes use a
# 247x60 strip, so the generated vignette follows the same format.
THUMBNAIL_SIZE = (247, 60)

ACCENT_NAMES = [
    "rosewater",
    "flamingo",
    "pink",
    "mauve",
    "red",
    "maroon",
    "peach",
    "yellow",
    "green",
    "teal",
    "sky",
    "sapphire",
    "blue",
    "lavender",
]

# 5x7 bitmap font used for the generated PNG thumbnails.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("11111", "00100", "00100", "00100", "00100", "00100", "11111"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    "3": ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "10000", "11110", "00001", "00001", "11110"),
    "6": ("01110", "10000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00001", "01110"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
}


# ---------------------------------------------------------------------------
# Colors
# ---------------------------------------------------------------------------


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)


def rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return "#{:02x}{:02x}{:02x}".format(*rgb)


def rgba(value: str, alpha: float) -> str:
    r, g, b = hex_to_rgb(value)
    return f"rgba({r}, {g}, {b}, {alpha:g})"


def mix(first: str, second: str, weight: float) -> str:
    a = hex_to_rgb(first)
    b = hex_to_rgb(second)
    return rgb_to_hex(
        tuple(round(x * (1.0 - weight) + y * weight) for x, y in zip(a, b))
    )


def relative_luminance(value: str) -> float:
    def channel(component: int) -> float:
        component = component / 255
        if component <= 0.04045:
            return component / 12.92
        return ((component + 0.055) / 1.055) ** 2.4

    red, green, blue = hex_to_rgb(value)
    return 0.2126 * channel(red) + 0.7152 * channel(green) + 0.0722 * channel(blue)


def contrast_ratio(first: str, second: str) -> float:
    """WCAG 2.1 contrast ratio between two opaque colors."""
    lighter = max(relative_luminance(first), relative_luminance(second))
    darker = min(relative_luminance(first), relative_luminance(second))
    return (lighter + 0.05) / (darker + 0.05)


def rgb_to_hsl(value: str) -> tuple[float, float, float]:
    red, green, blue = (component / 255 for component in hex_to_rgb(value))
    highest, lowest = max(red, green, blue), min(red, green, blue)
    lightness = (highest + lowest) / 2
    if highest == lowest:
        return 0.0, 0.0, lightness
    delta = highest - lowest
    saturation = delta / (2 - highest - lowest if lightness > 0.5 else highest + lowest)
    if highest == red:
        hue = ((green - blue) / delta) % 6
    elif highest == green:
        hue = (blue - red) / delta + 2
    else:
        hue = (red - green) / delta + 4
    return hue * 60, saturation, lightness


def hsl_to_hex(hue: float, saturation: float, lightness: float) -> str:
    chroma = (1 - abs(2 * lightness - 1)) * saturation
    secondary = chroma * (1 - abs((hue / 60) % 2 - 1))
    match = lightness - chroma / 2
    sextant = int(hue // 60) % 6
    red, green, blue = [
        (chroma, secondary, 0.0),
        (secondary, chroma, 0.0),
        (0.0, chroma, secondary),
        (0.0, secondary, chroma),
        (secondary, 0.0, chroma),
        (chroma, 0.0, secondary),
    ][sextant]
    return rgb_to_hex(
        tuple(
            round(min(max(component + match, 0.0), 1.0) * 255)
            for component in (red, green, blue)
        )
    )


def ensure_contrast(
    color: str, backgrounds: list[str], fallback: str, target: float = WCAG_TEXT
) -> str:
    """Return `color` with its lightness adjusted until it reaches `target`.

    The Catppuccin accents are pastel, so drawing text with them on the light
    flavors falls below the WCAG ratio. Only the lightness changes: the hue and
    the saturation of the official palette color are kept, so a warning stays
    amber instead of turning grey. Fills, borders and indicators keep using the
    untouched palette color; only foreground tokens go through here.
    """
    if all(contrast_ratio(color, background) >= target for background in backgrounds):
        return color

    hue, saturation, lightness = rgb_to_hsl(color)
    darken = relative_luminance(backgrounds[0]) > relative_luminance(color)
    for step in range(1, 101):
        factor = step / 100
        if darken:
            candidate_lightness = lightness * (1 - factor)
        else:
            candidate_lightness = lightness + (1 - lightness) * factor
        candidate = hsl_to_hex(hue, saturation, candidate_lightness)
        if all(contrast_ratio(candidate, background) >= target for background in backgrounds):
            return candidate
    return fallback


def on_accent_color(accent: str, base: str, text: str, target: float = WCAG_TEXT) -> str:
    """Return the most readable text color for a background filled with `accent`.

    The Catppuccin style guide recommends Base on the accent. That holds for the
    dark flavors and for most accents, but a mid-tone or pale accent on the light
    flavors needs the better of Base/Text, with its lightness pushed until the
    pair is readable. Base is only left untouched when it already qualifies.
    """
    if contrast_ratio(base, accent) >= target:
        return base
    adjusted = [
        ensure_contrast(candidate, [accent], fallback=candidate, target=target)
        for candidate in (base, text)
    ]
    best = max(adjusted, key=lambda candidate: contrast_ratio(candidate, accent))
    if contrast_ratio(best, accent) >= target:
        return best
    return max(("#ffffff", "#000000"), key=lambda candidate: contrast_ratio(candidate, accent))


def flavor_tokens(flavor: dict, accent_name: str) -> dict[str, str]:
    colors = flavor["colors"]
    dark = bool(flavor["dark"])
    accent = colors[accent_name]

    tokens: dict[str, str] = dict(colors)
    tokens["flavor"] = flavor["name"]
    tokens["flavor_slug"] = flavor["folder"]
    tokens["accent"] = accent
    tokens["accent_hover"] = mix(accent, colors["text"] if dark else colors["base"], 0.15)
    tokens["accent_active"] = mix(accent, colors["crust"] if dark else colors["text"], 0.15)
    tokens["on_accent"] = on_accent_color(accent, colors["base"], colors["text"])

    # Structural colors.
    tokens["panel"] = colors["crust"]
    tokens["panel_bg"] = colors["crust"]
    tokens["panel_border"] = colors["surface0"]
    tokens["menu_bg"] = colors["base"]
    tokens["menu_border"] = colors["surface0"]
    tokens["sidebar_bg"] = colors["mantle"]
    tokens["entry_bg"] = colors["surface0"]
    tokens["entry_border"] = colors["surface1"]
    tokens["tooltip_bg"] = colors["mantle"]
    tokens["notification_bg"] = colors["mantle"]
    tokens["osd_bg"] = rgba(colors["base"], 0.96)

    # Interaction colors.
    tokens["hover"] = colors["surface0"]
    tokens["active"] = colors["surface1"]
    tokens["pressed"] = colors["surface2"]
    tokens["insensitive"] = colors["overlay1"]
    tokens["selection_bg"] = rgba(colors["overlay2"], 0.3)

    # Semantic colors.
    tokens["success"] = colors["green"]
    tokens["warning"] = colors["yellow"]
    tokens["error"] = colors["red"]
    tokens["info"] = colors["teal"]

    # Readable foreground variants. The official accents are pastel, so drawing
    # text with them on the light flavors falls below the WCAG ratio; these
    # tokens darken (or lighten, on dark flavors) toward `text` just enough.
    # Fills, borders and indicators keep the untouched palette colors above.
    surfaces = [colors["base"], colors["crust"]]
    tokens["text_success"] = ensure_contrast(colors["green"], surfaces, colors["text"])
    tokens["text_warning"] = ensure_contrast(colors["yellow"], surfaces, colors["text"])
    tokens["text_error"] = ensure_contrast(colors["red"], surfaces, colors["text"])
    tokens["text_info"] = ensure_contrast(colors["teal"], surfaces, colors["text"])
    tokens["link"] = ensure_contrast(colors["blue"], surfaces, colors["text"])
    tokens["link_hover"] = ensure_contrast(colors["sky"], surfaces, colors["text"])

    # Shadows and scrims.
    tokens["shadow"] = rgba("#000000", 0.45 if dark else 0.15)
    tokens["shadow_soft"] = rgba("#000000", 0.3 if dark else 0.08)
    tokens["backdrop"] = rgba("#000000", 0.5 if dark else 0.3)

    # Every solid color also gets an alpha variant: @text_a80@, @accent_a25@...
    alpha_tokens: dict[str, str] = {}
    for name, value in list(tokens.items()):
        if HEX_RE.match(value):
            for alpha in ALPHAS:
                alpha_tokens[f"{name}_a{alpha:02d}"] = rgba(value, alpha / 100.0)
    tokens.update(alpha_tokens)
    return tokens


def substitute(text: str, tokens: dict[str, str], label: str) -> str:
    missing: set[str] = set()

    def replace(match: re.Match[str]) -> str:
        name = match.group(1)
        if name not in tokens:
            missing.add(name)
            return match.group(0)
        return tokens[name]

    result = TOKEN_RE.sub(replace, text)
    if missing:
        names = ", ".join("@" + name + "@" for name in sorted(missing))
        raise ValueError(f"{label}: unresolved tokens: {names}")
    return result


def contrast_issues(flavor: dict, tokens: dict[str, str]) -> list[str]:
    """List foreground/background pairs below the WCAG normal-text ratio."""
    pairs = [
        ("Texte", "text", "base"),
        ("Texte sur panneau", "text", "crust"),
        ("Texte secondaire", "subtext0", "base"),
        ("Accent lisible", "text_info", "base"),
        ("Succès", "text_success", "base"),
        ("Avertissement", "text_warning", "base"),
        ("Erreur", "text_error", "base"),
        ("Succès sur panneau", "text_success", "crust"),
        ("Avertissement sur panneau", "text_warning", "crust"),
        ("Erreur sur panneau", "text_error", "crust"),
        ("Lien", "link", "base"),
        ("Lien survolé", "link_hover", "base"),
        ("Lien sur panneau", "link", "crust"),
        ("Texte sur accent", "on_accent", "accent"),
    ]
    issues: list[str] = []
    for label, foreground, background in pairs:
        ratio = contrast_ratio(tokens[foreground], tokens[background])
        if ratio < WCAG_TEXT:
            issues.append(
                f"{flavor['name']}: {label} ({foreground} sur {background}) "
                f"= {ratio:.2f}:1 < {WCAG_TEXT:g}:1"
            )
    return issues


# ---------------------------------------------------------------------------
# Minimal PNG canvas (no Pillow dependency)
# ---------------------------------------------------------------------------


class Canvas:
    def __init__(self, width: int, height: int, background: str | None = None):
        self.width = width
        self.height = height
        self.pixels = bytearray(width * height * 4)
        if background is not None:
            self.fill_rect(0, 0, width, height, background)

    def blend(self, x: int, y: int, color: str, alpha: float) -> None:
        if alpha <= 0 or x < 0 or y < 0 or x >= self.width or y >= self.height:
            return
        alpha = min(alpha, 1.0)
        r, g, b = hex_to_rgb(color)
        index = (y * self.width + x) * 4
        dst_a = self.pixels[index + 3] / 255.0
        out_a = alpha + dst_a * (1.0 - alpha)
        if out_a <= 0:
            return
        for offset, src in enumerate((r, g, b)):
            dst = self.pixels[index + offset]
            self.pixels[index + offset] = round(
                (src * alpha + dst * dst_a * (1.0 - alpha)) / out_a
            )
        self.pixels[index + 3] = round(out_a * 255)

    def fill_rect(self, x: float, y: float, w: float, h: float, color: str, alpha: float = 1.0) -> None:
        x0 = max(0, int(math.floor(x)))
        y0 = max(0, int(math.floor(y)))
        x1 = min(self.width, int(math.ceil(x + w)))
        y1 = min(self.height, int(math.ceil(y + h)))
        for py in range(y0, y1):
            for px in range(x0, x1):
                self.blend(px, py, color, alpha)

    def fill_rounded_rect(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        radius: float,
        color: str,
        alpha: float = 1.0,
    ) -> None:
        radius = max(0.0, min(radius, min(w, h) / 2.0))
        x0 = max(0, int(math.floor(x)))
        y0 = max(0, int(math.floor(y)))
        x1 = min(self.width, int(math.ceil(x + w)))
        y1 = min(self.height, int(math.ceil(y + h)))
        cx = x + w / 2.0
        cy = y + h / 2.0
        hw = w / 2.0 - radius
        hh = h / 2.0 - radius
        for py in range(y0, y1):
            for px in range(x0, x1):
                dx = abs(px + 0.5 - cx) - hw
                dy = abs(py + 0.5 - cy) - hh
                outside = math.hypot(max(dx, 0.0), max(dy, 0.0))
                inside = min(max(dx, dy), 0.0)
                distance = outside + inside - radius
                coverage = min(max(0.5 - distance, 0.0), 1.0)
                if coverage > 0:
                    self.blend(px, py, color, alpha * coverage)

    def fill_circle(self, cx: float, cy: float, radius: float, color: str, alpha: float = 1.0) -> None:
        x0 = max(0, int(math.floor(cx - radius - 1)))
        y0 = max(0, int(math.floor(cy - radius - 1)))
        x1 = min(self.width, int(math.ceil(cx + radius + 1)))
        y1 = min(self.height, int(math.ceil(cy + radius + 1)))
        for py in range(y0, y1):
            for px in range(x0, x1):
                distance = math.hypot(px + 0.5 - cx, py + 0.5 - cy) - radius
                coverage = min(max(0.5 - distance, 0.0), 1.0)
                if coverage > 0:
                    self.blend(px, py, color, alpha * coverage)

    def draw_text(self, x: int, y: int, text: str, scale: int, color: str, alpha: float = 1.0) -> int:
        cursor = x
        for character in text.upper():
            glyph = FONT.get(character, FONT[" "])
            for row, bits in enumerate(glyph):
                for column, bit in enumerate(bits):
                    if bit == "1":
                        self.fill_rect(
                            cursor + column * scale,
                            y + row * scale,
                            scale,
                            scale,
                            color,
                            alpha,
                        )
            cursor += (5 + 1) * scale
        return cursor

    def write_png(self, path: Path) -> None:
        raw = bytearray()
        for y in range(self.height):
            raw.append(0)
            raw.extend(self.pixels[y * self.width * 4 : (y + 1) * self.width * 4])

        def chunk(tag: bytes, data: bytes) -> bytes:
            return (
                struct.pack(">I", len(data))
                + tag
                + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
            )

        header = struct.pack(">IIBBBBB", self.width, self.height, 8, 6, 0, 0, 0)
        png = (
            b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", header)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + chunk(b"IEND", b"")
        )
        path.write_bytes(png)


# ---------------------------------------------------------------------------
# Theme assets
# ---------------------------------------------------------------------------


def write_svg(path: Path, width: int, height: int, body: str) -> None:
    path.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">\n{body}\n</svg>\n',
        encoding="utf-8",
    )


def write_assets(asset_dir: Path, tokens: dict[str, str]) -> None:
    accent = tokens["accent"]
    on_accent = tokens["on_accent"]
    text = tokens["text"]
    surface0 = tokens["surface0"]
    surface1 = tokens["surface1"]
    surface2 = tokens["surface2"]
    overlay1 = tokens["overlay1"]
    overlay2 = tokens["overlay2"]
    red = tokens["red"]

    write_svg(
        asset_dir / "checkbox-off.svg",
        20,
        20,
        f'<rect x="1.5" y="1.5" width="17" height="17" rx="4" '
        f'fill="none" stroke="{overlay1}" stroke-width="2"/>',
    )
    write_svg(
        asset_dir / "checkbox.svg",
        20,
        20,
        f'<rect x="1" y="1" width="18" height="18" rx="4" '
        f'fill="{accent}" stroke="{accent}" stroke-width="1"/>'
        f'<path d="M5.5 10.2 L8.6 13.3 L14.8 6.6" fill="none" '
        f'stroke="{on_accent}" stroke-width="2.2" stroke-linecap="round" '
        f'stroke-linejoin="round"/>',
    )
    write_svg(
        asset_dir / "radio-off.svg",
        20,
        20,
        f'<circle cx="10" cy="10" r="8.5" fill="none" '
        f'stroke="{overlay1}" stroke-width="2"/>',
    )
    write_svg(
        asset_dir / "radio.svg",
        20,
        20,
        f'<circle cx="10" cy="10" r="8.5" fill="{accent}"/>'
        f'<circle cx="10" cy="10" r="4" fill="{on_accent}"/>',
    )
    write_svg(
        asset_dir / "toggle-off.svg",
        46,
        26,
        f'<rect x="1" y="1" width="44" height="24" rx="12" fill="{surface1}"/>'
        f'<circle cx="13" cy="13" r="8" fill="{overlay2}"/>',
    )
    write_svg(
        asset_dir / "toggle-on.svg",
        46,
        26,
        f'<rect x="1" y="1" width="44" height="24" rx="12" fill="{accent}"/>'
        f'<circle cx="33" cy="13" r="8" fill="{on_accent}"/>',
    )

    for direction, path in (
        ("left", "M10.2 3.2 L5.2 8 L10.2 12.8"),
        ("right", "M5.8 3.2 L10.8 8 L5.8 12.8"),
    ):
        write_svg(
            asset_dir / f"calendar-arrow-{direction}.svg",
            16,
            16,
            f'<path d="{path}" fill="none" stroke="{text}" stroke-width="2" '
            f'stroke-linecap="round" stroke-linejoin="round"/>',
        )
        write_svg(
            asset_dir / f"calendar-arrow-{direction}-hover.svg",
            16,
            16,
            f'<path d="{path}" fill="none" stroke="{accent}" stroke-width="2" '
            f'stroke-linecap="round" stroke-linejoin="round"/>',
        )

    write_svg(
        asset_dir / "close.svg",
        26,
        26,
        f'<circle cx="13" cy="13" r="12" fill="{surface0}" stroke="{surface1}" '
        f'stroke-width="1"/>'
        f'<path d="M9.5 9.5 L16.5 16.5 M16.5 9.5 L9.5 16.5" '
        f'stroke="{text}" stroke-width="2" stroke-linecap="round"/>',
    )
    write_svg(
        asset_dir / "add-workspace.svg",
        35,
        200,
        f'<rect x="2" y="2" width="31" height="196" rx="10" fill="{surface0}" '
        f'stroke="{surface1}" stroke-width="1"/>'
        f'<path d="M17.5 20 L17.5 34 M10.5 27 L24.5 27" stroke="{overlay1}" '
        f'stroke-width="2.5" stroke-linecap="round"/>',
    )
    write_svg(
        asset_dir / "add-workspace-hover.svg",
        35,
        200,
        f'<rect x="2" y="2" width="31" height="196" rx="10" fill="{accent}" '
        f'fill-opacity="0.18" stroke="{accent}" stroke-width="1.5"/>'
        f'<path d="M17.5 20 L17.5 34 M10.5 27 L24.5 27" stroke="{accent}" '
        f'stroke-width="2.5" stroke-linecap="round"/>',
    )
    write_svg(
        asset_dir / "trash-icon.svg",
        400,
        120,
        f'<rect x="1" y="1" width="398" height="118" rx="16" fill="{red}" '
        f'fill-opacity="0.12" stroke="{red}" stroke-opacity="0.45" stroke-width="1.5"/>'
        f'<path d="M178 44 L222 44 M186 36 L214 36 M182 50 L186 94 L214 94 L218 50" '
        f'fill="none" stroke="{red}" stroke-width="3" stroke-linecap="round" '
        f'stroke-linejoin="round"/>'
        f'<path d="M193 58 L195 84 M207 58 L205 84" stroke="{red}" '
        f'stroke-width="2" stroke-linecap="round"/>',
    )

    # Launch ripple used by Cinnamon when a launcher is activated.
    ripple = Canvas(104, 104)
    for y in range(104):
        for x in range(104):
            distance = math.hypot(x + 0.5 - 52.0, y + 0.5 - 52.0)
            alpha = max(0.0, 1.0 - abs(distance - 38.0) / 12.0) * 0.55
            alpha += max(0.0, 1.0 - abs(distance - 24.0) / 9.0) * 0.3
            if alpha > 0:
                ripple.blend(x, y, accent, min(alpha, 1.0))
    ripple.write_png(asset_dir / "corner-ripple.png")


def make_thumbnail(path: Path, tokens: dict[str, str], flavor: dict) -> None:
    """Draw the 247x60 strip shown by the Cinnamon theme chooser.

    The chooser scales the thumbnail to 125 px wide, like the Mint themes, so the
    strip stays a readable overview of the panel and the application menu.
    """
    width, height = THUMBNAIL_SIZE
    base = tokens["base"]
    mantle = tokens["mantle"]
    crust = tokens["crust"]
    surface0 = tokens["surface0"]
    surface1 = tokens["surface1"]
    surface2 = tokens["surface2"]
    text = tokens["text"]
    subtext0 = tokens["subtext0"]
    overlay0 = tokens["overlay0"]
    accent = tokens["accent"]
    on_accent = tokens["on_accent"]

    canvas = Canvas(width, height, base)

    # Panel: launcher, name, flavor and clock.
    canvas.fill_rect(0, 0, width, 16, crust)
    canvas.fill_rect(0, 16, width, 1, surface0)
    canvas.fill_circle(9, 8, 5, accent)
    canvas.draw_text(7, 5, "C", 1, on_accent)
    canvas.draw_text(18, 5, "CATPPUCCIN", 1, text)
    name = flavor["name"].upper().replace("É", "E")
    canvas.draw_text(78, 5, name, 1, accent)
    canvas.fill_circle(140, 8, 3, surface2)
    canvas.fill_circle(152, 8, 3, surface2)
    canvas.fill_circle(164, 8, 3, surface2)
    canvas.draw_text(208, 5, "12:30", 1, subtext0)

    # Application menu.
    canvas.fill_rounded_rect(6, 22, 235, 34, 7, "#000000", 0.22)
    canvas.fill_rounded_rect(5, 20, 235, 34, 7, surface1)
    canvas.fill_rounded_rect(6, 21, 233, 32, 6, base)

    canvas.fill_rounded_rect(6, 21, 56, 32, 6, mantle)
    canvas.fill_rect(56, 21, 8, 32, mantle)
    canvas.fill_rect(63, 21, 1, 32, surface0)
    canvas.fill_circle(17, 29, 6, accent)
    canvas.draw_text(15, 26, "M", 1, on_accent)
    canvas.draw_text(27, 26, "MINT", 1, text)
    canvas.fill_rounded_rect(11, 38, 44, 6, 3, surface0)
    canvas.fill_circle(15, 41, 1.8, accent)
    canvas.fill_rect(20, 40, 26, 2, subtext0)
    canvas.fill_rounded_rect(11, 46, 44, 6, 3, surface0)
    canvas.fill_circle(15, 49, 1.8, tokens["green"])
    canvas.fill_rect(20, 48, 20, 2, subtext0)

    app_rows = [
        (tokens["mauve"], 40, 26),
        (tokens["green"], 34, 20),
        (tokens["peach"], 44, 30),
        (tokens["blue"], 28, 18),
    ]
    for index, (color, label_width, sub_width) in enumerate(app_rows):
        y = 23 + index * 8
        if index == 0:
            canvas.fill_rounded_rect(68, y - 1, 168, 9, 3, surface0)
        canvas.fill_rounded_rect(72, y, 7, 7, 2, color)
        canvas.fill_rect(84, y + 1, label_width, 2, text, 0.9)
        canvas.fill_rect(84, y + 5, sub_width, 1.5, overlay0)

    canvas.write_png(path)


def make_overview(palette: dict, preview_dir: Path, output: Path, accent_name: str) -> None:
    template = OVERVIEW_TEMPLATE_PATH.read_text(encoding="utf-8")
    chips = [
        "rosewater",
        "mauve",
        "red",
        "peach",
        "yellow",
        "green",
        "teal",
        "blue",
        "lavender",
    ]
    cards = []
    for slug, flavor in palette["flavors"].items():
        colors = flavor["colors"]
        svg = (preview_dir / f"{flavor['folder']}.svg").read_text(encoding="utf-8")
        svg = re.sub(r"^<\?xml[^>]*\?>\s*", "", svg)
        svg = svg.replace('id="shadow"', f'id="shadow-{slug}"')
        svg = svg.replace("url(#shadow)", f"url(#shadow-{slug})")
        svg = svg.replace('id="menuClip"', f'id="menuClip-{slug}"')
        svg = svg.replace("url(#menuClip)", f"url(#menuClip-{slug})")
        swatches = "".join(
            f'<span class="swatch" style="background:{colors[name]}" '
            f'title="{name} {colors[name]}"></span>'
            for name in chips
        )
        kind = "sombre" if flavor["dark"] else "clair"
        accent = colors[accent_name]
        cards.append(
            f'''    <section class="card" style="--cc-base:{colors['base']}; --cc-mantle:{colors['mantle']}; --cc-crust:{colors['crust']}; --cc-surface0:{colors['surface0']}; --cc-surface1:{colors['surface1']}; --cc-text:{colors['text']}; --cc-subtext0:{colors['subtext0']}; --cc-accent:{accent};">
      <div class="card-head">
        <div>
          <h2>Catppuccin {flavor['name']}</h2>
          <span class="kind">{kind}</span>
        </div>
        <div class="swatches">{swatches}</div>
      </div>
      <div class="preview">{svg}</div>
      <div class="meta">
        <span><b>Base</b> <code>{colors['base']}</code></span>
        <span><b>Panneau</b> <code>{colors['crust']}</code></span>
        <span><b>Texte</b> <code>{colors['text']}</code></span>
        <span><b>Accent</b> <code>{accent}</code></span>
      </div>
    </section>'''
        )
    output.write_text(
        template.replace("{{ACCENT}}", accent_name).replace("{{CARDS}}", "\n".join(cards)),
        encoding="utf-8",
    )


def remove_stale_previews(preview_dir: Path, expected: set[str]) -> None:
    """Delete generated previews that no flavor produces any more."""
    for path in sorted(preview_dir.glob("Catppuccin-*.svg")):
        if path.name not in expected:
            path.unlink()
            print(f"  removed stale preview {path.name}")


def make_preview(path: Path, tokens: dict[str, str], flavor: dict) -> None:
    base = tokens["base"]
    mantle = tokens["mantle"]
    crust = tokens["crust"]
    surface0 = tokens["surface0"]
    surface1 = tokens["surface1"]
    text = tokens["text"]
    subtext0 = tokens["subtext0"]
    subtext1 = tokens["subtext1"]
    overlay0 = tokens["overlay0"]
    accent = tokens["accent"]
    on_accent = tokens["on_accent"]
    red = tokens["red"]
    yellow = tokens["yellow"]
    green = tokens["green"]
    mauve = tokens["mauve"]
    blue = tokens["blue"]
    teal = tokens["teal"]

    def rect(x, y, w, h, r, fill, stroke="none", sw=0, opacity=1.0):
        return (
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}" opacity="{opacity}"/>'
        )

    def text_el(x, y, value, size=13, fill=None, weight="normal", anchor="start"):
        fill = fill or text
        return (
            f'<text x="{x}" y="{y}" font-family="DejaVu Sans, Segoe UI, sans-serif" '
            f'font-size="{size}" font-weight="{weight}" fill="{fill}" '
            f'text-anchor="{anchor}">{value}</text>'
        )

    panel_items = [
        (200, "Fichiers", True),
        (310, "Terminal", False),
        (420, "Navigateur", False),
    ]
    window_items = ""
    for x, label, active in panel_items:
        if active:
            window_items += rect(x - 8, 9, 90, 22, 6, surface0)
            window_items += f'<rect x="{x - 8}" y="29" width="90" height="2" fill="{accent}"/>'
        window_items += text_el(x, 25, label, 12, text)

    sidebar_rows = ""
    for index, (label, color) in enumerate(
        (("Favoris", accent), ("Bureaux", green), ("Documents", yellow), ("Système", red))
    ):
        y = 206 + index * 32
        if index == 0:
            sidebar_rows += rect(48, y - 18, 88, 28, 7, surface0)
        sidebar_rows += f'<circle cx="60" cy="{y - 4}" r="5" fill="{color}"/>'
        sidebar_rows += text_el(72, y, label, 12, text)

    apps = [
        (mauve, "Fichiers", "Gérer vos documents"),
        (green, "Éditeur de texte", "Écrire et modifier du code"),
        (tokens["peach"], "Terminal", "Ligne de commande"),
        (blue, "Navigateur web", "Explorer internet"),
        (teal, "Paramètres", "Configurer le système"),
    ]
    app_rows = ""
    for index, (color, title, subtitle) in enumerate(apps):
        y = 150 + index * 45
        if index == 0:
            app_rows += rect(150, y - 21, 208, 38, 8, surface0)
        app_rows += rect(158, y - 18, 26, 26, 7, color)
        app_rows += rect(161, y - 15, 20, 20, 6, base, opacity=0.16)
        app_rows += text_el(194, y - 4, title, 12.5, text, "bold")
        app_rows += text_el(194, y + 11, subtitle, 10.5, subtext0)

    preview = f'''<svg xmlns="http://www.w3.org/2000/svg" width="800" height="500" viewBox="0 0 800 500">
  <defs>
    <filter id="shadow" x="-30%" y="-30%" width="160%" height="160%">
      <feDropShadow dx="0" dy="8" stdDeviation="12" flood-color="#000000" flood-opacity="0.35"/>
    </filter>
    <clipPath id="menuClip"><rect x="32" y="70" width="340" height="380" rx="16"/></clipPath>
  </defs>
  {rect(0, 0, 800, 500, 0, base)}
  <circle cx="710" cy="420" r="220" fill="{surface0}" opacity="0.55"/>
  <circle cx="90" cy="470" r="150" fill="{accent}" opacity="0.10"/>
  <circle cx="780" cy="80" r="110" fill="{accent}" opacity="0.08"/>

  <!-- Desktop window behind the menu -->
  <g transform="translate(-20 0)">
  <g filter="url(#shadow)">
    {rect(430, 150, 330, 250, 12, mantle)}
    {rect(461, 181, 268, 188, 8, base)}
  </g>
  {rect(430, 150, 330, 38, 12, surface0)}
  {rect(430, 176, 330, 12, 0, surface0)}
  <circle cx="452" cy="169" r="6" fill="{red}"/>
  <circle cx="472" cy="169" r="6" fill="{yellow}"/>
  <circle cx="492" cy="169" r="6" fill="{green}"/>
  {text_el(570, 174, "catppuccin.css", 12, subtext1, "bold", "middle")}
  {text_el(470, 220, "/* Catppuccin" + " " + flavor["name"] + " */", 13, overlay0)}
  {text_el(470, 246, "panel {", 13, mauve)}
  {text_el(490, 268, "background-color:", 13, blue)}
  {text_el(630, 268, "{crust};", 13, tokens["peach"])}
  {text_el(490, 290, "color:", 13, blue)}
  {text_el(545, 290, "{text};", 13, tokens["peach"])}
  {text_el(470, 312, "}", 13, mauve)}
  {text_el(470, 338, "/* pastel • cozy • consistent */", 12, subtext0)}
  </g>

  <!-- Panel -->
  {rect(0, 0, 800, 40, 0, crust)}
  {rect(0, 40, 800, 1, 0, surface0)}
  <circle cx="24" cy="20" r="11" fill="{accent}"/>
  {text_el(20, 25, "C", 13, on_accent, "bold")}
  {text_el(44, 25, "Catppuccin " + flavor["name"], 14, text, "bold")}
  {window_items}
  <circle cx="646" cy="20" r="4" fill="{subtext0}"/>
  <circle cx="662" cy="20" r="4" fill="{subtext0}"/>
  <circle cx="678" cy="20" r="4" fill="{subtext0}"/>
  {text_el(738, 25, "12:30", 13, text, "bold", "middle")}

  <!-- Application menu -->
  <g filter="url(#shadow)">
    {rect(32, 70, 340, 380, 16, base, surface1, 1)}
    {rect(32, 70, 118, 380, 16, mantle)}
    {rect(126, 70, 24, 380, 0, mantle)}
    {rect(149, 70, 1, 380, 0, surface0)}
    <g clip-path="url(#menuClip)">
      {rect(32, 70, 340, 48, 0, surface1, opacity=0.35)}
      {rect(32, 118, 340, 1, 0, surface0)}
    </g>
    <circle cx="82" cy="116" r="24" fill="{accent}"/>
    {text_el(75, 125, "M", 24, on_accent, "bold", "middle")}
    {text_el(82, 158, "Mint", 14, text, "bold", "middle")}
    {text_el(82, 176, "Session Cinnamon", 10.5, subtext0, "normal", "middle")}
    {sidebar_rows}
    {rect(48, 334, 88, 30, 7, surface0)}
    {text_el(70, 354, "Éteindre", 11.5, text, "bold")}
    {rect(48, 374, 88, 30, 7, surface0)}
    {text_el(73, 394, "Verrouiller", 11.5, text)}
    {rect(48, 414, 88, 22, 7, red)}
    {text_el(72, 430, "Redémarrer", 11, on_accent, "bold")}

    {rect(164, 90, 188, 34, 8, surface0, surface1, 1)}
    <circle cx="180" cy="107" r="5" fill="none" stroke="{accent}" stroke-width="2"/>
    <path d="M184 111 L190 117" stroke="{accent}" stroke-width="2" stroke-linecap="round"/>
    {text_el(200, 112, "Rechercher une application…", 11.5, subtext0)}
    {app_rows}
    {text_el(356, 436, "4 variantes", 10.5, overlay0, "normal", "end")}
  </g>
  {text_el(748, 484, "Catppuccin " + flavor["name"], 12, subtext0, "bold", "end")}
</svg>
'''
    path.write_text(preview, encoding="utf-8")


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------


def validate_css(css: str, label: str) -> None:
    if css.count("{") != css.count("}"):
        raise ValueError(f"{label}: unbalanced braces ({css.count('{')} != {css.count('}')})")
    leftover = TOKEN_RE.search(css)
    if leftover:
        raise ValueError(f"{label}: unresolved token {leftover.group(0)}")
    # Catch token-shaped leftovers the strict pattern above cannot see, such as
    # @Text@ or @accent-hover@, without rejecting legitimate at-rules.
    malformed = STRAY_TOKEN_RE.search(css)
    if malformed:
        raise ValueError(f"{label}: unexpected token-like text {malformed.group(0)}")


def validate_svg(path: Path) -> None:
    ElementTree.parse(path)


def zip_date_time() -> tuple[int, int, int, int, int, int]:
    """Return a deterministic timestamp for archive entries."""
    epoch = os.environ.get("SOURCE_DATE_EPOCH")
    if not epoch:
        return DEFAULT_ZIP_DATE_TIME
    try:
        seconds = max(int(epoch), 315532800)  # 1980-01-01, lower bound for zip
    except ValueError:
        raise ValueError(f"SOURCE_DATE_EPOCH is not an integer: {epoch!r}") from None
    return tuple(time.gmtime(seconds)[:6])  # type: ignore[return-value]


def write_archive(paths: list[tuple[Path, Path]], output: Path) -> None:
    """Write (file, archive name) pairs with fixed metadata for reproducibility."""
    date_time = zip_date_time()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for source, name in paths:
            info = zipfile.ZipInfo(str(name).replace(os.sep, "/"), date_time=date_time)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3  # Unix, so the permission bits below apply
            info.external_attr = 0o100644 << 16
            archive.writestr(info, source.read_bytes())


def package_theme(theme_dir: Path, output: Path) -> None:
    write_archive(
        [
            (path, path.relative_to(theme_dir.parent))
            for path in sorted(theme_dir.rglob("*"))
            if path.is_file()
        ],
        output,
    )


def package_all(theme_dirs: list[Path], output: Path) -> None:
    write_archive(
        [
            (path, path.relative_to(DIST_DIR))
            for theme_dir in theme_dirs
            for path in sorted(theme_dir.rglob("*"))
            if path.is_file()
        ],
        output,
    )


def build(accent_name: str, make_zips: bool, strict_contrast: bool = False) -> None:
    if accent_name not in ACCENT_NAMES:
        raise ValueError(
            f"Unknown accent '{accent_name}'. Choose from: {', '.join(ACCENT_NAMES)}"
        )

    palette = json.loads(PALETTE_PATH.read_text(encoding="utf-8"))
    css_template = CSS_TEMPLATE_PATH.read_text(encoding="utf-8")
    index_template = INDEX_TEMPLATE_PATH.read_text(encoding="utf-8")

    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir(parents=True)
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)

    theme_dirs: list[Path] = []
    issues: list[str] = []
    for slug, flavor in palette["flavors"].items():
        tokens = flavor_tokens(flavor, accent_name)
        issues.extend(contrast_issues(flavor, tokens))
        theme_dir = DIST_DIR / flavor["folder"]
        cinnamon_dir = theme_dir / "cinnamon"
        cinnamon_dir.mkdir(parents=True)

        css = substitute(css_template, tokens, f"{flavor['name']} CSS")
        validate_css(css, f"{flavor['name']} CSS")
        (cinnamon_dir / "cinnamon.css").write_text(css, encoding="utf-8")

        index = substitute(index_template, tokens, f"{flavor['name']} index.theme")
        (theme_dir / "index.theme").write_text(index, encoding="utf-8")

        write_assets(cinnamon_dir, tokens)
        make_thumbnail(cinnamon_dir / "thumbnail.png", tokens, flavor)
        preview_path = PREVIEW_DIR / f"{flavor['folder']}.svg"
        make_preview(preview_path, tokens, flavor)
        validate_svg(preview_path)
        shutil.copy2(ROOT / "LICENSE", theme_dir / "LICENSE")

        for svg in cinnamon_dir.glob("*.svg"):
            validate_svg(svg)

        png_header = (cinnamon_dir / "thumbnail.png").read_bytes()[:24]
        if not png_header.startswith(b"\x89PNG\r\n\x1a\n"):
            raise ValueError(f"{flavor['name']}: thumbnail is not a valid PNG")
        width, height = struct.unpack(">II", png_header[16:24])
        if (width, height) != THUMBNAIL_SIZE:
            raise ValueError(
                f"{flavor['name']}: thumbnail is {width}x{height}, "
                f"expected {THUMBNAIL_SIZE[0]}x{THUMBNAIL_SIZE[1]}"
            )

        theme_dirs.append(theme_dir)
        print(
            f"  {flavor['folder']:<24} {len(css.splitlines()):>4} lines CSS, "
            f"accent {accent_name}, {len(list(cinnamon_dir.iterdir()))} files"
        )

    make_overview(palette, PREVIEW_DIR, PREVIEW_DIR / "overview.html", accent_name)
    remove_stale_previews(
        PREVIEW_DIR,
        {flavor["folder"] + ".svg" for flavor in palette["flavors"].values()},
    )

    if make_zips:
        package_all(theme_dirs, DIST_DIR / "Catppuccin-Cinnamon-all-flavors.zip")
        for theme_dir in theme_dirs:
            package_theme(theme_dir, DIST_DIR / f"{theme_dir.name}.zip")
        print("  archives: 5 zip files")

    print(f"\nBuilt {len(theme_dirs)} themes in {DIST_DIR}")
    print(f"Previews: {PREVIEW_DIR}")

    if issues:
        print(f"\nContrastes sous {WCAG_TEXT:g}:1 :")
        for issue in issues:
            print(f"  {issue}")
        if strict_contrast:
            raise ValueError(
                f"{len(issues)} couple(s) de couleurs sous le seuil de contraste WCAG"
            )
    else:
        print(f"\nContrastes : tous les couples contrôlés atteignent {WCAG_TEXT:g}:1.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--accent",
        default="blue",
        choices=ACCENT_NAMES,
        help="Catppuccin accent color used for highlights (default: blue)",
    )
    parser.add_argument("--no-zip", action="store_true", help="do not create zip archives")
    parser.add_argument(
        "--strict-contrast",
        action="store_true",
        help="fail when a checked color pair is below the WCAG 4.5:1 ratio",
    )
    args = parser.parse_args()

    print("Catppuccin for Cinnamon — build")
    print(f"Palette: {PALETTE_PATH}")
    try:
        build(args.accent, not args.no_zip, args.strict_contrast)
    except Exception as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
