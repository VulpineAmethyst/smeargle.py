#!/usr/bin/env python3

import json
from math import ceil, floor

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
        """Calculate the pixel-wise length of the given string."""
        return sum(self.table[x]['width'] for x in text)


class Script:
    def __init__(self, filename, raw_fn=None, deduped_fn=None, tilemap_fn=None,
                 max_tiles=0, output_format=None, tile_offset=0, leading_zeroes=False):
        self.max_tiles = max_tiles
        self.output_format = output_format
        self.tile_offset = tile_offset
        self.leading_zeroes = leading_zeroes
        self.raw_fn = raw_fn
        self.deduped_fn = deduped_fn
        self.tilemap_fn = tilemap_fn
        with open(filename, mode='r', encoding='UTF-8') as f:
            self._text = f.read().split('\n')

        self._painter = QPainter()

    def render_lines(self, font):
        table = font.table
        lines = []
        max_tiles = self.max_tiles * font.width

        for line in self._text:
            if len(line) < 1:
                continue
            length = font.length(line)
            length = ceil(length / font.width) * font.width
            if 0 < max_tiles < length:
                print('WARNING: "{}" exceeds {} tiles by {}px; truncating.'.format(
                    line,
                    int(max_tiles / font.width),
                    length - max_tiles
                ))
                length = max_tiles
            image = QImage(length, font.height, QImage.Format_RGB32)
            image.fill(font.palette[0])
            pos = 0

            self._painter.begin(image)
            for glyph in line:
                width = font.table[glyph]['width']
                if pos + width >= max_tiles:
                    break
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
                    if self.output_format == 'atlas':
                        index = unique + self.tile_offset
                        upper_val = int(floor(index / 256))
                        lower_val = int(index % 256)
                        if upper_val > 0 or self.leading_zeroes is True:
                            map_idx[data] = "<${:02x}><${:02x}>".format(upper_val, lower_val)
                        else:
                            map_idx[data] = "<${:02x}>".format(lower_val)
                    elif self.output_format == 'thingy':
                        index = unique + self.tile_offset
                        upper_val = int(floor(index / 256))
                        lower_val = int(index % 256)
                        if upper_val > 0 or self.leading_zeroes is True:
                            map_idx[data] = "{:02x}{:02x}".format(upper_val, lower_val)
                        else:
                            map_idx[data] = "{:02x}".format(lower_val)
                    else:
                        if self.leading_zeroes:
                            map_idx[data] = '0x{:04x}'.format(unique + self.tile_offset)
                        else:
                            map_idx[data] = '0x{:02x}'.format(unique + self.tile_offset)
                    unique += 1

                raw_tiles.append(tile)
                tile_idx.append(map_idx[data])
                total += 1
                column += font.width
                count -= 1

            if self.output_format is None:
                indexes.append((text, ' '.join(tile_idx)))
            else:
                indexes.append((text, ''.join(tile_idx)))
        return compressed_tiles, raw_tiles, map_idx, indexes, total, unique

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


class Game:
    def __init__(self, filename):
        with open(filename, mode='rb') as f:
            self._data = json.load(f)

        self._fonts = {}
        self._scripts = {}

        for name, file in self._data['fonts'].items():
            self._fonts[name] = Font(file)

        valid_formats = ['thingy', 'atlas', None]
        defaults = {
            'max_tiles_per_line': 0,
            'output_format': None,
            'tile_offset': 0,
            'leading_zeroes': False,
            'raw_fn': None,
            'deduped_fn': None,
            'tilemap_fn': None
        }

        for script, data in self._data['scripts'].items():

            # Add defaults to script data if not present
            for k, v in defaults.items():
                if k not in data:
                    data[k] = v

            if data['output_format'] not in valid_formats:
                raise ValueError("output_format must be one of {} or omitted entirely".format(valid_formats[:-1]))

            self._scripts[script] = (
                Script(filename=script,
                       raw_fn=data['raw_fn'],
                       deduped_fn=data['deduped_fn'],
                       tilemap_fn=data['tilemap_fn'],
                       max_tiles=data['max_tiles_per_line'],
                       output_format=data['output_format'],
                       tile_offset=data['tile_offset'],
                       leading_zeroes=data['leading_zeroes']),
                self._fonts[data['font']]
            )

    @property
    def fonts(self):
        return tuple(self._fonts.keys())

    @property
    def scripts(self):
        return tuple(self._scripts.keys())

    def render_script(self, script, render_path, output=False):
        if script not in self._scripts.keys():
            raise KeyError('unknown script')

        filebase = os.path.split(script)[-1]
        name, ext = os.path.splitext(filebase)

        script, font = self._scripts[script]

        if script.raw_fn is None:
            output_raw = os.path.join(render_path, name + '_raw.png')
        else:
            output_raw = os.path.join(render_path, script.raw_fn)

        if script.deduped_fn is None:
            output_comp = os.path.join(render_path, name + '_compressed.png')
        else:
            output_comp = os.path.join(render_path, script.deduped_fn)

        if script.tilemap_fn is None:
            output_map = os.path.join(render_path, name + '_index.txt')
        else:
            output_map = os.path.join(render_path, script.tilemap_fn)

        if output: print('Rendering text...')
        lines = script.render_lines(font)
        if output: print('Text rendered.')

        if output: print("Generating tilemap...", end='')
        (compressed, raw, map_index, indexes, total, unique) = script.generate_tilemap(font, lines)
        if output: print("{} tiles generated, {} unique.".format(total, unique))

        if output: print('Writing compressed tiles...', end='')
        script.render_tiles_to_file(font, compressed, output_comp)
        if output: print('done.')

        if output: print('Writing raw tiles...', end='')
        script.render_tiles_to_file(font, raw, output_raw)
        if output: print('done.')

        if output: print('Writing map index...', end='')
        with open(output_map, mode='wt') as f:
            for text, index in indexes:
                if script.output_format == 'thingy':
                    f.write('{}={}\n'.format(index, text))
                else:
                    f.write('{} = {}\n'.format(text, index))
        if output: print('done.')

        if output:
            print()
            print('Raw tiles:   ', output_raw)
            print('Compressed:  ', output_comp)
            print('Tile<->text: ', output_map)


if __name__ == '__main__':
    import sys
    import os

    if len(sys.argv) < 1:
        print('Usage: smeargle.py game.json [output_directory]')
        print('\nPlease see the included readme.txt for documentation on file formats.')
        sys.exit(-1)

    app = QGuiApplication(sys.argv)
    render_path = sys.argv[2] if len(sys.argv) > 2 else 'output'
    if not os.path.exists(render_path):
        os.mkdir(render_path, mode=0o644)

    print('Loading game data from {}...'.format(sys.argv[1]), end='')
    game = Game(sys.argv[1])
    print('done.')

    for script in game.scripts:
        print('Processing {}...'.format(script))
        game.render_script(script, render_path, output=True)
        print('{} processed.'.format(script))
