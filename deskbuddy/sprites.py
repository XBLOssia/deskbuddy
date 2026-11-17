"""Read exported Codex pet PNGs without changing their artwork or pet records."""

from fractions import Fraction
import json
from pathlib import Path
import struct
import tkinter as tk


CELL = (192, 208)
ROW_FRAMES = (6, 8, 8, 4, 5, 8, 6, 6, 6, 8, 8)
# These are application roles, not a claim that a finished reply passed review.
ROLE_ROWS = {"idle": 0, "working": 7, "attention": 6, "name": 6, "done": 8}


def png_dimensions(path):
    """Check encoded dimensions before passing a potentially large file to Tk."""
    path = Path(path)
    if path.stat().st_size > 20 * 1024 * 1024:
        raise ValueError("Pet PNG must be no larger than 20 MiB.")
    with path.open("rb") as stream:
        header = stream.read(24)
    if len(header) < 24 or header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        raise ValueError("Choose an exported PNG sprite sheet. WebP is not supported by this reader yet.")
    return struct.unpack(">II", header[16:24])


def png_layout(path):
    dimensions = png_dimensions(path)
    if dimensions not in ((1536, 1872), (1536, 2288)):
        raise ValueError("Expected a Codex pet sheet: 1536×1872 (v1) or 1536×2288 (v2).")
    return dimensions


def frame_box(row, frame):
    if type(row) is not int or not 0 <= row < len(ROW_FRAMES):
        raise ValueError("Unknown sprite row.")
    if type(frame) is not int or not 0 <= frame < ROW_FRAMES[row]:
        raise ValueError("Frame is outside the populated part of this row.")
    x, y = frame * CELL[0], row * CELL[1]
    return x, y, x + CELL[0], y + CELL[1]


def fit_factor(available):
    """A bounded integer zoom/subsample pair preserves alpha without dependencies."""
    limit = available / max(CELL)
    choices = [Fraction(n, d) for n in range(1, 13) for d in range(1, 9) if n / d <= limit]
    if not choices:
        raise ValueError("Sprite display area is too small.")
    return max(choices)


class PetSpriteSheet:
    def __init__(self, master, path):
        self.master = master
        self.path = Path(path).expanduser().resolve()
        self.dimensions = png_layout(self.path)
        try:
            self.image = tk.PhotoImage(master=master, file=str(self.path), format="png")
        except tk.TclError as exc:
            raise ValueError("The pet PNG could not be decoded.") from exc
        if (self.image.width(), self.image.height()) != self.dimensions:
            raise ValueError("Decoded sprite dimensions do not match the PNG header.")
        self.cache = {}

    def frames(self, role, available):
        row = ROLE_ROWS[role]
        factor = fit_factor(available)
        key = (row, factor)
        if key not in self.cache:
            output = []
            for frame in range(ROW_FRAMES[row]):
                cell = tk.PhotoImage(master=self.master, width=CELL[0], height=CELL[1])
                self.image.tk.call(str(cell), "copy", str(self.image), "-from", *frame_box(row, frame))
                if factor.numerator != 1:
                    cell = cell.zoom(factor.numerator)
                if factor.denominator != 1:
                    cell = cell.subsample(factor.denominator)
                output.append(cell)
            self.cache[key] = output
        return self.cache[key]


class PetStill:
    """A prepared 192×208 status skin, shown without fabricated motion."""

    def __init__(self, master, path):
        path = Path(path)
        if png_dimensions(path) != CELL:
            raise ValueError("Status skins must be prepared as 192×208 transparent PNG cells.")
        try:
            self.image = tk.PhotoImage(master=master, file=str(path), format="png")
        except tk.TclError as exc:
            raise ValueError("The status skin PNG could not be decoded.") from exc
        self.cache = {}

    def frames(self, role, available):
        factor = fit_factor(available)
        if factor not in self.cache:
            image = self.image
            if factor.numerator != 1:
                image = image.zoom(factor.numerator)
            if factor.denominator != 1:
                image = image.subsample(factor.denominator)
            self.cache[factor] = [image]
        return self.cache[factor]


class PetAppearance:
    """Select independent approved pot treatments; never tint the face."""

    def __init__(self, master, manifest):
        manifest = Path(manifest).expanduser().resolve()
        if manifest.stat().st_size > 100_000:
            raise ValueError("Pet appearance configuration is too large.")
        data = json.loads(manifest.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or data.get("version") != 1:
            raise ValueError("Unsupported pet appearance configuration.")
        base = data.get("base_sheet")
        skins = data.get("status_skins", {})
        if not isinstance(base, str) or not base or not isinstance(skins, dict):
            raise ValueError("Pet appearance needs a base_sheet and status_skins mapping.")
        self.base = PetSpriteSheet(master, manifest.parent / base)
        self.skins = {}
        for role, relative in skins.items():
            if role not in ROLE_ROWS or not isinstance(relative, str) or not relative:
                raise ValueError("Invalid pet status skin.")
            path = manifest.parent / relative
            self.skins[role] = PetStill(master, path) if png_dimensions(path) == CELL else PetSpriteSheet(master, path)

    def frames(self, role, available):
        return self.skins.get(role, self.base).frames(role, available)
