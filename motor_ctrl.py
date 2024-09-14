# motor_control.py
""" run dc motor(s) under PWM control
    - developed using MicroPython v1.22.0
    - developed for Famous Trains Derby by David Jones
    - shared with MERG by member 9042
"""

import asyncio
from l298n import L298N


class MotorCtrl:
    """ control direction and speed of a 2-channel motor board """

    def __init__(self, board, a_speeds, b_speeds, start_u16=16_383):
        self.board = board
        self.a_speeds = a_speeds
        self.b_speeds = b_speeds
        self.start_u16 = start_u16  # start-up speed
        self.states = board.STATES
        self.states_set = board.STATES_SET
        self.run_set = {'F', 'R'}
        self.speed_u16 = 0
        self.stop_a_b()
        self.state = 'S'

    def set_state_a_b(self, state):
        """ set channel state pins  """
        if state in self.states_set:
            self.board.channel_a.set_state(state)
            self.board.channel_b.set_state(state)
            self.state = state
        else:
            print(f'Unknown state: {state}')

    def stop_a_b(self):
        """ stop both motors """
        self.board.channel_a.stop()
        self.board.channel_b.stop()
        self.state = 'S'

    def set_logic_off(self):
        """ turn off channel logic """
        self.board.channel_a.set_logic_off()
        self.board.channel_b.set_logic_off()
        self.state = 'H'

    async def accel(self, channel, target_u16, period_ms):
        """ accelerate channel from current to target duty cycle """
        current_dc = channel.dc_u16
        delta = target_u16 - current_dc
        if delta == 0:
            return
        # start from rest?
        if current_dc == 0:
            current_dc = self.start_u16
            delta -= current_dc
        n_steps = 25
        step = delta // n_steps
        pause_ms = period_ms // n_steps
        for dc_u16 in range(current_dc, target_u16, step):
            channel.set_dc_u16(dc_u16)
            await asyncio.sleep_ms(pause_ms)
        channel.set_dc_u16(target_u16)

    async def accel_a_b(self, direction, period_ms=1_000):
        """ accelerate both motors """
        self.board.channel_a.set_state(direction)
        self.board.channel_b.set_state(direction)
        await asyncio.gather(self.accel(self.board.channel_a, self.a_speeds[direction], period_ms),
                             self.accel(self.board.channel_b, self.b_speeds[direction], period_ms)
                             )


async def main():
    """ test motor methods """
    
    def pc_u16(percentage):
        """ convert positive percentage to 16-bit equivalent """
        if 0 < percentage <= 100:
            return 0xffff * percentage // 100
        else:
            return 0

    params = {
        'pwm_pins': (22, 17),
        'bridge_pins': (21, 20, 19, 18),
        'pulse_f': 10_000,
        'motor_start_pc': 25,
        'motor_a_speed': {'F': 70, 'R': 50},
        'motor_b_speed': {'F': 70, 'R': 50},
        'motor_hold_period': 5
    }

    board = L298N(params['pwm_pins'], params['bridge_pins'], params['pulse_f'],
                  start_pc=params['motor_start_pc'])
    a_speeds = {'F': pc_u16(params['motor_a_speed']['F']),
                'R': pc_u16(params['motor_a_speed']['R'])
                }
    b_speeds = {'F': pc_u16(params['motor_b_speed']['F']),
                'R': pc_u16(params['motor_b_speed']['R'])
                }
    
    controller = MotorCtrl(board, a_speeds, b_speeds)
    for _ in range(2):
        print('Forward')
        await controller.accel_a_b('F')
        await asyncio.sleep(4)
        print('Stop')
        controller.stop_a_b()
        await asyncio.sleep(3)
        print('Reverse')
        await controller.accel_a_b('R')
        await asyncio.sleep(4)
        print('Stop')
        controller.stop_a_b()
        await asyncio.sleep(3)

    controller.set_logic_off()
    print('Controller logic turned off')
    await asyncio.sleep_ms(500)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('execution complete')
 