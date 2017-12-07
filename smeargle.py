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

import sys
import json
import os.path as op
from math import ceil

from PyQt5.QtGui import QImage, QPixmap, QPainter, QGuiApplication

def pack(bits=2, bytes=()):
    min = 0
    max = 2**bits - 1
    base = 0
    shift = 0
    ret = bytearray()

    for byte in bytes:
        if byte > max:
            raise ValueError('{} exceeds bit cap'.format(bin(byte)))

        base = base + ((byte & max) << shift)
        shift += bits

    while base > 0:
        byte = base & 0xFF
        ret.append(byte)
        base -= 256

    ret.reverse()

    return ret

def export(image, filename, bits=2):
    if bits == 2:
        write = 4
    elif bits == 3:
        write = 8
    elif bits == 4:
        write = 2
    else:
        raise ValueError('too many bits per pixel')

    if image.colorCount() > 2**bits:
        raise ValueError('too many colors')

    with open(filename, mode='wb') as f:
        qwidth = int(image.width() / write)

        for y in range(image.height()):
            for qx in range(qwidth):
                if write == 4:
                    packing = (
                        image.pixelIndex(qx * write + 0, y),
                        image.pixelIndex(qx * write + 1, y),
                        image.pixelIndex(qx * write + 2, y),
                        image.pixelIndex(qx * write + 3, y)
                    )
                elif write == 2:
                    packing = (
                        image.pixelIndex(qx * write + 0, y),
                        image.pixelIndex(qx * write + 1, y)
                    )
                elif write == 6:
                    packing = (
                        image.pixelIndex(qx * write + 0, y),
                        image.pixelIndex(qx * write + 1, y),
                        image.pixelIndex(qx * write + 2, y),
                        image.pixelIndex(qx * write + 3, y),
                        image.pixelIndex(qx * write + 4, y),
                        image.pixelIndex(qx * write + 5, y),
                        image.pixelIndex(qx * write + 6, y),
                        image.pixelIndex(qx * write + 7, y),
                    )

                f.write(pack(bits, packing))

class Font(QPixmap):
    """A simple class for basic bitmap fonts."""
    def __init__(self, filename, width=8, height=8):
        super().__init__(filename)
        self._width = width
        self._height = height

        self._tpr = int(self.width() / self._width)

    def index(self, tile):
        row    = int(tile / self._tpr)
        column = tile % self._tpr

        x = column * self._width
        y = row * self._height
        if (x > self.width()) or (y > self.height()):
            raise KeyError('index')

        return self.copy(x, y, self._width, self._height)

def main():
    if len(sys.argv) < 2:
        print(
            """Usage: smeargle.py font.json script

            font.json is the metadata file associated with the font.

            script is the text to be typeset.

            The PNG and raw binary outputs will be exported using the script filename
            as a base. (ex: test.txt -> test.png & test.bin)
            """
        )
        sys.exit(1)

    app = QGuiApplication(sys.argv)

    (font, script) = sys.argv[1:3]
    font_info = None
    script_base, ext = op.splitext(script)
    output = script_base + '.png'
    output_raw = script_base + '.bin'

    print('Loading font information...')
    with open(font, mode='rb') as f:
        font_info = json.load(f)

    print('Loading font data...')
    font_data = Font(font_info['filename'], font_info['width'], font_info['height'])

    print('Loading text...')
    with open(script, mode='r', encoding='utf-8', errors='replace') as f:
        text = f.read()

    images = []
    fmap = font_info['map']
    width = font_info['width']
    height = font_info['height']
    line = 0
    lines = text.split('\n')
    painter = QPainter()
    filler = font_data.index(fmap[' ']['index']).toImage().pixel(0, 0)

    print('Rendering text...')
    scriptmap = {}
    while len(images) < text.count('\n'):
        position = 0

        temp = QImage(width * len(lines[line]), height, QImage.Format_RGB32)
        temp.fill(filler)

        painter.begin(temp)
        for char in lines[line]:
            if char in fmap.keys():
                glyph = font_data.index(fmap[char]['index'] - 1)
                painter.drawImage(position, 0, glyph.toImage())
                painter.save()
                position += fmap[char]['width']
            else:
                print('WARNING: unknown glyph "{}"'.format(char))
        painter.end()
        temp = temp.copy(0, 0, ceil(position / width) * width, height)
        images.append(temp)
        scriptmap[lines[line]] = temp
        line += 1

    print('Text rendered. Generating tilemap...')
    tilemap = {}
    tilemap_index = {}
    counter_unique = 0
    counter_total  = 0
    for line, image in scriptmap.items():
        iwidth = image.width()
        tiles = int(iwidth / width)
        column = 0
        text_tiles = []

        while tiles > 0:
            tile = image.copy(column, 0, width, height).convertToFormat(QImage.Format_Indexed8)
            data = bytearray()

            for y in range(tile.height()):
                for x in range(tile.width()):
                    data.append(tile.pixelIndex(x, y))

            data = bytes(data)

            if data not in tilemap.keys():
                tilemap[data] = tile
                tilemap_index[data] = str(counter_unique)
                counter_unique += 1

            text_tiles.append(tilemap_index[data])

            counter_total += 1

            column += width
            tiles -= 1

        scriptmap[line] = text_tiles

    print('Tilemap generated, with {} tiles mapped ({} unique). Rendering tilemap...'.format(counter_total, counter_unique))
    image = QImage(width * 16, ceil(len(tilemap.keys()) / 16) * height, QImage.Format_RGB32)
    image.fill(filler)
    painter.begin(image)
    (row, column) = (0, 0)
    for data, tile in tilemap.items():
        painter.drawImage(column, row, tile)
        if column < (width * 16 - width):
            column += width
        else:
            column = 0
            row += height
    painter.end()

    print('Writing line <-> tilemap indexing...')
    with open(script_base + '_index.txt', mode='w') as f:
        for line, index in scriptmap.items():
            f.write('{} -> {}\n'.format(line, ', '.join(index)))

    print('Saving rendered tilemap...')
    file = QPixmap.fromImage(image)
    file.save(output, 'PNG')
    print('Exporting as 2bpp...')
    export(image.convertToFormat(QImage.Format_Indexed8), output_raw, font_info['bits_per_pixel'])

if __name__ == '__main__':
    main()
