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

        # Font
        self.memory[0:0x050] = [
            0xF0, 0x90, 0x90, 0x90, 0xF0, # 0
            0x20, 0x60, 0x20, 0x20, 0x70, # 1
            0xF0, 0x10, 0xF0, 0x80, 0xF0, # 2
            0xF0, 0x10, 0xF0, 0x10, 0xF0, # 3
            0x90, 0x90, 0xF0, 0x10, 0x10, # 4
            0xF0, 0x80, 0xF0, 0x10, 0xF0, # 5
            0xF0, 0x80, 0xF0, 0x90, 0xF0, # 6
            0xF0, 0x10, 0x20, 0x40, 0x40, # 7
            0xF0, 0x90, 0xF0, 0x90, 0xF0, # 8
            0xF0, 0x90, 0xF0, 0x10, 0xF0, # 9
            0xF0, 0x90, 0xF0, 0x90, 0x90, # A
            0xE0, 0x90, 0xE0, 0x90, 0xE0, # B
            0xF0, 0x80, 0x80, 0x80, 0xF0, # C
            0xE0, 0x90, 0x90, 0x90, 0xE0, # D
            0xF0, 0x80, 0xF0, 0x80, 0xF0, # E
            0xF0, 0x80, 0xF0, 0x80, 0x80  # F
        ]
        
        # Big font
        self.memory[0x050:0x0F0] = [
            0xFF, 0xFF, 0xC3, 0xC3, 0xC3, 0xC3, 0xC3, 0xC3, 0xFF, 0xFF, # 0
            0x18, 0x78, 0x78, 0x18, 0x18, 0x18, 0x18, 0x18, 0xFF, 0xFF, # 1
            0xFF, 0xFF, 0x03, 0x03, 0xFF, 0xFF, 0xC0, 0xC0, 0xFF, 0xFF, # 2
            0xFF, 0xFF, 0x03, 0x03, 0xFF, 0xFF, 0x03, 0x03, 0xFF, 0xFF, # 3
            0xC3, 0xC3, 0xC3, 0xC3, 0xFF, 0xFF, 0x03, 0x03, 0x03, 0x03, # 4
            0xFF, 0xFF, 0xC0, 0xC0, 0xFF, 0xFF, 0x03, 0x03, 0xFF, 0xFF, # 5
            0xFF, 0xFF, 0xC0, 0xC0, 0xFF, 0xFF, 0xC3, 0xC3, 0xFF, 0xFF, # 6
            0xFF, 0xFF, 0x03, 0x03, 0x06, 0x0C, 0x18, 0x18, 0x18, 0x18, # 7
            0xFF, 0xFF, 0xC3, 0xC3, 0xFF, 0xFF, 0xC3, 0xC3, 0xFF, 0xFF, # 8
            0xFF, 0xFF, 0xC3, 0xC3, 0xFF, 0xFF, 0x03, 0x03, 0xFF, 0xFF, # 9
            0x7E, 0xFF, 0xC3, 0xC3, 0xC3, 0xFF, 0xFF, 0xC3, 0xC3, 0xC3, # A
            0xFC, 0xFC, 0xC3, 0xC3, 0xFC, 0xFC, 0xC3, 0xC3, 0xFC, 0xFC, # B
            0x3C, 0xFF, 0xC3, 0xC0, 0xC0, 0xC0, 0xC0, 0xC3, 0xFF, 0x3C, # C
            0xFC, 0xFE, 0xC3, 0xC3, 0xC3, 0xC3, 0xC3, 0xC3, 0xFE, 0xFC, # D
            0xFF, 0xFF, 0xC0, 0xC0, 0xFF, 0xFF, 0xC0, 0xC0, 0xFF, 0xFF, # E
            0xFF, 0xFF, 0xC0, 0xC0, 0xFF, 0xFF, 0xC0, 0xC0, 0xC0, 0xC0  # F
        ]

        rom = open(rom_file, "rb").read()
        self.memory[0x200:0x200 + len(rom)] = rom

        self.quirks = {
            'shift': False,
            'load_store': False,
            'lores_wide_sprites': True,  # Octo
            'lores_tall_sprites': False, # DREAM 6800
            'jump': False
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
            if self.quirks['jump']:
                self.pc = nnn + self.v[x]
            else:
                self.pc = nnn + self.v[0]
        elif opcode == 0xC000:
            self.v[x] = random.randint(0, 256) & nn
        elif opcode == 0xD000:
            if n == 0:
                #if self.display.hires_mode:
                sprite_bytes = 32 * len(self.display.active_planes)
                #else: # DREAM 6800 mode
                #    sprite_bytes = 16 * len(self.display.active_planes)
            else:
                sprite_bytes = n * len(self.display.active_planes)

            sprite = self.memory[self.i : self.i + sprite_bytes]
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
                planes = [place - 1 for place, digit in enumerate(bin(x)[2:][::-1]) if digit=='1']
                self.display.set_active_planes(planes)
            elif nn == 0x02:
                # Audio not implemented
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
            elif nn == 0x30:
                self.i = 0x50 + (self.v[x] * 10)
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
        self.display = UnicodeCursesDisplay(stdscr, self.quirks)
        while True:
            #curses.update_lines_cols()
            #time.sleep(0.003)
            self.read_keys()
            for _ in range(50):
                self.decode(self.fetch())
            self.timers()
