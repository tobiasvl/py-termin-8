# termin-8

CHIP-8 interpreter that runs in your terminal using `curses`.

Supports CHIP-8, Super-CHIP and XO-CHIP, as well as multiple "quirks"/legacy behaviors. Should run most CHIP-8 programs out there.

Regular 64x32 resolution CHIP-8 programs are compatible with VT100 terminals (ie. maximum 80x25 characters) by compressing pixels in height.

Please use a monospace font (otherwise the ASCII space character, used for empty space, is not guaranteed to be as wide as other characters).

By default, this program uses [Unicode Block Elements](https://en.wikipedia.org/wiki/Block_Elements) to draw the screen. If your font does not support them, you can supply other characters in config.

XO-CHIP uses colors by default to distinguish planes. You can set it to use shaded Block Elements instead.
