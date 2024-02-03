# lcd1602.py
""" Waveshare-supplied class for:
    - LCD1602 I2C Module
    - const() function added
"""
# coding: utf-8
import time
from machine import Pin, I2C
from micropython import const

# Device I2C Address
ADDRESS = const(0x7c >> 1)


CLEARDISPLAY = const(0x01)
RETURNHOME = const(0x02)
ENTRYMODESET = const(0x04)
DISPLAYCONTROL = const(0x08)
CURSORSHIFT = const(0x10)
FUNCTIONSET = const(0x20)
SETCGRAMADDR = const(0x40)
SETDDRAMADDR = const(0x80)

# flags for display entry mode
ENTRYRIGHT = const(0x00)
ENTRYLEFT = const(0x02)
ENTRYSHIFTINCREMENT = const(0x01)
ENTRYSHIFTDECREMENT = const(0x00)

# flags for display on/off control
DISPLAYON = const(0x04)
DISPLAYOFF = const(0x00)
CURSORON = const(0x02)
CURSOROFF = const(0x00)
BLINKON = const(0x01)
BLINKOFF = const(0x00)

# flags for display/cursor shift
DISPLAYMOVE = const(0x08)
CURSORMOVE = const(0x00)
MOVERIGHT = const(0x04)
MOVELEFT = const(0x00)

# flags for function set
_8BITMODE = const(0x10)
_4BITMODE = const(0x00)
_2LINE = const(0x08)
_1LINE = const(0x00)
_5x8DOTS = const(0x00)


class Lcd1602:
    """ drive LCD1602 display """

    def __init__(self, sda_, scl_, col=16, row=2):
        if sda_ in (0, 4, 8, 12, 16, 20):
            i = 0
        else:
            i = 1
        self.i2c = I2C(i, sda=Pin(sda_), scl=Pin(scl_), freq=400_000)
        self._col = col
        self._row = row
        self._showfunction = _4BITMODE | _1LINE | _5x8DOTS
        self.start(self._row)
        self._numlines = None
        self._currline = None
        self._showcontrol = None
        self._showmode = None

    def _command(self, cmd):
        self.i2c.writeto_mem(ADDRESS, 0x80, chr(cmd))

    def write(self, data):
        self.i2c.writeto_mem(ADDRESS, 0x40, chr(data))

    def set_cursor(self, col, row):
        if row == 0:
            col |= 0x80
        else:
            col |= 0xc0
        self.i2c.writeto(ADDRESS, bytearray([0x80, col]))

    def clear(self):
        self._command(CLEARDISPLAY)
        time.sleep_ms(2)

    def printout(self, arg):
        if isinstance(arg, int):
            arg = str(arg)
        for x in bytearray(arg, 'utf-8'):
            self.write(x)

    def display(self):
        self._showcontrol |= DISPLAYON
        self._command(DISPLAYCONTROL | self._showcontrol)

    def start(self, lines):
        if lines > 1:
            self._showfunction |= _2LINE
        self._numlines = lines
        self._currline = 0
        time.sleep_ms(50)

        # Send function set command sequence
        for _ in range(3):
            self._command(FUNCTIONSET | self._showfunction)
            time.sleep_ms(5)  # wait more than 4.1ms
        # turn the display on with no cursor or blinking default
        self._showcontrol = DISPLAYON | CURSOROFF | BLINKOFF
        self.display()
        self.clear()
        # Initialize to default text direction
        self._showmode = ENTRYLEFT | ENTRYSHIFTDECREMENT
        self._command(ENTRYMODESET | self._showmode)
