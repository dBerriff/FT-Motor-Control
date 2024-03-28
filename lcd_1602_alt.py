import machine
from micropython import const
import time

COLUMNS = const(16)
ROWS = const(2)

# Instruction set
CLEARDISPLAY = const(0x01)

ENTRYMODESET = const(0x04)
ENTRYLEFT = const(0x02)
ENTRYRIGHT = const(0x00)
ENTRYSHIFTINCREMENT = const(0x01)
ENTRYSHIFTDECREMENT = const(0x00)

DISPLAYCONTROL = const(0x08)
DISPLAYON = const(0x04)
DISPLAYOFF = const(0x00)
CURSORON = const(0x02)
CURSOROFF = const(0x00)
BLINKON = const(0x01)
BLINKOFF = const(0x00)

FUNCTIONSET = const(0x20)
_5x10DOTS = const(0x04)
_5x8DOTS = const(0x00)
_1LINE = const(0x00)
_2LINE = const(0x08)
_8BITMODE = const(0x10)
_4BITMODE = const(0x00)


class LCD:
    def __init__(self, sda, scl):
        _sda = machine.Pin(sda)
        _scl = machine.Pin(scl)
        self.column = 0
        self.row = 0
        self.address = const(62)
        self.command = bytearray(2)

        if sda in (0, 4, 8, 12, 16, 20):
            self.i2c = machine.I2C(0, sda=_sda, scl=_scl, freq=400_000)
        else:
            self.i2c = machine.I2C(1, sda=_sda, scl=_scl, freq=400_000)
        time.sleep_ms(50)

        for i in range(3):
            self._command(FUNCTIONSET | _2LINE)
            time.sleep_ms(10)

        self.on()
        self.clear()
        self._command(ENTRYMODESET | ENTRYLEFT | ENTRYSHIFTDECREMENT)
        self.set_cursor(0, 0)

    def on(self, cursor=False, blink=False):
        c_state = CURSORON if cursor else CURSOROFF
        b_state = BLINKON if blink else BLINKOFF
        self._command(DISPLAYCONTROL | DISPLAYON | c_state | b_state)

    def off(self):
        self._command(DISPLAYCONTROL | DISPLAYOFF | CURSOROFF | BLINKOFF)

    def clear(self):
        self._command(CLEARDISPLAY)
        self.set_cursor(0, 0)

    def set_cursor(self, column, row):
        column = column % COLUMNS
        row = row % ROWS
        command = column | 0x80 if row == 0 else column | 0xC0
        self.row = row
        self.column = column
        self._command(command)

    def write(self, s):
        for i in range(len(s)):
            time.sleep_ms(10)
            self.i2c.writeto(self.address, b'\x40' + s[i])
            self.column = self.column + 1
            if self.column >= COLUMNS:
                self.set_cursor(0, self.row + 1)

    def _command(self, value):
        self.command[0] = 0x80
        self.command[1] = value
        self.i2c.writeto(self.address, self.command)
        time.sleep_ms(1)
