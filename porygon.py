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

def linear1(tile, *args):
    data = bytearray()

    for y in range(8):
        byte = 0

        for x in range(8):
            if tile.pixelIndex(x, y) > 0:
                byte += 2**(8 - x)

        data.append(byte)

    return bytes(data)

def linear2(tile, palette):
    data = bytearray()

    for y in range(8):
        bp1 = 0
        bp2 = 0

        for x in range(8):
            pixel = tile.pixelIndex(x, y)
            if palette is not None:
                pixel = palette[pixel]

            a = pixel & 0x1
            b = pixel & 0x2
            if a:
                bp1 += 2**(7 - x)
            if b:
                bp2 += 2**(7 - x)

        data.extend((bp1, bp2))

    return bytes(data)

def planar2(tile, palette):
    data = bytearray()

    for y in range(8):
        byte = 0

        for x in range(4):
            pixel = tile.pixelIndex(x, y)
            if palette is not None:
                pixel = palette[pixel]
            pixel &= 0x3
            byte = byte + (pixel << x * 2)

        data.append(byte)
        byte = 0

        for x in range(4, 8):
            pixel = tile.pixelIndex(x, y)
            pixel &= 0x3
            byte = byte + (pixel << x * 2)

        data.append(byte)

    return bytes(data)

def linear4(tile, palette):
    data = bytearray()

    for y in range(8):
        bp1 = 0
        bp2 = 0

        for x in range(8):
            pixel = tile.pixelIndex(x, y)
            if palette is not None:
                pixel = palette[pixel]

            a = pixel & 0x1
            b = pixel & 0x2

            if a:
                bp1 += 2**(7 - x)
            if b:
                bp2 += 2**(7 - x)

        data.extend((bp1, bp2))
        
    for y in range(8):
        bp3 = 0
        bp4 = 0
        
        for x in range(8):
            pixel = tile.pixelIndex(x,y)
            a = pixel & 0x4
            b = pixel & 0x8
            
            if a:
                bp3 += 2**(7-x)
            if b:
                bp4 += 2**(7-x)
        
        data.extend((bp3,bp4))
        
    return bytes(data)

def padded4_2(tile, palette):
    data = bytearray()

    for y in range(8):
        bp1 = 0
        bp2 = 0

        for x in range(8):
            pixel = tile.pixelIndex(x, y)
            if palette is not None:
                pixel = palette[pixel]

            a = pixel & 0x1
            b = pixel & 0x2

            if a:
                bp1 += 2**(7 - x)
            if b:
                bp2 += 2**(7 - x)

        data.extend((bp1, bp2))
        
    for y in range(8):
        bp3 = 0
        bp4 = 0
        
        data.extend((bp3,bp4))
        
    return bytes(data)

def planar4(tile, palette):
    data = bytearray()

    for y in range(8):
        byte = 0

        for x in range(2):
            pixel = tile.pixelIndex(x, y)
            if palette is not None:
                pixel = palette[pixel]
            pixel &= 0x7
            byte = byte + (pixel << x * 4)

        data.append(byte)
        byte = 0

        for x in range(2, 4):
            pixel = tile.pixelIndex(x, y)
            pixel &= 0x7
            byte = byte + (pixel << x * 4)

        data.append(byte)
        byte = 0

        for x in range(4, 6):
            pixel = tile.pixelIndex(x, y)
            pixel &= 0x7
            byte = byte + (pixel << x * 4)

        data.append(byte)
        byte = 0

        for x in range(6, 8):
            pixel = tile.pixelIndex(x, y)
            pixel &= 0x7
            byte = byte + (pixel << x * 4)

        data.append(byte)

    return bytes(data)


# Add new formats to this dict as they are implemented.
formats = {
    '1bpp':     linear1,
    'linear2':  linear2,
    'planar2':  planar2,
    'nes2':     planar2,
    'gb2':      linear2,
    'snes2':    linear2,
    'gbc2':     linear2,
    'linear4':  linear4,
    'planar4':  planar4,
    'snes4':    linear4,
    'pce4':     linear4,
    'padded4_2': padded4_2
}

def main():
    app = QGuiApplication(sys.argv)

    if len(sys.argv) < 3 or sys.argv[2] not in formats.keys():
        print(
            '''Usage: porygon.py image format

image is an image file in PNG. The base filename is also used to find a
mapper in order to force palette modifications.

format is one of the supported formats:'''
        )
        for format in formats.keys():
            print('* {}'.format(format))
        sys.exit(1)

    (image, format) = sys.argv[1:3]
    (image_base, ext) = op.splitext(image)
    output = '{}.bin'.format(image_base)
    mapper = image_base + '.txt'

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

    palette = {}
    if op.exists(mapper):
        print('Palette found. Loading...')
        with open(mapper, mode='r') as f:
            text = f.read().split('\n')

        for line in text:
            if line == '':
                continue
            a = line.split('=')

            key = int(a[0])
            value = int(a[1])
            palette[key] = value
    else:
        print('No palette found.')
        palette = None

    print('Converting to {}'.format(format))
    counter = 0
    with open(output, mode='wb') as f:
        for row in range(rows):
            for column in range(columns):
                tile = data.copy(column * 8, row * 8, 8, 8)
                f.write(formats[format](tile, palette))
                counter += 1

if __name__ == '__main__':
    main()
