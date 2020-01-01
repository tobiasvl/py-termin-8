import sys
import curses
import random

BLOCK = "█"
SPACE = " "
HEIGHT = 32
WIDTH = 64

TALL_MODE = False

try:
    rom_file = sys.argv[1]
except:
    rom_file = "BC_test.ch8"

def main(stdscr):
    curses.curs_set(False)
    stdscr.nodelay(True)

    if (curses.LINES < HEIGHT) or (not TALL_MODE and curses.LINES < HEIGHT // 2) or curses.COLS < WIDTH:
        raise curses.error("CHIP-8 needs at least 16 lines and 64 columns to run.")

    stdscr.clear()

    key_map = {
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

    key_status = [False] * 16

    memory = [0] * 4096
    memory[0:79] = [0xF0, 0x90, 0x90, 0x90, 0xF0,
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
    memory[512:512+len(rom)] = rom

    pc = 0x200
    i = 0
    v = [0] * 16
    delay = 0
    sound = 0
    stack = []

    reset_keys = -1

    while True:
        curses.napms(3)

        if reset_keys >= 0:
            reset_keys -= 1

        if reset_keys == 0:
            key_status = [False] * 16

        while True:
            try:
                key = stdscr.getkey()
            except curses.error:
                break
            else:
                if key in key_map:
                    key_status[key_map[key]] = True
                reset_keys = 20

        instruction = (memory[pc] << 8) | memory[pc + 1]

        opcode = instruction & 0xF000
        x = (instruction & 0x0F00) >> 8
        y = (instruction & 0x00F0) >> 4
        n = instruction & 0x000F
        nn = instruction & 0x00FF
        nnn = instruction & 0x0FFF

        pc += 2

        if sound > 0:
            #curses.beep()
            #curses.flash()
            sound -= 1

        if delay > 0:
            delay -= 1

        if opcode == 0x0000:
            if x == 0:
                if nn == 0xE0:
                    stdscr.clear()
                    stdscr.refresh()
                elif nn == 0xEE:
                    pc = stack.pop()
        elif opcode == 0x1000:
            pc = nnn
        elif opcode == 0x2000:
            stack.append(pc)
            pc = nnn
        elif opcode == 0x3000:
            if v[x] == nn:
                pc += 2
        elif opcode == 0x4000:
            if v[x] != nn:
                pc += 2
        elif opcode == 0x5000:
            if n == 0:
                if v[x] == v[y]:
                    pc += 2
        elif opcode == 0x6000:
            v[x] = nn
        elif opcode == 0x7000:
            v[x] = (v[x] + nn) & 0xFF
        elif opcode == 0x8000:
            if n == 0:
                v[x] = v[y]
            elif n == 1:
                v[x] |= v[y]
            elif n == 2:
                v[x] &= v[y]
            elif n == 3:
                v[x] ^= v[y]
            elif n == 4:
                if v[x] + v[y] > 255:
                    v[0xF] = 1
                else:
                    v[0xF] = 0
                v[x] = (v[x] + v[y]) & 0xFF
            elif n == 5:
                if v[y] > v[x]:
                    v[0xF] = 0
                else:
                    v[0xF] = 1
                v[x] = v[x] - v[y] & 0xFF
            elif n == 6:
                v[0xF] = v[x] & 1
                v[x] >>= 1
                # TODO QUIRK
            elif n == 7:
                if v[x] > v[y]:
                    v[0xF] = 0
                else:
                    v[0xF] = 1
                v[x] = v[y] - v[x] & 0xFF
            elif n == 0xE:
                v[0xF] = (v[x] & 0x80) >> 7
                v[x] <<= 1
                v[x] &= 0xFF
                # TODO QUIRK
        elif opcode == 0x9000:
            if n == 0:
                if v[x] != v[y]:
                    pc += 2
        elif opcode == 0xA000:
            i = nnn
        elif opcode == 0xB000:
            pc = nnn + v[0]
            # TODO QUIRK pc = nnn + v[x]
        elif opcode == 0xC000:
            v[x] = random.randint(0, 256) & nn
        elif opcode == 0xD000:
            if TALL_MODE:
                v[0xF] = 0
                real_y = v[y] & 0x1F
                real_x = v[x] & 0x3F

                for row in range(n):
                    if real_y + row > 0x1F:
                        break
                    num = memory[i + row]
                    for col in range(8):
                        if real_x + col > 0x3F:
                            break
                        if (num >> (7 - col)) & 1:
                            if stdscr.inch(real_y + row, real_x + col) & curses.A_CHARTEXT == 136: #BLOCK:
                                v[0xF] = 1 # TODO QUIRK
                                stdscr.addch(real_y + row, real_x + col, SPACE)
                            else:
                                stdscr.addch(real_y + row, real_x + col, BLOCK)
            else:
                v[0xF] = 0
                real_y = v[y] & 0x1F
                real_x = v[x] & 0x3F
                for row in range(n):
                    num = memory[i + row]
                    for col in range(8):
                        if (num >> (7 - col)) & 1:
                            if (real_y + row) % 2 == 0:
                                if stdscr.inch((real_y + row) // 2, real_x + col) & curses.A_CHARTEXT == 128: #upper
                                    v[0xF] = 1 # TODO QUIRK
                                    stdscr.addch((real_y + row) // 2, real_x + col, SPACE)
                                elif stdscr.inch((real_y + row) // 2, real_x + col) & curses.A_CHARTEXT == 132: #lower
                                    stdscr.addch((real_y + row) // 2, real_x + col, BLOCK)
                                elif stdscr.inch((real_y + row) // 2, real_x + col) & curses.A_CHARTEXT == 136: #full
                                    v[0xF] = 1 # TODO QUIRK
                                    stdscr.addch((real_y + row) // 2, real_x + col, "▄")
                                else:
                                    stdscr.addch((real_y + row) // 2, real_x + col, "▀")
                            else:
                                if stdscr.inch((real_y + row) // 2, real_x + col) & curses.A_CHARTEXT == 128: #upper
                                    stdscr.addch((real_y + row) // 2, real_x + col, BLOCK)
                                elif stdscr.inch((real_y + row) // 2, real_x + col) & curses.A_CHARTEXT == 132: #lower
                                    v[0xF] = 1 # TODO QUIRK
                                    stdscr.addch((real_y + row) // 2, real_x + col, SPACE)
                                elif stdscr.inch((real_y + row) // 2, real_x + col) & curses.A_CHARTEXT == 136: #full
                                    v[0xF] = 1 # TODO QUIRK
                                    stdscr.addch((real_y + row) // 2, real_x + col, "▀")
                                else:
                                    stdscr.addch((real_y + row) // 2, real_x + col, "▄")

            stdscr.refresh()
                
        elif opcode == 0xE000:
            if nn == 0x9E:
                if key_status[v[x]]:
                    pc += 2
            elif nn == 0xA1:
                if not key_status[v[x]]:
                    pc += 2
        elif opcode == 0xF000:
            if nn == 0x07:
                v[x] = delay
            elif nn == 0x0A:
                try:
                    v[x] = key_status.index(True)
                except:
                    pc -= 2
            elif nn == 0x15:
                delay = v[x]
            elif nn == 0x18:
                sound = v[x]
            elif nn == 0x1E:
                i += v[x]
            elif nn == 0x29:
                i = v[x] * 5
            elif nn == 0x33:
                memory[i], bcd = divmod(v[x], 100)
                memory[i+1], memory[i+2] = divmod(bcd, 10)
                #i += 3
            elif nn == 0x55:
                for reg in range(x + 1):
                    memory[reg+i] = v[reg]
                    #i += 1
                # TODO QUIRK
            elif nn == 0x65:
                for reg in range(x + 1):
                    v[reg] = memory[reg+i]
                    #i += 1
                # TODO QUIRK

    stdscr.refresh()
    stdscr.getkey()

try:
    curses.wrapper(main)
except KeyboardInterrupt:
    pass
