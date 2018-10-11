Smeargle 0.7.0 readme
---------------------
Usage: smeargle.py game.json

game.json is a file which follows the Game JSON format outlined below.

Output
------
Smeargle outputs three files per script, at present:

* <script>_raw.png is the undeduplicated rendering of the script with the
  specified font.
* <script>_compressed.png deduplicates tiles to provide the most compact
  rendering of the font without delving into actual compression algorithms.
* <script>_index.txt provides a mapping of deduplicated tiles to the original
  text.

These filenames can be configured on an individual script basis; see game.json
documentation below.

game.json format
----------------
The following format MUST be observed, or you will not get the output you want.
Remove '//' and everything following it in each line if you plan to cop/paste
this example for your own use. Do not leave a trailing comma on the final entry
in each object or array.

{
    "name": "Example",                    // The name of the game, for reference.
    "fonts": {
        "Melissa 8": "melissa8.json"       // Font name and its filename.
    }, "scripts": {
        "test.txt": {                      // Script filename.
            "font": "Melissa 8",           // Reference to the font table, above.
            "max_tiles_per_line": 8,       // Optional: set to 0 for unlimited tiles.
            "min_tiles_per_line": 0,       // Optional: Non-zero enforces a minimum tile-wise width.
            "output_format": "thingy",     // Optional: Output format for tilemap. "thingy", "atlas"
            "leading_zeroes": true,        // Optional: Forces 16-bit tilemap output (i.e. 0x0012 instead of 0x12)
            "tile_offset": 256,            // Optional: Constant to add to tile index (first tile: 0x0000 + 256 = 0x0100)
            "raw_fn": "ex_raw.png",        // Optional: Output filename for raw graphic tile data.
            "deduped_fn": "ex_comp.png",   // Optional: Output filename for deduped tile data.
            "tilemap_fn": "example.tbl"    // Optional: Output filename for tilemap text.
        }
    }
}

font.json format
----------------
The following format MUST be observed, or you will not get the output you want.
Remove '//' and everything following it in each line if you plan to copy/paste
this example for your own use. Do not leave a trailing comma on the final entry
in each object or array.

{
    "font_name": "Example",               // Human-readable, not currently used
    "filename": "example.png",            // Filename of the font (PNG)
    "bits_per_pixel": 2,                  // Depth in bits; 2**n is color count
    "width":  8,                          // Width of a given tile
    "height": 8,                          // Height of a given tile
    "palette": [                          // A list of colors.
        '00bbbb',                         // A color in hex format.
        [0, 0, 0]                         // A color in R,G,B format.
    ],
    "map": {                              // character -> index & width
        " ":  {"index": 115, "width": 4}, // Must be a blank tile somewhere
    }
}

The first color in the palette is assumed to be the background color.

porygon.py
----------
Usage: porygon.py image format

This script converts the image into the target format. Run porygon.py without
arguments to see what formats are available.

Changelog
---------
0.7.0
* Add an optional argument to script JSON:
** min_tiles_per_line: enforce a minimum tile count per line.
* Split classes out to separate files.
* Add girafarig, a simple script for interpolating 1bpp graphics.

0.6.0
* Adds several optional arguments to script json elements:
** output_format: determines how the tilemap text file gets rendered. Possible
   values are "atlas", "thingy", null
** leading_zeroes: Forces tilemap output to always be 16-bit.
** tile_offset: Adds a constant value to the tile index. Useful if you want the
   tilemap to start counting somewhere other than zero.
** raw_fn: Filename for raw tile graphic png output.
** deduped_fn: Filename for compressed tile graphic png output.
** tilemap_fn: Filename for text index tilemap file.

0.5.0
* Introduce a master 'game.json' file in order to enable batch processing, for
  games which use multiple scripts that have different fonts or rendering
  requirements.
* Emit an error if no arguments are given.

0.4.0
* A complete rewrite of Smeargle to make it more modular.
* Implemented a palette feature in order to ensure strict palette ordering in
  the output images.

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
