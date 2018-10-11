# Copyright 2018 Kiyoshi Aman
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY
# SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR
# IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

import json

from PyQt5.QtGui import QPixmap, QColor

class Font:
    """A simple class for managing Smeargle's font data."""

    def __init__(self, filename):
        """Creates the font object.

        Takes a filename pointing at the JSON metadata for a font.
        """
        with open(filename, mode='rb') as f:
            self._json = json.load(f)

        self._image = QPixmap(self._json['filename'])
        self._colors = []

        if 'palette' in self._json:
            for color in self._json['palette']:
                if isinstance(color, (list, tuple)):
                    self._colors.append(QColor(*color))
                elif isinstance(color, str):
                    red   = int(color[0:2], 16)
                    green = int(color[2:4], 16)
                    blue  = int(color[4:6], 16)
                    self._colors.append(QColor(red, green, blue).rgb())
                else:
                    raise ValueError('unsupported color format: {}'.format(color))
        else:
            print("WARNING: No palette was provided with this font. Output palette order cannot be guaranteed.")
            tile = self.index(self.table[' ']['index'])
            self._colors = [tile.toImage().pixel(0, 0).rgb()]

    def index(self, idx):
        """Given an index, returns the character at that location in the font.

        Please note that this function assumes that even variable-width fonts
        are stored in a fixed-width grid.
        """
        tpr = int(self._image.width() / self.width)
        row = int(idx / tpr)
        column = idx % tpr

        x = column * self.width
        y = row * self.height

        if (x > self._image.width()) or (y > self._image.height()):
            raise ValueError('out of bounds: {}'.format(idx))

        return self._image.copy(x, y, self.width, self.height).toImage()

    @property
    def palette(self):
        return self._colors

    @property
    def width(self):
        return self._json['width']

    @property
    def height(self):
        return self._json['height']

    @property
    def table(self):
        return self._json['map']

    def length(self, text):
        """Calculate the pixel-wise length of the given string."""
        return sum(self.table[x]['width'] for x in text)
