import curses

BLOCK = "█"
SPACE = " "

class Display:
    """CHIP-8 ncurses display"""
    def __init__(self, stdscr):
        self.width = 64
        self.height = 32
        self.stdscr = stdscr
        self.tall_mode = False
        self.hires_mode = False
        curses.curs_set(False)
        self.stdscr.nodelay(True)

        self.check_display()
        self.clear()

    def check_display(self):
        """Assert that the display is large enoug."""
        # pylint: disable=no-member
        # The curses module does in fact have the members LINES and COLS.
        curses.update_lines_cols()
        if curses.LINES < self.height // 2 or curses.COLS < self.width:
            raise curses.error("CHIP-8 needs at least " + str(self.height // 2) + " lines and " + str(self.width) + " cols, got " + str(curses.LINES) + " and " + str(curses.COLS))

    def hires(self):
        """Enters hires mode."""
        self.width = 128
        self.height = 64
        self.check_display()
        self.hires_mode = True
        self.clear()

    def lores(self):
        """Enters lores mode."""
        self.width = 64
        self.height = 32
        self.check_display()
        self.hires_mode = False
        self.clear()

    def clear(self):
        """Clear the display."""
        self.stdscr.erase()
        self.stdscr.refresh()

    def scroll(self, direction, pixels):
        pass

    def draw(self, x, y, sprite):
        """Draw a CHIP-8 sprite and return the collision status."""
        collision = 0
        y = y % self.height
        x = x % self.width

        if self.hires_mode and len(sprite) == 32:
            for row, double_num in enumerate(zip(sprite[0::2], sprite[1::2])):
                num = (double_num[0] << 8) | double_num[1]
                if y + row > self.height:
                    break
                for col in range(16):
                    if (num >> (15 - col)) & 1:
                        if x + col > self.width:
                            break
                        if (y + row) % 2 == 0:
                            if self.stdscr.inch((y + row) // 2, x + col) & curses.A_CHARTEXT == 128: #upper
                                collision = 1 # TODO QUIRK
                                self.stdscr.addch((y + row) // 2, x + col, SPACE)
                            elif self.stdscr.inch((y + row) // 2, x + col) & curses.A_CHARTEXT == 132: #lower
                                self.stdscr.addch((y + row) // 2, x + col, BLOCK)
                            elif self.stdscr.inch((y + row) // 2, x + col) & curses.A_CHARTEXT == 136: #full
                                collision = 1 # TODO QUIRK
                                self.stdscr.addch((y + row) // 2, x + col, "▄")
                            else:
                                self.stdscr.addch((y + row) // 2, x + col, "▀")
                        else:
                            if self.stdscr.inch((y + row) // 2, x + col) & curses.A_CHARTEXT == 128: #upper
                                self.stdscr.addch((y + row) // 2, x + col, BLOCK)
                            elif self.stdscr.inch((y + row) // 2, x + col) & curses.A_CHARTEXT == 132: #lower
                                collision = 1 # TODO QUIRK
                                self.stdscr.addch((y + row) // 2, x + col, SPACE)
                            elif self.stdscr.inch((y + row) // 2, x + col) & curses.A_CHARTEXT == 136: #full
                                collision = 1 # TODO QUIRK
                                self.stdscr.addch((y + row) // 2, x + col, "▀")
                            else:
                                self.stdscr.addch((y + row) // 2, x + col, "▄")
        #elif self.tall_mode:
        #    for row, num in enumerate(sprite):
        #        if y + row > self.height:
        #            break
        #        for col in range(8):
        #            if x + col > self.width:
        #                break
        #            if (num >> (7 - col)) & 1:
        #                if self.stdscr.inch(y + row, x + col) & curses.A_CHARTEXT == 136: #BLOCK:
        #                    collision = 1 # TODO QUIRK
        #                    self.stdscr.addch(y + row, x + col, SPACE)
        #                else:
        #                    self.stdscr.addch(y + row, x + col, BLOCK)
        else:
            for row, num in enumerate(sprite):
                if y + row > self.height:
                    break
                for col in range(8):
                    if (num >> (7 - col)) & 1:
                        if x + col > self.width:
                            break
                        if (y + row) % 2 == 0:
                            if self.stdscr.inch((y + row) // 2, x + col) & curses.A_CHARTEXT == 128: #upper
                                collision = 1 # TODO QUIRK
                                self.stdscr.addch((y + row) // 2, x + col, SPACE)
                            elif self.stdscr.inch((y + row) // 2, x + col) & curses.A_CHARTEXT == 132: #lower
                                self.stdscr.addch((y + row) // 2, x + col, BLOCK)
                            elif self.stdscr.inch((y + row) // 2, x + col) & curses.A_CHARTEXT == 136: #full
                                collision = 1 # TODO QUIRK
                                self.stdscr.addch((y + row) // 2, x + col, "▄")
                            else:
                                self.stdscr.addch((y + row) // 2, x + col, "▀")
                        else:
                            if self.stdscr.inch((y + row) // 2, x + col) & curses.A_CHARTEXT == 128: #upper
                                self.stdscr.addch((y + row) // 2, x + col, BLOCK)
                            elif self.stdscr.inch((y + row) // 2, x + col) & curses.A_CHARTEXT == 132: #lower
                                collision = 1 # TODO QUIRK
                                self.stdscr.addch((y + row) // 2, x + col, SPACE)
                            elif self.stdscr.inch((y + row) // 2, x + col) & curses.A_CHARTEXT == 136: #full
                                collision = 1 # TODO QUIRK
                                self.stdscr.addch((y + row) // 2, x + col, "▀")
                            else:
                                self.stdscr.addch((y + row) // 2, x + col, "▄")

        self.stdscr.refresh()
        return collision
