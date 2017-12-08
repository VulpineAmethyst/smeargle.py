#!/usr/bin/env python3
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
import os.path as op

from PyQt5.QtGui import QImage, QPixmap, QPainter, QGuiApplication

def linear1(tile):
    data = bytearray()

    for y in range(8):
        byte = 0

        for x in range(8):
            if tile.pixelIndex(x, y) > 0:
                byte += 2**x

        data.insert(0, byte)

    return bytes(data)

def linear2(tile):
    data = bytearray()

    for y in range(8):
        bp1 = 0
        bp2 = 0

        for x in range(8):
            pixel = tile.pixelIndex(x, y)

            a = pixel % 2
            b = int(pixel / 2)
            if a >= 1:
                bp1 += 2**x
            if b >= 1:
                bp2 += 2**x

        data.insert(0, bp2)
        data.insert(0, bp1)

    return bytes(data)

def planar2(tile):
    data = bytearray()

    for y in range(8):
        byte = 0

        for x in range(4):
            pixel = tile.pixelIndex(x, y)
            byte = byte & (pixel << (4 - x))

        data.insert(0, byte)
        byte = 0

        for x in range(4, 8):
            pixel = tile.pixelIndex(x, y)
            byte = byte & (pixel << (8 - x))

        data.insert(0, byte)

    return bytes(data)

def linear4(tile):
    data = bytearray()

    for y in range(8):
        bp1 = 0
        bp2 = 0
        bp3 = 0
        bp4 = 0

        for x in range(8):
            pixel = tile.pixelIndex(x, y)

            a = pixel & 0x1
            b = pixel & 0x2
            c = pixel & 0x4
            d = pixel & 0x8
            if a:
                bp1 += 2**x
            if b:
                bp2 += 2**x
            if c:
                bp3 += 2**x
            if d:
                bp3 += 2**x

        data.insert(0, bp4)
        data.insert(0, bp3)
        data.insert(0, bp2)
        data.insert(0, bp1)

    return bytes(data)

# Add new formats to this dict as they are implemented.
formats = {
    '1bpp':    linear1,
    'linear2': linear2,
    'planar2': planar2,
    'linear4': linear4,
    'nes2':    planar2,
    'gb2':     linear2,
    'snes2':   linear2,
    'gbc2':    linear2,
    'snes4':   linear4,
    'pce4':    linear4,
}

def main():
    app = QGuiApplication(sys.argv)

    if len(sys.argv) < 3 or sys.argv[2] not in formats.keys():
        print(
            '''Usage: porygon.py image format

image is an image file in PNG.

format is one of the supported formats:'''
        )
        for format in formats.keys():
            print('* {}'.format(format))
        sys.exit(1)

    (image, format) = sys.argv[1:3]
    (image_base, ext) = op.splitext(image)
    output = '{}.bin'.format(image_base)

    if not op.exists('output/'):
        import os
        os.mkdir('output')
    if not output.startswith('output/'):
        output = 'output/{}'.format(output)

    bpp = int(format[-1])

    print('Loading image...')
    data = QImage(image)
    data = data.convertToFormat(QImage.Format_Indexed8)
    if data.colorCount() > 2**bpp:
        raise ValueError('image has too many colors')

    width = data.width()
    height = data.height()
    rows = int(height / 8)
    columns = int(width / 8)

    print('Converting to {}'.format(format))
    with open(output, mode='wb') as f:
        for row in range(rows):
            for column in range(columns):
                tile = data.copy(row * 8, column * 8, 8, 8)
                f.write(formats[format](tile))

if __name__ == '__main__':
    main()
