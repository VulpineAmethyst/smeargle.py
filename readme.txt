Smeargle 0.2.1 readme
-------------------
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

Raw output
----------
The raw output is fairly simple. For 2bpp, four pixels are encoded at a time.
For 3bpp, six pixels are encoded at a time. For 4bpp, only two are encoded at
a time. Raw output looks like:

    2bpp [0123]     ->                       0b11100100
    3bpp [01234543] -> 0b01110010 0b01000110 0b10001000
    4bpp [01]       ->                       0b00010000

Note that it doesn't matter how the pixels are arranged in the original image;
your code should be aware of the image dimensions regardless.