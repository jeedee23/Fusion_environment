"""Tests for the JSON working model behind the PhotoBooth settings GUI."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import photobooth_settings_gui as gui


class SettingsModelTests(unittest.TestCase):
    def test_catalog_contains_every_xml_attribute(self) -> None:
        catalog = gui.create_catalog()
        root = gui.ET.fromstring(gui.SOURCE_XML.read_bytes())
        xml_attribute_count = sum(len(element.attrib) for element in root.iter())
        fields = list(gui.walk_fields(catalog["tree"]))

        self.assertEqual(len(fields), xml_attribute_count)
        self.assertEqual(
            catalog["source"]["sha256"],
            "79810da1933a75733383a55dd0a4791546a3a49f6ab1e8720f9718338366e4d5",
        )
        self.assertEqual(catalog["source"]["base_status"], "unverified_current_file")

    def test_catalog_has_exact_indexed_field_identity(self) -> None:
        catalog = gui.create_catalog()
        _, field = gui.find_field(
            catalog, "/PhotoBooth[1]/SketchLineColor[1]/@ARGB"
        )
        self.assertEqual(field["xml_value"], "1.0 0.02 0.59 0.84")
        self.assertEqual(field["working_value"], field["xml_value"])

    def test_colour_adjustment_format_preserves_alpha_order(self) -> None:
        colour = gui.parse_colour("ARGB", "0.25 0.1 0.2 0.3")
        revised = gui.ColourValue("ARGB", 0.4, 0.5, 0.6, colour.alpha)
        self.assertEqual(gui.format_colour(revised, "0.25 0.1 0.2 0.3"), "0.25 0.4 0.5 0.6")

    def test_signed_shadow_color_is_not_editable_colour(self) -> None:
        catalog = gui.create_catalog()
        _, field = gui.find_field(
            catalog, "/PhotoBooth[1]/OGSLighting[1]/Light[1]/@ShadowColor"
        )
        self.assertEqual(field["kind"], "signed-unverified")
        with self.assertRaisesRegex(gui.ModelError, "read-only"):
            gui.validate_working_value(field, "0 0 0")

    def test_clone_preserves_working_values_and_resets_history(self) -> None:
        catalog = gui.create_catalog()
        _, field = gui.find_field(
            catalog, "/PhotoBooth[1]/SketchLineColor[1]/@ARGB"
        )
        gui.append_history(field, "1 0.1 0.2 0.3")
        with tempfile.TemporaryDirectory() as directory:
            original_profiles = gui.PROFILES_DIRECTORY
            try:
                gui.PROFILES_DIRECTORY = Path(directory)
                _, cloned = gui.clone_profile(catalog, "soft-tone")
            finally:
                gui.PROFILES_DIRECTORY = original_profiles
        _, cloned_field = gui.find_field(
            cloned, "/PhotoBooth[1]/SketchLineColor[1]/@ARGB"
        )
        self.assertEqual(cloned_field["working_value"], "1 0.1 0.2 0.3")
        self.assertEqual(cloned_field["history"], ["1 0.1 0.2 0.3"])


if __name__ == "__main__":
    unittest.main()
