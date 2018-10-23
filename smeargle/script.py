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

from math import floor, ceil

from PyQt5.QtGui import QPainter, QImage

from smeargle.font import Font

def get_or_default(d, key, default):
    if key not in d:
        return default
    return d[key]

class Script:
    def __init__(self, filename, **kwargs):
        self._cfg = {
            'max_tiles':      get_or_default(kwargs, 'max_tiles_per_line', 0),
            'min_tiles':      get_or_default(kwargs, 'min_tiles_per_line', 0),
            'output_format':  get_or_default(kwargs, 'output_format',      None),
            'tile_offset':    get_or_default(kwargs, 'tile_offset',        0),
            'leading_zeroes': get_or_default(kwargs, 'leading_zeroes',     False),
            'raw_fn':         get_or_default(kwargs, 'raw_fn',             None),
            'deduped_fn':     get_or_default(kwargs, 'deduped_fn',         None),
            'tilemap_fn':     get_or_default(kwargs, 'tilemap_fn',         None),
            'little_endian':  get_or_default(kwargs, 'little_endian',      False),
        }
        mint = self._cfg['min_tiles']
        maxt = self._cfg['max_tiles']

        if mint > maxt and maxt != 0:
            raise ValueError('minimum tiles per line higher than maximum')

        with open(filename, mode='r', encoding='UTF-8') as f:
            self._text = f.read().split('\n')

        self._painter = QPainter()

    @property
    def raw_fn(self):
        return self._cfg['raw_fn']

    @property
    def deduped_fn(self):
        return self._cfg['deduped_fn']

    @property
    def tilemap_fn(self):
        return self._cfg['tilemap_fn']

    @property
    def output_format(self):
        return self._cfg['output_format']

    @property
    def leading_zeroes(self):
        return self._cfg['leading_zeroes']
    
    @property
    def tile_offset(self):
        return self._cfg['tile_offset']
    
    def render_lines(self, font):
        table = font.table
        lines = []
        max_tiles = self._cfg['max_tiles'] * font.width
        min_tiles = self._cfg['min_tiles'] * font.width

        for line in self._text:
            if len(line) < 1:
                continue
            length = font.length(line)
            length = ceil(length / font.width) * font.width

            if max_tiles > 0:
                if 0 < max_tiles < length:
                    print('WARNING: "{}" exceeds {} tiles by {}px; truncating.'.format(
                        line,
                        int(max_tiles / font.width),
                        length - max_tiles
                    ))
                    length = max_tiles
            if min_tiles > 0:
                if 0 < length < min_tiles:
                    print('INFO: "{}" is shorter than {} tiles by {}px'.format(
                        line,
                        int(min_tiles / font.width),
                        min_tiles - length
                    ))
                    length = min_tiles
            image = QImage(length, font.height, QImage.Format_RGB32)
            image.fill(font.palette[0])
            pos = 0

            self._painter.begin(image)
            for glyph in line:
                width = font.table[glyph]['width']
                if pos + width >= max_tiles and max_tiles > 0:
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
                            if self._cfg['little_endian']:
                                temp = upper_val
                                upper_val = lower_val
                                lower_val = temp
                            map_idx[data] = "<${:02x}><${:02x}>".format(upper_val, lower_val)
                        else:
                            map_idx[data] = "<${:02x}>".format(lower_val)
                    elif self.output_format == 'thingy':
                        index = unique + self.tile_offset
                        upper_val = int(floor(index / 256))
                        lower_val = int(index % 256)
                        if upper_val > 0 or self.leading_zeroes is True:
                            if self._cfg['little_endian']:
                                temp = upper_val
                                upper_val = lower_val
                                lower_val = temp
                            map_idx[data] = "{:02x}{:02x}".format(upper_val, lower_val)
                        else:
                            map_idx[data] = "{:02x}".format(lower_val)
                    else:
                        index = unique + self.tile_offset
                        upper_val = int(floor(index / 256))
                        lower_val = int(index % 256)
                        if upper_val > 0 or self.leading_zeroes is True:
                            if self._cfg['little_endian']:
                                temp = upper_val
                                upper_val = lower_val
                                lower_val = temp
                            map_idx[data] = '0x{:02x}{:02x}'.format(upper_val, lower_val)
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

__all__ = ['Script']
