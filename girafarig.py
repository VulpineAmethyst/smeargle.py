import sys

"""
Super basic simple stupid script to interpolate 1bpp font graphics from smeargle/porygon
"""

def main():
  if len(sys.argv) != 3:
    raise ValueError("syntax is girafarig.py infile.bin outfile.bin")
  in_filename = sys.argv[1]
  outfile = sys.argv[2]

  with open(in_filename, "rb") as binary_file:
    # Read the whole file at once
    data = bytearray(binary_file.read())

  output = bytearray(len(data))

  read_base = 0
  while read_base < len(data):
    # process row
    for i in range(0x10):
      top_half_origin = read_base + (i*0x08)
      bot_half_origin = read_base + (i*0x08) + 0x80
      top_half_dest = read_base + (i*0x10)
      bot_half_dest = read_base + (i*0x10) + 0x08
      # process character
      q = 1
      for j in range(0x08):
          top_half = data[top_half_origin+j]
          bot_half = data[bot_half_origin+j]
          output[top_half_dest+j] = top_half
          output[bot_half_dest+j] = bot_half
    read_base += 0x100

  with open(outfile, "wb") as out:
    out.write(output)
  print ("Done")


if __name__ == '__main__':
  main()
