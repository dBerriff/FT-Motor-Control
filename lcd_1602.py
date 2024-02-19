# lcd1602.py
""" Refactor of Waveshare class for LCD1602 I2C Module """

from machine import Pin, I2C
from micropython import const
import time


class Lcd1602:
    """ drive LCD1602 display """

    # not all constants are used
    I2C_ADDR = const(62)  # I2C Address

    CLR_DISP = const(0x01)
    # HOME = const(0x02)
    ENTRY_MODE = const(0x04)
    DISP_CONTROL = const(0x08)
    # CURS_SHIFT = const(0x10)
    FN_SET = const(0x20)
    # SET_CGRAM_ADDR = const(0x40)
    # SET_DDRAM_ADDR = const(0x80)

    # flags for display entry mode
    # ENT_RIGHT = const(0x00)
    ENT_LEFT = const(0x02)
    # ENT_SHIFT_INC = const(0x01)
    ENT_SHIFT_DEC = const(0x00)

    # flags for display on/off control
    DISP_ON = const(0x04)
    # DISP_OFF = const(0x00)
    # CURS_ON = const(0x02)
    CURS_OFF = const(0x00)
    # BLINK_ON = const(0x01)
    BLINK_OFF = const(0x00)

    # flags for display/cursor shift
    # DISP_MOVE = const(0x08)
    # CURS_MOVE = const(0x00)
    # MOVE_RIGHT = const(0x04)
    # MOVE_LEFT = const(0x00)

    # flags for function set
    # MODE_8BIT = const(0x10)
    MODE_4BIT = const(0x00)
    LINES_2 = const(0x08)
    LINES_1 = const(0x00)
    DOTS_5x8 = const(0x00)

    def __init__(self, sda_, scl_, col=16, row=2):
        i = 0 if sda_ in (0, 4, 8, 12, 16, 20) else 1
        self.i2c = I2C(i, sda=Pin(sda_), scl=Pin(scl_), freq=400_000)
        self._col = col
        self._row = row
        self._show_fn = self.MODE_4BIT | self.LINES_1 | self.DOTS_5x8
        try:
            # self.address info only; ADDRESS used in code
            self.address = self.i2c.scan()[0]
        except IndexError:
            raise Exception('I2C address not found.')
        self.start(row)
        self._n_lines = None
        self._curr_line = None
        self._show_ctrl = None
        self._show_mode = None

    def _command(self, cmd):
        self.i2c.writeto_mem(self.I2C_ADDR, 0x80, chr(cmd))

    def _write(self, data):
        self.i2c.writeto_mem(self.I2C_ADDR, 0x40, chr(data))

    def set_cursor(self, col, row):
        col |= 0x80 if row == 0 else 0xc0
        self.i2c.writeto(self.I2C_ADDR, bytearray([0x80, col]))

    def clear(self):
        self._command(self.CLR_DISP)
        time.sleep_ms(2)

    def write_out(self, arg):
        for b in bytearray(str(arg), 'utf-8'):
            self.i2c.writeto_mem(self.I2C_ADDR, 0x40, chr(b))

    def display(self):
        self._show_ctrl |= self.DISP_ON
        self._command(self.DISP_CONTROL | self._show_ctrl)

    def start(self, lines):
        self._n_lines = lines
        self._curr_line = 0
        self._show_fn |= self.LINES_2 if lines > 1 else self.LINES_1
        time.sleep_ms(50)

        # Send function set command 3 times (apparently required)
        for _ in range(3):
            self._command(self.FN_SET | self._show_fn)
            time.sleep_ms(5)  # wait more than 4.1ms
        # turn the display on, cursor and blinking off
        self._show_ctrl = self.DISP_ON | self.CURS_OFF | self.BLINK_OFF
        self.display()
        self.clear()
        # Initialize to L > R text direction
        self._show_mode = self.ENT_LEFT | self.ENT_SHIFT_DEC
        self._command(self.ENTRY_MODE | self._show_mode)

    # helper functions

    def write_line(self, row, text):
        self.set_cursor(0, row)
        self.write_out(text)
