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

from PyQt5.QtGui import QImage, QPixmap, QPainter, QGuiApplication

def linear1(tile):
    data = bytearray()

    for y in range(8):
        byte = 0

        for x in range(8):
            if tile.pixelIndex(x, y) > 0:
                byte += 2**x

        data.append(byte)

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
            if a == 1:
                bp1 += 2**x
            if b == 1:
                bp2 += 2**x

        data.extend((bp1, bp2))

    return bytes(data)

def planar2(tile):
    data = bytearray()

    for y in range(8):
        byte = 0

        for x in range(4):
            pixel = tile.pixelIndex(x, y)
            byte = byte & (pixel << (4 - x))

        data.append(byte)
        byte = 0

        for x in range(4, 8):
            pixel = tile.pixelIndex(x, y)
            byte = byte & (pixel << (8 - x))

        data.append(byte)

    return bytes(data)

# Add new formats to this dict as they are implemented.
formats = {
    '1bpp':    linear1,
    'linear2': linear2,
    'planar2': planar2,
    'nes2':    planar2,
    'gb2':     linear2,
    'snes2':   linear2,
    'gbc2':    linear2,
}

def main():
    app = QGuiApplication(sys.argv)

    if len(sys.argv < 3):
        print(
            '''Usage: porygon.py image format

            image is an image file in PNG.

            format is one of the supported formats:
            '''
        )
        for format in formats.keys():
            print('* {}'.format(format))
