import curses
from collections import defaultdict
from itertools import cycle, zip_longest

BLOCK = "█"
SPACE = " "

class BasicCursesDisplay:
    """CHIP-8 ncurses display"""
    def __init__(self, stdscr, quirks):
        self.active_planes = [0]
        self.width = 64
        self.height = 32
        self.stdscr = stdscr
        self.tall_mode = False
        self.hires_mode = False
        
        self.quirks = quirks

        # Set the cursor as invisible as possible
        self.stdscr.leaveok(True)
        try:
            curses.curs_set(0)
        except curses.error:
            try:
                curses.curs_set(1)
            except:
                pass

        self.stdscr.nodelay(True)

        self.frame_buffer = [[[0] * self.width for _ in range(self.height)]]

        self.plane_colors = [
            curses.COLOR_BLACK,
            curses.COLOR_WHITE,
            curses.COLOR_RED,
            curses.COLOR_GREEN
        ]

        #curses.init_pair(1, self.plane_colors[], curses.COLOR_BLACK)
        #curses.init_pair(2, self.plane_colors[4], curses.COLOR_BLACK)

        self.check_display()
        self.clear()

    def check_display(self):
        """Assert that the display is large enough."""
        # pylint: disable=no-member
        # The curses module does in fact have the members LINES and COLS.
        curses.update_lines_cols()
        if curses.LINES < self.height or curses.COLS < self.width:
            raise curses.error("CHIP-8 needs at least " + str(self.height) + " lines and " + str(self.width) + " cols, got " + str(curses.LINES) + " and " + str(curses.COLS))

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
    
    def set_active_planes(self, planes):
        if not self.frame_buffer[planes[-1]]:
            self.frame_buffer += [[[0] * self.width for _ in range(self.height)] for __ in range(len(self.frame_buffer), planes[-1] - len(self.frame_buffer))]
        self.active_planes = planes

    def clear(self):
        """Clear the display for any active planes."""
        if not self.active_planes:
            return
        for plane in self.active_planes:
            self.frame_buffer[plane] = [[0] * self.width for _ in range(self.height)]
        if len(self.active_planes) < len(self.frame_buffer):
            # If only some of the existing planes are active, we'll need to redraw
            # (unless we can smartly check that the inactive planes are all blank...)
            self.redraw()
        else:
            # If all planes are active, we just wipe the display instead of doing a costly
            # redraw.
            self.stdscr.erase()
            self.stdscr.refresh()

    def scroll(self, direction, pixels):
        pass

class UnicodeCursesDisplay(BasicCursesDisplay):
    def __init__(self, stdscr, quirks):
        super().__init__(stdscr, quirks)
    
    def check_display(self):
        """Assert that the display is large enoug."""
        # pylint: disable=no-member
        # The curses module does in fact have the members LINES and COLS.
        curses.update_lines_cols()
        if curses.LINES < self.height // 2 or curses.COLS < self.width:
            raise curses.error("CHIP-8 needs at least " + str(self.height // 2) + " lines and " + str(self.width) + " cols, got " + str(curses.LINES) + " and " + str(curses.COLS))

    def redraw(self):
        self.stdscr.erase()
        if self.hires_mode or curses.LINES < self.height or curses.COLS < self.width:
            lookup = [
                {
                    32:  ("▀", False),
                    128: (" ", True), #upper
                    132: ("█", False),#lower
                    136: ("▄", True)    #full
                },
                {
                    32:  ("▄", False),
                    128: ("█", False), #upper
                    132: (" ", True), #lower
                    136: ("▀", True)    #full
                }
            ]
            for y in range(self.height):
                for x in range(self.width):
                    for p in self.active_planes:
                        if self.frame_buffer[p][y][x]:
                            if self.frame_buffer[p][y][x]:
                                pixel = lookup[y % 2][self.stdscr.inch(y // 2, x) & curses.A_CHARTEXT]
                                self.stdscr.addch(y // 2, x, pixel[0])
        else:
            for y in range(self.height):
                for x in range(self.width):
                    for p in self.active_planes:
                        if self.frame_buffer[p][y][x]:
                            if curses.LINES >= self.height and curses.COLS >= (self.width * 2):
                                self.stdscr.addch(y, (x * 2), BLOCK)
                                self.stdscr.addch(y, (x * 2) + 1, BLOCK)
                            elif curses.LINES >= self.height and curses.COLS >= self.width:
                                self.stdscr.addch(y, x, BLOCK)
        self.stdscr.refresh()

    def draw(self, x, y, sprite):
        """Draw a CHIP-8 sprite and return the collision status."""
        if not self.active_planes:
            return 0

        collision = 0
        y = y % self.height
        x = x % self.width

        if len(sprite) == 32 and (self.hires_mode or self.quirks['lores_wide_sprites']):
            # FIXME Sprites can be 32 bytes large with the combination XO-CHIP, lores mode and DXY0!!!
            sprite_width = 16
            sprite = zip(sprite[0::2], sprite[1::2])
        else:
            sprite_width = 8
    
        active_plane = cycle(self.active_planes)
        for row, num in enumerate(sprite):
            plane = self.frame_buffer[next(active_plane)]
            if y + row > self.height:
                break
            if sprite_width == 16:
                num = (num[0] << 8) | num[1]
            for col in range(sprite_width):
                    if x + col > self.width:
                        break
                    if (num >> (sprite_width - col - 1)) & 1:
                        if plane[y + row][x + col]:
                            collision = 1
                        plane[y + row][x + col] ^= 1

        self.redraw() # TODO Change this to just redraw affected area
        return collision