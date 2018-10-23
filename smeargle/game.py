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
import os.path

from smeargle.font import Font
from smeargle.script import Script

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
            'min_tiles_per_line': 0,
            'output_format': None,
            'tile_offset': 0,
            'leading_zeroes': False,
            'raw_fn': None,
            'deduped_fn': None,
            'tilemap_fn': None,
            'little_endian': False,
        }

        for script, data in self._data['scripts'].items():

            # Add defaults to script data if not present
            for k, v in defaults.items():
                if k not in data:
                    data[k] = v

            if data['output_format'] not in valid_formats:
                raise ValueError("output_format must be one of {} or omitted entirely".format(valid_formats[:-1]))

            self._scripts[script] = (
                Script(filename=script, **data),
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
