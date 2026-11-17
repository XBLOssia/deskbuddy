from pathlib import Path
import json
import struct
import tempfile
import tkinter as tk
import unittest
import zlib

from deskbuddy.sprites import CELL, ROLE_ROWS, PetAppearance, PetSpriteSheet, fit_factor, frame_box, png_layout


def write_fixture(path, width=1536, height=1872):
    """Transparent geometry fixture with markers; never substitute pet artwork."""
    def chunk(name, value):
        return struct.pack(">I", len(value)) + name + value + struct.pack(">I", zlib.crc32(name + value))

    compressor = zlib.compressobj()
    encoded = bytearray()
    for y in range(height):
        pixels = bytearray(width * 4)
        for row, count in enumerate((6, 8, 8, 4, 5, 8, 6, 6, 6, 8, 8)):
            if y == row * CELL[1] + 20:
                for frame in range(count):
                    x = frame * CELL[0] + 20
                    if x < width:
                        pixels[x * 4:x * 4 + 4] = bytes((row * 20, frame * 30, 100, 255))
        encoded.extend(compressor.compress(b"\x00" + pixels))
    encoded.extend(compressor.flush())
    header = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    Path(path).write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", bytes(encoded)) + chunk(b"IEND", b""))


class SpriteTests(unittest.TestCase):
    def test_reader_accepts_both_export_layouts(self):
        with tempfile.TemporaryDirectory() as folder:
            for height in (1872, 2288):
                path = Path(folder) / f"fixture-{height}.png"
                write_fixture(path, height=height)
                self.assertEqual(png_layout(path), (1536, height))

    def test_reader_rejects_other_dimensions_and_non_png(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "fixture.png"
            write_fixture(path, width=20, height=20)
            with self.assertRaises(ValueError):
                png_layout(path)
            path.write_bytes(b"RIFF not a PNG")
            with self.assertRaises(ValueError):
                png_layout(path)

    def test_working_uses_thinking_row_and_never_directional_running(self):
        self.assertEqual(ROLE_ROWS["working"], 7)
        self.assertEqual(ROLE_ROWS["attention"], 6)
        self.assertEqual(ROLE_ROWS["done"], 8)

    def test_frame_boxes_stay_in_populated_cells(self):
        self.assertEqual(frame_box(7, 5), (960, 1456, 1152, 1664))
        for row, frame in ((0, 6), (3, 4), (-1, 0), (11, 0)):
            with self.assertRaises(ValueError):
                frame_box(row, frame)

    def test_native_and_high_dpi_fit_preserve_aspect_and_stay_inside_preview(self):
        for available in (216, 270, 432, 540, 648):
            factor = fit_factor(available)
            self.assertLessEqual(208 * factor, available)
            self.assertLessEqual(factor.numerator, 12)
            self.assertLessEqual(factor.denominator, 8)

    def test_tk_decoder_extracts_correct_frames_and_preserves_transparency(self):
        root = tk.Tk()
        root.withdraw()
        try:
            with tempfile.TemporaryDirectory() as folder:
                path = Path(folder) / "geometry-fixture.png"
                write_fixture(path)
                sheet = PetSpriteSheet(root, path)
                for role, row in ROLE_ROWS.items():
                    frames = sheet.frames(role, 216)
                    self.assertEqual(len(frames), 6)
                    for index, frame in enumerate(frames):
                        self.assertEqual(frame.get(20, 20), (row * 20, index * 30, 100))
                        self.assertTrue(frame.transparency_get(0, 0))
                high_dpi = sheet.frames("working", 540)[0]
                self.assertLessEqual(high_dpi.height(), 540)
                self.assertTrue(high_dpi.transparency_get(0, 0))
        finally:
            root.destroy()

    def test_status_appearance_selects_only_the_requested_skin(self):
        root = tk.Tk()
        root.withdraw()
        try:
            with tempfile.TemporaryDirectory() as folder:
                folder = Path(folder)
                write_fixture(folder / "base.png")
                write_fixture(folder / "working.png", 192, 208)
                manifest = folder / "appearance.json"
                manifest.write_text(json.dumps({"version": 1, "base_sheet": "base.png",
                                               "status_skins": {"working": "working.png"}}))
                appearance = PetAppearance(root, manifest)
                self.assertEqual(len(appearance.frames("working", 216)), 1)
                self.assertEqual(appearance.frames("working", 216)[0].get(20, 20), (0, 0, 100))
                self.assertEqual(len(appearance.frames("attention", 216)), 6)
                self.assertEqual(appearance.frames("attention", 216)[0].get(20, 20), (120, 0, 100))
                manifest.write_text(json.dumps({"version": 1, "base_sheet": "base.png",
                                               "status_skins": {"not-a-status": "working.png"}}))
                with self.assertRaises(ValueError):
                    PetAppearance(root, manifest)
        finally:
            root.destroy()


if __name__ == "__main__":
    unittest.main()
