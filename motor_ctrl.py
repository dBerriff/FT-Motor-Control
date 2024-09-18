# motor_control.py
""" run dc motor(s) under PWM control
    - developed using MicroPython v1.22.0
    - developed for Famous Trains Derby by David Jones
    - shared with MERG by member 9042
"""

import asyncio
from hb_l298n import L298N
from lcd_1602 import LcdApi
from config import read_cf, pc_u16


class MotorCtrl:
    """ control direction and speed of a 2-channel motor board """

    def __init__(self, board, a_speeds, b_speeds, start_u16=16_383):
        self.board = board
        self.a_speeds = a_speeds
        self.b_speeds = b_speeds
        self.start_u16 = start_u16
        self.chan_a = board.channel_a
        self.chan_b = board.channel_b
        self.states = board.STATES
        self.states_set = board.STATES_SET
        self.halt_a_b()

    def set_state(self, state, channel):
        """ set channel h-pins  """
        if channel == 'A':
            self.board.channel_a.set_state(state)
        elif channel == 'B':
            self.board.channel_b.set_state(state)

    async def change_speed(self, channel, current_u16, target_u16, t_ms, n_steps):
        """ accelerate channel from current to target duty cycle """
        step = (target_u16 - current_u16) // n_steps
        step_ms = t_ms // n_steps
        for dc_u16 in range(self.start_u16, target_u16, step):
            channel.set_dc_u16(dc_u16)
            await asyncio.sleep_ms(step_ms)
        channel.set_dc_u16(target_u16)

    async def start(self, channel, target_u16, period_ms, n_steps=25):
        """ accelerate channel from 0 to target duty cycle """
        await self.change_speed(channel, self.start_u16, target_u16, period_ms, n_steps)

    async def stop(self, channel, current_u16, period_ms, n_steps=25):
        """ decelerate channel from current duty cycle to 0 """
        await self.change_speed(channel, current_u16, 0, period_ms, n_steps)

    def set_state_a_b(self, state):
        """ set both channel h-pins  """
        if state in self.states_set:
            self.board.channel_a.set_state(state)
            self.board.channel_b.set_state(state)

    def halt_a_b(self):
        """ stop both motors """
        self.board.channel_a.stop()
        self.board.channel_b.stop()

    async def start_a_b(self, direction, period_ms=1_000):
        """ accelerate both motors """
        self.set_state_a_b(direction)
        await asyncio.gather(self.start(self.chan_a, self.a_speeds[direction], period_ms),
                             self.start(self.chan_b, self.b_speeds[direction], period_ms)
                             )

    async def stop_a_b(self, direction, period_ms=1_000):
        """ accelerate both motors """
        await asyncio.gather(self.stop(self.chan_a, self.a_speeds[direction], period_ms),
                             self.stop(self.chan_b, self.b_speeds[direction], period_ms)
                             )


async def main():
    """ test motor methods """
    
    io_p = read_cf('io_p.json')
    l298n_p = read_cf('l298n_p.json')
    motor_p = read_cf('motor_p.json')
    lcd = LcdApi(io_p['i2c_pins'])
    if lcd.lcd_mode:
        lcd.write_line(0, f'FT Timed V1.0')
        lcd.write_line(1, f'I2C addr: {lcd.I2C_ADDR}')
    else:
        print('LCD Display not found')
    await asyncio.sleep_ms(2_000)
    lcd.clear()

    board = L298N(l298n_p['pins'], l298n_p['pulse_f'])
    a_speeds = {'F': pc_u16(motor_p['a_speed']['F']),
                'R': pc_u16(motor_p['a_speed']['R'])
                }
    b_speeds = {'F': pc_u16(motor_p['b_speed']['F']),
                'R': pc_u16(motor_p['b_speed']['R'])
                }
    
    long_pause = 5  # s
    controller = MotorCtrl(board, a_speeds, b_speeds)
    for _ in range(1):
        lcd.write_line(0, f'Forward')
        await controller.start_a_b('F')
        await asyncio.sleep(4)
        lcd.write_line(0, f'Stop')
        await controller.stop_a_b('F')
        await asyncio.sleep(3)
        lcd.write_line(0, f'Reverse')
        await controller.start_a_b('R')
        await asyncio.sleep(4)
        lcd.write_line(0, f'Stop')
        await controller.stop_a_b('R')
        await asyncio.sleep(long_pause)

    controller.halt_a_b()
    print('Controller logic turned off')
    await asyncio.sleep_ms(500)
    lcd.clear()
    await asyncio.sleep_ms(500)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('execution complete')
 