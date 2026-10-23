#!/usr/bin/env python3
"""Tests unitaires des helpers de scripts/build.py (bibliothèque standard seule).

Lancer : python3 scripts/test_build.py
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build

WCAG = build.WCAG_TEXT


def palette() -> dict:
    return json.loads(build.PALETTE_PATH.read_text(encoding="utf-8"))


class ContrastTests(unittest.TestCase):
    def test_extremes(self) -> None:
        self.assertAlmostEqual(build.contrast_ratio("#000000", "#ffffff"), 21.0, places=2)
        self.assertAlmostEqual(build.contrast_ratio("#ffffff", "#ffffff"), 1.0, places=2)

    def test_symmetric(self) -> None:
        self.assertAlmostEqual(
            build.contrast_ratio("#1e1e2e", "#cdd6f4"),
            build.contrast_ratio("#cdd6f4", "#1e1e2e"),
        )

    def test_official_pairs(self) -> None:
        # Mocha text on base is comfortable; Latte blue on base is not.
        self.assertGreater(build.contrast_ratio("#cdd6f4", "#1e1e2e"), 7)
        self.assertLess(build.contrast_ratio("#1e66f5", "#eff1f5"), WCAG)


class ColorMathTests(unittest.TestCase):
    def test_mix_endpoints(self) -> None:
        self.assertEqual(build.mix("#000000", "#ffffff", 0.0), "#000000")
        self.assertEqual(build.mix("#000000", "#ffffff", 1.0), "#ffffff")

    def test_hsl_roundtrip(self) -> None:
        for color in ("#df8e1d", "#1e66f5", "#000000", "#ffffff", "#808080", "#dce0e8"):
            hue, saturation, lightness = build.rgb_to_hsl(color)
            self.assertEqual(build.hsl_to_hex(hue, saturation, lightness), color, color)

    def test_ensure_contrast_reaches_target(self) -> None:
        flavors = palette()["flavors"]
        for slug in ("latte", "frappe", "macchiato", "mocha"):
            colors = flavors[slug]["colors"]
            surfaces = [colors["base"], colors["crust"]]
            for name in ("yellow", "green", "red", "sky", "blue", "teal"):
                adjusted = build.ensure_contrast(colors[name], surfaces, colors["text"])
                for surface in ("base", "crust"):
                    self.assertGreaterEqual(
                        build.contrast_ratio(adjusted, colors[surface]),
                        WCAG - 1e-9,
                        f"{slug}/{name} sur {surface}",
                    )


class TokenTests(unittest.TestCase):
    def test_alpha_variants(self) -> None:
        tokens = build.flavor_tokens(palette()["flavors"]["mocha"], "blue")
        self.assertEqual(tokens["text_a80"], "rgba(205, 214, 244, 0.8)")
        self.assertEqual(tokens["accent_a25"], "rgba(137, 180, 250, 0.25)")

    def test_text_secondary_is_readable(self) -> None:
        for slug, flavor in palette()["flavors"].items():
            colors = flavor["colors"]
            tokens = build.flavor_tokens(flavor, "blue")
            for surface in ("base", "crust"):
                self.assertGreaterEqual(
                    build.contrast_ratio(tokens["text_secondary"], colors[surface]),
                    WCAG - 1e-9,
                    f"{slug} sur {surface}",
                )

    def test_contrast_report_is_empty_for_default_accent(self) -> None:
        for flavor in palette()["flavors"].values():
            tokens = build.flavor_tokens(flavor, "blue")
            self.assertEqual(build.contrast_issues(flavor, tokens), [])

    def test_dark_flavors_keep_palette_colors(self) -> None:
        flavors = palette()["flavors"]
        for slug in ("frappe", "macchiato", "mocha"):
            colors = flavors[slug]["colors"]
            tokens = build.flavor_tokens(flavors[slug], "blue")
            expected = {
                "text_secondary": colors["subtext0"],
                "text_success": colors["green"],
                "text_warning": colors["yellow"],
                "text_error": colors["red"],
                "link": colors["blue"],
                "link_hover": colors["sky"],
            }
            for name, value in expected.items():
                self.assertEqual(tokens[name], value, f"{slug}/{name}")

    def test_on_accent_is_readable_for_every_accent(self) -> None:
        for accent in build.ACCENT_NAMES:
            for slug, flavor in palette()["flavors"].items():
                tokens = build.flavor_tokens(flavor, accent)
                self.assertGreaterEqual(
                    build.contrast_ratio(tokens["on_accent"], tokens["accent"]),
                    WCAG - 1e-9,
                    f"{slug}/{accent}",
                )

    def test_unresolved_token_raises(self) -> None:
        with self.assertRaises(ValueError):
            build.substitute("a { color: @nope@; }", {}, "test")


class CssValidationTests(unittest.TestCase):
    def test_accepts_valid_css_and_at_rules(self) -> None:
        build.validate_css("a { color: #ffffff; }\n@media screen { b { color: #000000; } }", "ok")

    def test_rejects_unresolved_token(self) -> None:
        with self.assertRaises(ValueError):
            build.validate_css("a { color: @nope@; }", "leftover")

    def test_rejects_malformed_token(self) -> None:
        with self.assertRaises(ValueError):
            build.validate_css("a { color: @Accent@; }", "stray")

    def test_rejects_unbalanced_braces(self) -> None:
        with self.assertRaises(ValueError):
            build.validate_css("a { color: #ffffff;", "braces")


class ThumbnailTests(unittest.TestCase):
    def test_format_matches_cinnamon_chooser(self) -> None:
        self.assertEqual(build.THUMBNAIL_SIZE, (247, 60))


if __name__ == "__main__":
    unittest.main(verbosity=1)
