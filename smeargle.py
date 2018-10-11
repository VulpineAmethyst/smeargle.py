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
import os

from PyQt5.QtGui import QGuiApplication

from smeargle.game import Game

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
