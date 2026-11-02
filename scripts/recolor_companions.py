#!/usr/bin/env python3
"""Recolore les thèmes Kora et Vimix avec la palette Catppuccin Mocha.

Le script modifie les fichiers en place, de façon idempotente :

  icons/Catppuccin-Kora-Mocha/    (SVG, catégories d'interface uniquement)
  cursors/Catppuccin-Vimix-Mocha/ (Xcursor)

Les icônes d'applications (apps/) sont volontairement laissées intactes pour
préserver les logos de marque. Les valeurs déjà présentes dans la palette
Catppuccin ne sont pas retouchées, ce qui permet de relancer le script sans
dérive.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PALETTE_PATH = ROOT / "palette.json"
ICON_DIR = ROOT / "icons" / "Catppuccin-Kora-Mocha"
CURSOR_DIR = ROOT / "cursors" / "Catppuccin-Vimix-Mocha"

# Catégories Kora recolorées. Les icônes de marque (apps/) sont exclues.
ICON_CATEGORIES = (
    "actions",
    "animations",
    "categories",
    "devices",
    "emblems",
    "emotes",
    "mimetypes",
    "panel",
    "places",
    "status",
)

HEX_RE = re.compile(r"#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b")
RGB_RE = re.compile(r"rgb\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*\)")
RGBA_RE = re.compile(
    r"rgba\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*([0-9.]+)\s*\)"
)
NAMED_COLOR_RE = re.compile(
    r'(?P<prefix>(?:fill|stroke|stop-color|color)\s*[:=]\s*["\']?)'
    r'(?P<name>white|black)'
    r'(?P<suffix>["\']?)',
    re.IGNORECASE,
)

GRAY_RAMP = (
    "text",
    "subtext1",
    "subtext0",
    "overlay2",
    "overlay1",
    "overlay0",
    "surface2",
    "surface1",
    "surface0",
    "base",
    "mantle",
    "crust",
)

HUE_RAMP = (
    "red",
    "peach",
    "yellow",
    "green",
    "teal",
    "sky",
    "blue",
    "mauve",
    "pink",
)


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    if len(value) == 3:
        value = "".join(character * 2 for character in value)
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)


def rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return "#{:02x}{:02x}{:02x}".format(*rgb)


def srgb_to_linear(component: int) -> float:
    value = component / 255.0
    if value <= 0.04045:
        return value / 12.92
    return ((value + 0.055) / 1.055) ** 2.4


def rgb_to_lab(rgb: tuple[int, int, int]) -> tuple[float, float, float]:
    red, green, blue = (srgb_to_linear(component) for component in rgb)
    x = red * 0.4124564 + green * 0.3575761 + blue * 0.1804375
    y = red * 0.2126729 + green * 0.7151522 + blue * 0.0721750
    z = red * 0.0193339 + green * 0.1191920 + blue * 0.9503041

    def pivot(value: float) -> float:
        delta = 6.0 / 29.0
        if value > delta**3:
            return value ** (1.0 / 3.0)
        return value / (3 * delta * delta) + 4.0 / 29.0

    fx, fy, fz = pivot(x / 0.95047), pivot(y / 1.0), pivot(z / 1.08883)
    return 116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)


def rgb_to_hue(rgb: tuple[int, int, int]) -> float:
    red, green, blue = (component / 255.0 for component in rgb)
    highest, lowest = max(red, green, blue), min(red, green, blue)
    delta = highest - lowest
    if delta == 0:
        return 0.0
    if highest == red:
        hue = ((green - blue) / delta) % 6
    elif highest == green:
        hue = (blue - red) / delta + 2
    else:
        hue = (red - green) / delta + 4
    return hue * 60.0


def hue_distance(first: float, second: float) -> float:
    difference = abs(first - second) % 360.0
    return min(difference, 360.0 - difference)


def color_distance(first: str, second: str) -> float:
    first_lab = rgb_to_lab(hex_to_rgb(first))
    second_lab = rgb_to_lab(hex_to_rgb(second))
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(first_lab, second_lab)))


def saturation(rgb: tuple[int, int, int]) -> float:
    highest, lowest = max(rgb), min(rgb)
    return 0.0 if highest == 0 else (highest - lowest) / highest


def is_grayish(rgb: tuple[int, int, int]) -> bool:
    return max(rgb) - min(rgb) <= 45 and saturation(rgb) <= 0.35


def is_white(rgb: tuple[int, int, int]) -> bool:
    return min(rgb) >= 245


def is_black(rgb: tuple[int, int, int]) -> bool:
    return max(rgb) <= 12


class Recolored:
    def __init__(self, flavor: str, accent: str):
        palette = json.loads(PALETTE_PATH.read_text(encoding="utf-8"))
        if flavor not in palette["flavors"]:
            raise ValueError(f"Flavor inconnu : {flavor}")
        if accent not in palette["flavors"][flavor]["colors"]:
            raise ValueError(f"Accent inconnu : {accent}")
        colors = palette["flavors"][flavor]["colors"]
        self.colors = colors
        self.accent = colors[accent]
        self.text = colors["text"]
        self.base = colors["base"]
        self.crust = colors["crust"]

        self.palette_set = {value.lower() for value in colors.values()}
        self.grays = [colors[name] for name in GRAY_RAMP]
        self.hues = [colors[name] for name in HUE_RAMP]
        self.scheme = {
            "#dfdfdf": self.text,
            "#4285f4": self.accent,
            "#ff9800": colors["peach"],
            "#4caf50": colors["green"],
            "#f44336": colors["red"],
        }

    def nearest(self, rgb: tuple[int, int, int], candidates: list[str]) -> str:
        value = rgb_to_hex(rgb)
        return min(candidates, key=lambda candidate: color_distance(value, candidate))

    def map_rgb(
        self, rgb: tuple[int, int, int], colored_context: bool
    ) -> tuple[int, int, int]:
        value = rgb_to_hex(rgb)
        if value in self.palette_set:
            return rgb
        if value in self.scheme:
            return hex_to_rgb(self.scheme[value])
        if is_white(rgb):
            return hex_to_rgb(self.base if colored_context else self.text)
        if is_black(rgb):
            return hex_to_rgb(self.crust)
        if is_grayish(rgb):
            return hex_to_rgb(self.nearest(rgb, self.grays))
        return hex_to_rgb(
            min(
                self.hues,
                key=lambda color: hue_distance(rgb_to_hue(rgb), rgb_to_hue(hex_to_rgb(color))),
            )
        )

    def map_text(self, text: str) -> tuple[str, int]:
        colors = [
            hex_to_rgb(match.group(1))
            for match in HEX_RE.finditer(text)
        ]
        colors.extend(
            (int(match.group(1)), int(match.group(2)), int(match.group(3)))
            for match in RGB_RE.finditer(text)
        )
        colors.extend(
            (int(match.group(1)), int(match.group(2)), int(match.group(3)))
            for match in RGBA_RE.finditer(text)
        )
        colored_context = any(
            not is_grayish(rgb) and not is_white(rgb) and not is_black(rgb)
            for rgb in colors
        )
        changes = 0

        def replace_rgba(match: re.Match[str]) -> str:
            nonlocal changes
            rgb = (int(match.group(1)), int(match.group(2)), int(match.group(3)))
            mapped = self.map_rgb(rgb, colored_context)
            if mapped != rgb:
                changes += 1
            return "rgba({}, {}, {}, {})".format(*mapped, match.group(4))

        def replace_rgb(match: re.Match[str]) -> str:
            nonlocal changes
            rgb = (int(match.group(1)), int(match.group(2)), int(match.group(3)))
            mapped = self.map_rgb(rgb, colored_context)
            if mapped != rgb:
                changes += 1
            return rgb_to_hex(mapped)

        def replace_hex(match: re.Match[str]) -> str:
            nonlocal changes
            original = match.group(1)
            rgb = hex_to_rgb(original)
            mapped = self.map_rgb(rgb, colored_context)
            if mapped != rgb:
                changes += 1
            return rgb_to_hex(mapped)

        def replace_named(match: re.Match[str]) -> str:
            nonlocal changes
            given = match.group("name").lower()
            mapped = self.base if (given == "white" and colored_context) else (
                self.text if given == "white" else self.crust
            )
            changes += 1
            return match.group("prefix") + mapped + match.group("suffix")

        text = RGBA_RE.sub(replace_rgba, text)
        text = RGB_RE.sub(replace_rgb, text)
        text = HEX_RE.sub(replace_hex, text)
        text = NAMED_COLOR_RE.sub(replace_named, text)
        return text, changes


def iter_regular_files(root: Path):
    for entry in sorted(root.iterdir(), key=lambda path: path.name):
        if entry.name == ".DS_Store":
            continue
        if entry.is_symlink():
            continue
        if entry.is_dir():
            yield from iter_regular_files(entry)
        elif entry.is_file():
            yield entry


def recolor_icons(recolor: Recolored, dry_run: bool) -> tuple[int, int]:
    changed_files = 0
    changed_values = 0
    if not ICON_DIR.is_dir():
        raise FileNotFoundError(f"Dossier introuvable : {ICON_DIR}")
    for category in ICON_CATEGORIES:
        category_dir = ICON_DIR / category
        if not category_dir.is_dir():
            continue
        for path in iter_regular_files(category_dir):
            if path.suffix.lower() != ".svg":
                continue
            text = path.read_text(encoding="utf-8")
            updated, count = recolor.map_text(text)
            if count:
                changed_files += 1
                changed_values += count
                if not dry_run:
                    path.write_text(updated, encoding="utf-8")
    return changed_files, changed_values


def recolor_xcursor(data: bytes, recolor: Recolored) -> tuple[bytes, int]:
    magic, header_size, version, ntoc = struct.unpack_from("<4sIII", data, 0)
    if magic != b"Xcur":
        raise ValueError("format Xcursor inattendu")

    chunks: list[tuple[int, int, bytes]] = []
    for index in range(ntoc):
        chunk_type, subtype, position = struct.unpack_from(
            "<III", data, header_size + index * 12
        )
        if chunk_type != 0xFFFD0002:
            raise ValueError(f"chunk Xcursor non pris en charge : {chunk_type:#x}")
        image_header_size, _, _, image_version, width, height, xhot, yhot, delay = (
            struct.unpack_from("<IIIIIIIII", data, position)
        )
        start = position + image_header_size
        pixels = bytearray(data[start : start + width * height * 4])
        changes = 0
        for offset in range(0, len(pixels), 4):
            blue, green, red, alpha = pixels[offset : offset + 4]
            mapped = recolor.map_rgb((red, green, blue), colored_context=False)
            if mapped != (red, green, blue):
                changes += 1
                pixels[offset : offset + 4] = bytes(
                    (mapped[2], mapped[1], mapped[0], alpha)
                )
        header = struct.pack(
            "<IIIIIIIII",
            image_header_size,
            chunk_type,
            subtype,
            image_version,
            width,
            height,
            xhot,
            yhot,
            delay,
        )
        chunks.append((chunk_type, subtype, header + bytes(pixels)))

    positions = []
    position = header_size + ntoc * 12
    for chunk_type, subtype, chunk in chunks:
        positions.append((chunk_type, subtype, position, len(chunk)))
        position += len(chunk)

    output = bytearray(struct.pack("<4sIII", magic, header_size, version, ntoc))
    for chunk_type, subtype, chunk_position, _ in positions:
        output += struct.pack("<III", chunk_type, subtype, chunk_position)
    for _, _, chunk in chunks:
        output += chunk
    return bytes(output), changes


def recolor_cursors(recolor: Recolored, dry_run: bool) -> tuple[int, int]:
    changed_files = 0
    changed_pixels = 0
    cursors_dir = CURSOR_DIR / "cursors"
    if not cursors_dir.is_dir():
        raise FileNotFoundError(f"Dossier introuvable : {cursors_dir}")
    for path in sorted(cursors_dir.iterdir()):
        if path.is_symlink() or not path.is_file():
            continue
        data = path.read_bytes()
        if data[:4] != b"Xcur":
            continue
        updated, count = recolor_xcursor(data, recolor)
        if updated != data:
            changed_files += 1
            changed_pixels += count
            if not dry_run:
                path.write_bytes(updated)
    return changed_files, changed_pixels


def index_needs_update() -> bool:
    icon_index = ICON_DIR / "index.theme"
    if icon_index.is_file():
        text = icon_index.read_text(encoding="utf-8")
        if "Name=Catppuccin Kora Mocha" not in text or "FollowsColorScheme=false" not in text:
            return True
    cursor_index = CURSOR_DIR / "index.theme"
    if cursor_index.is_file():
        text = cursor_index.read_text(encoding="utf-8")
        if "Name=Catppuccin Vimix Mocha" not in text:
            return True
    return False


def update_index_files() -> None:
    """Keep the metadata in sync when the script is run on fresh sources."""
    icon_index = ICON_DIR / "index.theme"
    if icon_index.is_file():
        text = icon_index.read_text(encoding="utf-8")
        text = text.replace("Name=Kora", "Name=Catppuccin Kora Mocha", 1)
        text = text.replace(
            "Comment=Kora icon theme for GNU/Linux",
            "Comment=Kora recolorié avec la palette Catppuccin Mocha",
            1,
        )
        text = text.replace("FollowsColorScheme=true", "FollowsColorScheme=false", 1)
        icon_index.write_text(text, encoding="utf-8")

    cursor_index = CURSOR_DIR / "index.theme"
    if cursor_index.is_file():
        text = cursor_index.read_text(encoding="utf-8")
        text = text.replace("Name=Vimix Cursors", "Name=Catppuccin Vimix Mocha", 1)
        if "Comment=" not in text:
            text = text.replace(
                "Name=Catppuccin Vimix Mocha",
                "Name=Catppuccin Vimix Mocha\n"
                "Comment=Curseurs Vimix recolorés avec la palette Catppuccin Mocha",
                1,
            )
        cursor_index.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--flavor", default="mocha", help="flavor Catppuccin (mocha)")
    parser.add_argument("--accent", default="blue", help="accent Catppuccin (blue)")
    parser.add_argument(
        "--dry-run", action="store_true", help="affiche les changements sans écrire"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="ne modifie rien et échoue si des couleurs restent à recolorer",
    )
    args = parser.parse_args()
    dry_run = args.dry_run or args.check

    try:
        recolor = Recolored(args.flavor, args.accent)
        icon_files, icon_values = recolor_icons(recolor, dry_run)
        cursor_files, cursor_pixels = recolor_cursors(recolor, dry_run)
        if not dry_run:
            update_index_files()
    except Exception as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    prefix = "Simulation : " if args.dry_run else ""
    print(
        f"{prefix}{icon_files} SVG modifiés ({icon_values} couleurs), "
        f"{cursor_files} curseurs modifiés ({cursor_pixels} pixels)."
    )
    if args.check and (icon_files or cursor_files or index_needs_update()):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
