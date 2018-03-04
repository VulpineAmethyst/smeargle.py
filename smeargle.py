#!/usr/bin/env python3

import json
from math import ceil

from PyQt5.QtGui import QGuiApplication, QPixmap, QImage, QColor, QPainter

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
        return sum(self.table[x]['width'] for x in text)

class Script:
    def __init__(self, filename):
        with open(filename, mode='r', encoding='UTF-8') as f:
            self._text = f.read().split('\n')

        self._painter = QPainter()

    def render_lines(self, font):
        table = font.table
        lines = []

        for line in self._text:
            if len(line) < 1:
                continue
            length = font.length(line)
            length = ceil(length / font.width) * font.width
            image = QImage(length, font.height, QImage.Format_RGB32)
            image.fill(font.palette[0])
            pos = 0

            self._painter.begin(image)
            for glyph in line:
                width = font.table[glyph]['width']
                self._painter.drawImage(pos, 0, font.index(font.table[glyph]['index'] - 1))

                pos += width
            self._painter.end()

            lines.append((line, image, length, len(lines)))

        return lines

    def generate_tilemap(self, font, lines):
        tilemap = {}
        raw_tiles = []
        compressed_tiles = []
        map_idx = {}
        unique = total = 0
        indexes = []

        for line in lines:
            (text, image, length, lineno) = line
            tile_idx = []

            # number of tiles in this line
            count = int(length / font.width)

            column = 0

            while count > 0:
                tile = image.copy(column, 0, font.width, font.height)
                if len(font.palette) > 1:
                    tile = tile.convertToFormat(QImage.Format_Indexed8, font.palette)
                else:
                    tile = tile.convertToFormat(QImage.Format_Indexed8)
                data = bytearray()

                for y in range(tile.height()):
                    for x in range(tile.width()):
                        data.append(tile.pixelIndex(x, y))

                data = bytes(data)

                if data not in tilemap.keys():
                    tilemap[data] = tile
                    compressed_tiles.append(tile)
                    map_idx[data] = '0x{:02x}'.format(unique)
                    unique += 1

                raw_tiles.append(tile)
                tile_idx.append(map_idx[data])
                total += 1
                column += font.width
                count -= 1

            indexes.append((text, ' '.join(tile_idx)))
        return (compressed_tiles, raw_tiles, map_idx, indexes, total, unique)

    def render_tiles(self, font, tiles):
        image = QImage(font.width * 16, ceil(len(tiles) / 16) * font.height, QImage.Format_RGB32)
        image.fill(font.palette[0])

        (row, column) = (0, 0)

        self._painter.begin(image)
        for tile in tiles:
            self._painter.drawImage(column, row, tile)

            if column < (font.width * 15):
                column += font.width
            else:
                column = 0
                row += font.height
        self._painter.end()

        if len(font.palette) > 1:
            return image.convertToFormat(QImage.Format_Indexed8, font.palette)
        else:
            return image.convertToFormat(QImage.Format_Indexed8)

    def render_tiles_to_file(self, font, tiles, filename):
        self.render_tiles(font, tiles).save(filename, 'PNG')

if __name__ == '__main__':
    import sys
    import os.path
    
    if len(sys.argv) < 1:
        print('Usage: smeargle.py font.json script.txt')
        print('\nPlease see the included readme.txt for documentation on the font metadata.')
        sys.exit(-1)

    app = QGuiApplication(sys.argv)

    font   = sys.argv[1]
    script = sys.argv[2]
    render_path = sys.argv[3] if len(sys.argv) > 3 else 'output'

    filebase = os.path.split(script)[-1]
    name, ext = os.path.splitext(filebase)

    output_raw  = os.path.join(render_path, name + '_raw.png')
    output_comp = os.path.join(render_path, name + '_compressed.png')
    output_map  = os.path.join(render_path, name + '_index.txt')

    print("Loading font...", end='')
    font = Font(font)
    print("done.")

    print("Loading script...", end='')
    script = Script(script)
    print("done.")

    print("Rendering text...", end='')
    lines = script.render_lines(font)
    print("done.")

    print("Generating tilemap...", end='')
    (compressed, raw, map_index, indexes, total, unique) = script.generate_tilemap(font, lines)
    print("{} tiles generated, {} unique.".format(total, unique))

    print('Writing compressed tiles...', end='')
    script.render_tiles_to_file(font, compressed, output_comp)
    print('done.')

    print('Writing raw tiles...', end='')
    script.render_tiles_to_file(font, raw, output_raw)
    print('done.')

    print('Writing map index...', end='')
    with open(output_map, mode='wt') as f:
        for text, index in indexes:
            f.write('{} = {}\n'.format(text, index))
    print('done.')

    print()
    print('Raw tiles:   ', output_raw)
    print('Compressed:  ', output_comp)
    print('Tile<->text: ', output_map)
