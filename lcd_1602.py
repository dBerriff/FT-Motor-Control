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
LCD_ADDRESS = const(0x7c >> 1)

LCD_CLEARDISPLAY = const(0x01)
LCD_RETURNHOME = const(0x02)
LCD_ENTRYMODESET = const(0x04)
LCD_DISPLAYCONTROL = const(0x08)
LCD_CURSORSHIFT = const(0x10)
LCD_FUNCTIONSET = const(0x20)
LCD_SETCGRAMADDR = const(0x40)
LCD_SETDDRAMADDR = const(0x80)

# flags for display entry mode
LCD_ENTRYRIGHT = const(0x00)
LCD_ENTRYLEFT = const(0x02)
LCD_ENTRYSHIFTINCREMENT = const(0x01)
LCD_ENTRYSHIFTDECREMENT = const(0x00)

# flags for display on/off control
LCD_DISPLAYON = const(0x04)
LCD_DISPLAYOFF = const(0x00)
LCD_CURSORON = const(0x02)
LCD_CURSOROFF = const(0x00)
LCD_BLINKON = const(0x01)
LCD_BLINKOFF = const(0x00)

# flags for display/cursor shift
LCD_DISPLAYMOVE = const(0x08)
LCD_CURSORMOVE = const(0x00)
LCD_MOVERIGHT = const(0x04)
LCD_MOVELEFT = const(0x00)

# flags for function set
LCD_8BITMODE = const(0x10)
LCD_4BITMODE = const(0x00)
LCD_2LINE = const(0x08)
LCD_1LINE = const(0x00)
LCD_5x8DOTS = const(0x00)


class Lcd1602:
    """ drive LCD1602 display """

    def __init__(self, sda_, scl_, col=16, row=2):
        self.i2c = I2C(0, sda=Pin(sda_), scl=Pin(scl_), freq=400000)
        self._col = col
        self._row = row
        self._showfunction = LCD_4BITMODE | LCD_1LINE | LCD_5x8DOTS
        self.start(self._row)
        self._numlines = None
        self._currline = None
        self._showcontrol = None
        self._showmode = None

    def command(self, cmd):
        self.i2c.writeto_mem(LCD_ADDRESS, 0x80, chr(cmd))

    def write(self, data):
        self.i2c.writeto_mem(LCD_ADDRESS, 0x40, chr(data))

    def set_cursor(self, col, row):
        if row == 0:
            col |= 0x80
        else:
            col |= 0xc0
        self.i2c.writeto(LCD_ADDRESS, bytearray([0x80, col]))

    def clear(self):
        self.command(LCD_CLEARDISPLAY)
        time.sleep_ms(2)

    def printout(self, arg):
        if isinstance(arg, int):
            arg = str(arg)
        for x in bytearray(arg, 'utf-8'):
            self.write(x)

    def display(self):
        self._showcontrol |= LCD_DISPLAYON
        self.command(LCD_DISPLAYCONTROL | self._showcontrol)

    def start(self, lines):
        if lines > 1:
            self._showfunction |= LCD_2LINE
        self._numlines = lines
        self._currline = 0
        time.sleep_ms(50)

        # Send function set command sequence
        self.command(LCD_FUNCTIONSET | self._showfunction)
        # wait more than 4.1ms
        time.sleep_ms(5)
        # second try
        self.command(LCD_FUNCTIONSET | self._showfunction)
        time.sleep_ms(5)
        # third try
        self.command(LCD_FUNCTIONSET | self._showfunction)
        # finally, set # lines, font size, etc.
        self.command(LCD_FUNCTIONSET | self._showfunction)
        # turn the display on with no cursor or blinking default
        self._showcontrol = LCD_DISPLAYON | LCD_CURSOROFF | LCD_BLINKOFF
        self.display()
        self.clear()
        # Initialize to default text direction
        self._showmode = LCD_ENTRYLEFT | LCD_ENTRYSHIFTDECREMENT
        self.command(LCD_ENTRYMODESET | self._showmode)
