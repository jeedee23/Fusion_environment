import unittest
from xml.etree import ElementTree

from customize_environment import choose_color, find_colors


class FindColorsTests(unittest.TestCase):
    def test_finds_hex_color_attributes_and_text(self):
        root = ElementTree.fromstring(
            '<Fusion color="#112233"><Widget tint="0xAABBCCDD">'
            "<Color>#abcdef</Color><Label>not a color</Label></Widget></Fusion>"
        )

        colors = find_colors(root)

        self.assertEqual(
            [color.location for color in colors],
            [
                "/Fusion[1]/@color",
                "/Fusion[1]/Widget[1]/@tint",
                "/Fusion[1]/Widget[1]/Color[1]",
            ],
        )

    def test_updates_element_text_and_preserves_alpha_and_prefix(self):
        root = ElementTree.fromstring('<Fusion><Color>0x11223380</Color></Fusion>')
        color = find_colors(root)[0]

        color.set_value(choose_color(color, "#A1B2C3"))

        self.assertEqual(root.find("Color").text, "0xA1B2C380")

    def test_does_not_match_unprefixed_numbers_or_malformed_values(self):
        root = ElementTree.fromstring(
            '<Fusion><Value>112233</Value><Color>#12345</Color></Fusion>'
        )

        self.assertEqual(find_colors(root), [])


if __name__ == "__main__":
    unittest.main()
