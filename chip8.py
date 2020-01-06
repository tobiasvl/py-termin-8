import time
import curses
import random
from display import BasicCursesDisplay, UnicodeCursesDisplay

class Chip8:
    """CHIP-8 module"""

    # pylint: disable=too-many-instance-attributes
    # pylint: disable=invalid-name
    # Eight is reasonable in this case.

    def __init__(self, rom_file):
        self.display = None
        self.pc = 0x200
        self.i = 0
        self.v = [0] * 16
        self.delay = 0
        self.sound = 0
        self.stack = []
        self.reset_keys = -1
        self.key_map = {
            'x': 0,
            '1': 1,
            '2': 2,
            '3': 3,
            'q': 4,
            'w': 5,
            'e': 6,
            'a': 7,
            's': 8,
            'd': 9,
            'z': 0xA,
            'c': 0xB,
            '4': 0xC,
            'r': 0xD,
            'f': 0xE,
            'v': 0xF
        }

        self.key_status = [False] * 16

        self.memory = [0] * 4096
        self.memory[0:79] = [0xF0, 0x90, 0x90, 0x90, 0xF0,
                             0x20, 0x60, 0x20, 0x20, 0x70,
                             0xF0, 0x10, 0xF0, 0x80, 0xF0,
                             0xF0, 0x10, 0xF0, 0x10, 0xF0,
                             0x90, 0x90, 0xF0, 0x10, 0x10,
                             0xF0, 0x80, 0xF0, 0x10, 0xF0,
                             0xF0, 0x80, 0xF0, 0x90, 0xF0,
                             0xF0, 0x10, 0x20, 0x40, 0x40,
                             0xF0, 0x90, 0xF0, 0x90, 0xF0,
                             0xF0, 0x90, 0xF0, 0x10, 0xF0,
                             0xF0, 0x90, 0xF0, 0x90, 0x90,
                             0xE0, 0x90, 0xE0, 0x90, 0xE0,
                             0xF0, 0x80, 0x80, 0x80, 0xF0,
                             0xE0, 0x90, 0x90, 0x90, 0xE0,
                             0xF0, 0x80, 0xF0, 0x80, 0xF0,
                             0xF0, 0x80, 0xF0, 0x80, 0x80]

        rom = open(rom_file, "rb").read()
        self.memory[512:512+len(rom)] = rom

        self.quirks = {
            'shift': True,
            'load_store': True
        }

    def read_keys(self):
        """Read keys and set status"""
        if self.reset_keys >= 0:
            self.reset_keys -= 1

        if self.reset_keys == 0:
            self.key_status = [False] * 16

        while True:
            try:
                key = self.display.stdscr.getkey()
            except curses.error:
                break
            else:
                if key == "KEY_RESIZE":
                    self.display.check_display()
                    self.display.redraw()
                else:
                    if key in self.key_map:
                        self.key_status[self.key_map[key]] = True
                    self.reset_keys = 20

    def timers(self):
        """Handle CHIP-8 timers."""
        if self.sound > 0:
            #curses.beep()
            #curses.flash()
            self.sound -= 1

        if self.delay > 0:
            self.delay -= 1

    def fetch(self):
        """Fetch and return a CHIP-8 instruction. Also advance program counter."""
        instruction = (self.memory[self.pc] << 8) | self.memory[self.pc + 1]
        self.pc += 2
        return instruction

    def decode(self, instruction):
        """Decode and execute a CHIP-8 instruction."""
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements

        opcode = instruction & 0xF000
        x = (instruction & 0x0F00) >> 8
        y = (instruction & 0x00F0) >> 4
        n = instruction & 0x000F
        nn = instruction & 0x00FF
        nnn = instruction & 0x0FFF

        if opcode == 0x0000:
            if x == 0:
                if y == 0x1:
                    exit(n)
                elif y == 0xC:
                    self.display.scroll('down', n)
                elif y == 0xB or y == 0xD:
                    self.display.scroll('up', n)
                elif nn == 0xE0:
                    self.display.clear()
                elif nn == 0xEE:
                    self.pc = self.stack.pop()
                elif nn == 0xFA:
                    self.quirks.load_store = not self.quirks.load_store
                elif nn == 0xFB:
                    self.display.scroll('right', 4)
                elif nn == 0xFC:
                    self.display.scroll('left', 4)
                elif nn == 0xFE:
                    self.display.lores()
                elif nn == 0xFF:
                    self.display.hires()
        elif opcode == 0x1000:
            self.pc = nnn
        elif opcode == 0x2000:
            self.stack.append(self.pc)
            self.pc = nnn
        elif opcode == 0x3000:
            if self.v[x] == nn:
                self.pc += 2
        elif opcode == 0x4000:
            if self.v[x] != nn:
                self.pc += 2
        elif opcode == 0x5000:
            if n == 0:
                if self.v[x] == self.v[y]:
                    self.pc += 2
            elif n == 0x2:
                for i, reg in enumerate(range(x, y + 1)):
                    self.memory[i + self.i] = self.v[reg]
                if self.quirks['load_store']:
                    self.i += y - x + 1
            elif nn == 0x3:
                for i, reg in enumerate(range(x, y + 1)):
                    self.v[reg] = self.memory[i + self.i]
                if self.quirks['load_store']:
                    self.i += y - x + 1
        elif opcode == 0x6000:
            self.v[x] = nn
        elif opcode == 0x7000:
            self.v[x] = (self.v[x] + nn) & 0xFF
        elif opcode == 0x8000:
            if n == 0:
                self.v[x] = self.v[y]
            elif n == 1:
                self.v[x] |= self.v[y]
            elif n == 2:
                self.v[x] &= self.v[y]
            elif n == 3:
                self.v[x] ^= self.v[y]
            elif n == 4:
                if self.v[x] + self.v[y] > 255:
                    self.v[0xF] = 1
                else:
                    self.v[0xF] = 0
                self.v[x] = (self.v[x] + self.v[y]) & 0xFF
            elif n == 5:
                if self.v[y] > self.v[x]:
                    self.v[0xF] = 0
                else:
                    self.v[0xF] = 1
                self.v[x] = self.v[x] - self.v[y] & 0xFF
            elif n == 6:
                if not self.quirks['shift']:
                    self.v[x] = self.v[y]
                self.v[0xF] = self.v[x] & 1
                self.v[x] >>= 1
            elif n == 7:
                if self.v[x] > self.v[y]:
                    self.v[0xF] = 0
                else:
                    self.v[0xF] = 1
                self.v[x] = self.v[y] - self.v[x] & 0xFF
            elif n == 0xE:
                if not self.quirks['shift']:
                    self.v[x] = self.v[y]
                self.v[0xF] = (self.v[x] & 0x80) >> 7
                self.v[x] <<= 1
                self.v[x] &= 0xFF
        elif opcode == 0x9000:
            if n == 0:
                if self.v[x] != self.v[y]:
                    self.pc += 2
        elif opcode == 0xA000:
            self.i = nnn
        elif opcode == 0xB000:
            self.pc = nnn + self.v[0]
            # TODO QUIRK pc = nnn + v[x]
        elif opcode == 0xC000:
            self.v[x] = random.randint(0, 256) & nn
        elif opcode == 0xD000:
            if n == 0:
                if self.display.hires_mode:
                    sprite = self.memory[self.i : self.i + 32]
                else:
                    sprite = self.memory[self.i : self.i + 16]
            else:
                sprite = self.memory[self.i : self.i + (n * len(self.display.active_planes))]
            self.v[0xF] = self.display.draw(self.v[x], self.v[y], sprite)
        elif opcode == 0xE000:
            if nn == 0x9E:
                if self.key_status[self.v[x]]:
                    self.pc += 2
            elif nn == 0xA1:
                if not self.key_status[self.v[x]]:
                    self.pc += 2
        elif opcode == 0xF000:
            if nnn == 0x000:
                self.i = (self.memory[self.pc] << 8) | self.memory[self.pc + 1]
                self.pc += 2
            elif nn == 0x01:
                self.display.active_planes = [place for place, digit in enumerate(bin(x)[2:][::-1]) if digit=='1']
            elif nn == 0x02:
                # audio
                pass
            elif nn == 0x07:
                self.v[x] = self.delay
            elif nn == 0x0A:
                try:
                    self.v[x] = self.key_status.index(True)
                except ValueError:
                    self.pc -= 2
            elif nn == 0x15:
                self.delay = self.v[x]
            elif nn == 0x18:
                self.sound = self.v[x]
            elif nn == 0x1E:
                self.i += self.v[x]
            elif nn == 0x29:
                self.i = self.v[x] * 5
            elif nn == 0x33:
                self.memory[self.i], bcd = divmod(self.v[x], 100)
                self.memory[self.i + 1], self.memory[self.i + 2] = divmod(bcd, 10)
                #i += 3
            elif nn == 0x55:
                for reg in range(x + 1):
                    self.memory[reg + self.i] = self.v[reg]
                if self.quirks['load_store']:
                    self.i += x + 1
            elif nn == 0x65:
                for reg in range(x + 1):
                    self.v[reg] = self.memory[reg + self.i]
                if self.quirks['load_store']:
                    self.i += x + 1

    def loop(self, stdscr):
        self.display = UnicodeCursesDisplay(stdscr)
        while True:
            #curses.update_lines_cols()
            time.sleep(0.003)
            self.read_keys()
            self.decode(self.fetch())
            self.timers()
