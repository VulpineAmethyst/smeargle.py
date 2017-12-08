Smeargle 0.3.0 readme
---------------------
Usage: smeargle.py font.json script.txt

font.json is a JSON document which describes the font and provides a mapping
of characters to font indexes and font widths.

script.txt is a plaintext document without formatting which is rendered as an
image in both PNG and raw binary formats.

Script output
-------------
The following files are emitted when Smeargle is run:

* script.png contains the rendered script with deduplication, formatted
  compactly. This is provided so that you can use your favourite viewer to
  inspect the output.
* script.bin is almost identical to the above; the difference is that it has
  been converted to your font's bitdepth directly.
* script_index.txt provides an index mapping which tells you how to index
  into the rendered tilemap to reproduce the text.

font.json format
----------------
The following format MUST be observed, or you will not get the output you want.
Remove '//' and everything following it in each line if you plan to copy/paste
this example for your own use. Do not leave a trailing comma on the final entry
in the map.

{
    "font_name": "Example",               // Human-readable, not currently used
    "filename": "example.png",            // Filename of the font (PNG)
    "bits_per_pixel": 2,                  // Depth in bits; 2**n is color count
    "width":  8,                          // Width of a given tile
    "height": 8,                          // Height of a given tile
    "map": {                              // character -> index & width
        " ":  {"index": 115, "width": 4}, // Must be a blank tile somewher
    }
}

porygon.py
----------
Usage: porygon.py image format

This script converts the image into the target format. Run porygon.py without
arguments to see what formats are available.

Changelog:
0.3.3
* Added support for palette maps. Format is, one per line, 'n=m', where n and
  m must be integers within the colour range for the format.

0.3.2
* Added Linear 4 bits-per-pixel format.

0.3.1
* Make supported formats actually work.

0.3.0
* Added porygon.py script. Linear 1 & 2 and planar 2 bits-per-pixel formats
  are supported.

0.2.2
* Removed binary output. It wasn't emitting anything actually useful to anyone.
* Emit index map as hex.
