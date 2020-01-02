import curses
import sys
from chip8 import Chip8

def main():
    try:
        rom_file = sys.argv[1]
    except:
        rom_file = "BC_test.ch8"

    chip8 = Chip8(rom_file)

    try:
        curses.wrapper(chip8.loop)
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    main()
