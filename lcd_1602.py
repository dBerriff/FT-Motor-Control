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
    ENTRY_MODE = const(0x04)
    DISP_CONTROL = const(0x08)
    FN_SET = const(0x20)

    # flags for display entry mode
    ENT_LEFT = const(0x02)
    ENT_SHIFT_DEC = const(0x00)

    # flags for display on/off control
    DISP_ON = const(0x04)
    CURS_OFF = const(0x00)
    BLINK_OFF = const(0x00)

    # flags for function set
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
            self.lcd_mode = True
            print(f'I2C address: {self.address}')
        except IndexError:
            self.lcd_mode = False
            print('I2C address not found: print mode instead.')
        if self.lcd_mode:
            self._start(row)
        self._n_lines = None
        self._curr_line = None
        self._show_ctrl = None
        self._show_mode = None

    def _command(self, cmd):
        """ invoke command """
        self.i2c.writeto_mem(self.I2C_ADDR, 0x80, chr(cmd))

    def _set_cursor(self, col, row):
        """ set cursor for write """
        col |= 0x80 if row == 0 else 0xc0
        self.i2c.writeto(self.I2C_ADDR, bytearray([0x80, col]))

    def _write(self, data):
        """ write out character at cursor position """
        self.i2c.writeto_mem(self.I2C_ADDR, 0x40, chr(data))

    def _write_out(self, arg):
        """ write out bytearray at cursor position """
        for b in bytearray(str(arg), 'utf-8'):
            self.i2c.writeto_mem(self.I2C_ADDR, 0x40, chr(b))

    def _display(self):
        """ set display state (on) """
        self._show_ctrl |= self.DISP_ON
        self._command(self.DISP_CONTROL | self._show_ctrl)

    def _start(self, lines):
        """ start routine as per Waveshare docs """
        self._n_lines = lines
        self._curr_line = 0
        self._show_fn |= self.LINES_2 if lines > 1 else self.LINES_1
        time.sleep_ms(50)

        # Send function set command 3 times (!)
        for _ in range(3):
            self._command(self.FN_SET | self._show_fn)
            time.sleep_ms(5)  # wait more than 4.1ms
        # turn the display on, cursor and blinking off
        self._show_ctrl = self.DISP_ON | self.CURS_OFF | self.BLINK_OFF
        self._display()
        self.clear()
        # Initialize to L > R text direction
        self._show_mode = self.ENT_LEFT | self.ENT_SHIFT_DEC
        self._command(self.ENTRY_MODE | self._show_mode)

    # interface functions

    def clear(self):
        if self.lcd_mode:
            self._command(self.CLR_DISP)
            time.sleep_ms(2)

    def write_line(self, row, text):
        """ write text to display row """
        if self.lcd_mode:
            self._set_cursor(0, row)
            self._write_out(text)
        else:
            print(f'{row}: {text}')
