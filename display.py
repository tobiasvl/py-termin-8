import curses
from collections import defaultdict

BLOCK = "█"
SPACE = " "

class BasicCursesDisplay:
    """CHIP-8 ncurses display"""
    def __init__(self, stdscr):
        self.active_plane = 1
        self.width = 64
        self.height = 32
        self.stdscr = stdscr
        self.tall_mode = False
        self.hires_mode = False
        
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

        self.frame_buffer = [[0] * self.width for _ in range(self.height)]

        self.plane_colors = [
            curses.COLOR_BLACK,
            curses.COLOR_WHITE,
            curses.COLOR_RED,
            curses.COLOR_BLACK
        ]

        self.active_plane = 1

        #for pair in range(1,3):
        #    curses.init_pair(pair, self.plane_colors[pair], curses.COLOR_BLACK)
        #curses.init_pair(pair, self.plane_colors[4], curses.COLOR_BLACK)

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

    def clear(self):
        """Clear the display."""
        self.stdscr.erase()
        self.stdscr.refresh()
        self.frame_buffer = [[0] * self.width for _ in range(self.height)]

    def scroll(self, direction, pixels):
        pass
    
    def draw(self, x, y, sprite):
        for row, num in enumerate(sprite):
            if y + row > self.height:
                break
            for col in range(8):
                if x + col > self.width:
                    break
                if (num >> (7 - col)) & 1:
                    if self.stdscr.inch(y + row, x + col) & curses.A_CHARTEXT == 136: #BLOCK:
                        collision = 1 # TODO QUIRK
                        self.stdscr.addch(y + row, x + col, SPACE)
                    else:
                        self.stdscr.addch(y + row, x + col, BLOCK)

        self.stdscr.refresh()
        return collision

    def plane(self, x):
        self.active_plane = x
        return
        if x == 0:
            self.active_planes = [False] * 3
        elif x == 1:
            self.active_planes = [False, True, False]
        elif x == 2:
            self.active_planes = [False, False, True]
        elif x == 3:
            self.active_planes = [False, True, True]

class UnicodeCursesDisplay(BasicCursesDisplay):
    def __init__(self, stdscr):
        super().__init__(stdscr)
    
    def check_display(self):
        """Assert that the display is large enoug."""
        # pylint: disable=no-member
        # The curses module does in fact have the members LINES and COLS.
        curses.update_lines_cols()
        if curses.LINES < self.height // 2 or curses.COLS < self.width:
            raise curses.error("CHIP-8 needs at least " + str(self.height // 2) + " lines and " + str(self.width) + " cols, got " + str(curses.LINES) + " and " + str(curses.COLS))

    def redraw(self):
        self.stdscr.erase()
        if curses.LINES >= self.height and curses.COLS >= (self.width * 2) and not self.hires_mode:
            for y in range(self.height):
                for x in range(self.width):
                    if self.frame_buffer[y][x]:
                        self.stdscr.addch(y, (x * 2), BLOCK)
                        self.stdscr.addch(y, (x * 2) + 1, BLOCK)
        else:
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
                    if self.frame_buffer[y][x]:
                        pixel = lookup[y % 2][self.stdscr.inch(y // 2, x) & curses.A_CHARTEXT]
                        self.stdscr.addch(y // 2, x, pixel[0])
        self.stdscr.refresh()

    def draw(self, x, y, sprite):
        """Draw a CHIP-8 sprite and return the collision status."""
        if self.active_plane == 0:
            return 0
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

        collision = 0
        y = y % self.height
        x = x % self.width

        if self.hires_mode and len(sprite) == 32:
            sprite_width = 16
            sprite = zip(sprite[0::2], sprite[1::2])
        else:
            sprite_width = 8
    
        #for plane in range(active_plane):
        
        if curses.LINES >= self.height and curses.COLS >= (self.width * 2) and not self.hires_mode:
            for row, num in enumerate(sprite):
                if y + row > self.height:
                    break
                for col in range(8):
                    if (x + col) * 2 > self.width * 2:
                        break
                    if (num >> (7 - col)) & 1:
                        self.frame_buffer[y + row][x + col] ^= 1
                        if self.stdscr.inch(y + row, (x * 2) + (col * 2)) & curses.A_CHARTEXT == 136: #BLOCK:
                            collision = 1 # TODO QUIRK
                            self.stdscr.addch(y + row, (x * 2) + (col * 2), SPACE)
                            self.stdscr.addch(y + row, (x * 2) + (col * 2) + 1, SPACE)
                            
                        else:
                            self.stdscr.addch(y + row, (x * 2) + (col * 2), BLOCK)
                            self.stdscr.addch(y + row, (x * 2) + (col * 2) + 1, BLOCK)
        else:
            for row, num in enumerate(sprite):
                if y + row > self.height:
                    break
                if sprite_width == 16:
                    num = (num[0] << 8) | num[1]
                for col in range(sprite_width):
                    if (num >> (sprite_width - col - 1)) & 1:
                        self.frame_buffer[y + row][x + col] ^= 1
                        if x + col > self.width:
                            break
                        pixel = lookup[(y + row) % 2][self.stdscr.inch((y + row) // 2, x + col) & curses.A_CHARTEXT]
                        self.stdscr.addch((y + row) // 2, x + col, pixel[0])
                        if pixel[1]:
                            collision = 1

        self.stdscr.refresh()
        return collision