# motor_control.py
""" run dc motor(s) under PWM control
    - developed using MicroPython v1.22.0
    - developed for Famous Trains Derby by David Jones
    - shared with MERG by member 9042
"""

import asyncio
from l298n import L298N


class MotorCtrl:
    """ control state/direction/speed of a motor
        - negative speeds not supported
    """

    @staticmethod
    def pc_u16(percentage):
        """ convert positive percentage to 16-bit equivalent """
        if 0 < percentage <= 100:
            return 0xffff * percentage // 100
        else:
            return 0

    def __init__(self, channel, name, min_pc):
        self.channel = channel
        self.name = name  # for print or logging
        self.min_u16 = self.pc_u16(min_pc)  # start-up speed
        self.state = ''
        self.speed_u16 = 0
        self.states = channel.STATES
        self.run_set = {'F', 'R', 'f', 'r'}

    def set_state(self, state):
        """ 'F' forward, 'R' reverse, or 'S' stop  """
        if state in self.states:
            self.channel.set_state(state)
            self.state = state
        else:
            print(f'Unknown state: {state}')

    def rotate_u16(self, dc_u16):
        """ rotate motor at u16 duty cycle """
        self.channel.set_dc_u16(dc_u16)
        self.speed_u16 = dc_u16

    def rotate_pc(self, dc_pc):
        """ rotate motor at pc% duty cycle """
        self.rotate_u16(self.pc_u16(dc_pc))

    async def accel_pc(self, target_pc, period_ms=1_000):
        """ accelerate from current to target speed in trans_period_ms
            - supports (target < current) for deceleration
        """
        if self.state in self.run_set:
            target_u16 = self.pc_u16(target_pc)
            if target_u16 < self.min_u16:
                target_u16 = 0
            n_steps = 25
            # check for start from rest
            if self.speed_u16 == 0 and target_u16 > 0:
                self.speed_u16 = self.min_u16
            step = (target_u16 - self.speed_u16) // n_steps
            # check for stepped acceleration
            if step != 0:
                pause_ms = period_ms // n_steps
                for speed in range(self.speed_u16, target_u16, step):
                    self.rotate_u16(speed)
                    await asyncio.sleep_ms(pause_ms)
            self.rotate_u16(target_u16)
        else:
            self.stop()

    def halt(self):
        """ set speed immediately to 0 but retain state """
        self.rotate_u16(0)

    def stop(self):
        """ set state to 'S'; halt the motor """
        self.set_state('S')
        self.rotate_u16(0)

    def set_logic_off(self):
        """ turn off channel logic """
        self.channel.set_logic_off()


async def main():
    """ test motor methods """

    params = {
        'pwm_pins': (2, 3),
        'bridge_pins': (4, 5, 6, 7),
        'run_btn': 20,
        'kill_btn': 22,
        'pulse_f': 20_000,
        'motor_min_pc': 5,
        'motor_a_speed': {'F': 100, 'R': 95},
        'motor_b_speed': {'F': 95, 'R': 95},
        'motor_hold_period': 5
    }

    controller = L298N(params['pwm_pins'], params['bridge_pins'], params['pulse_f'])
    motor_a = MotorCtrl(controller.channel_a, name='A', min_pc=params['motor_min_pc'])

    print('Forward')
    motor_a.set_state('F')
    motor_a.rotate_u16(motor_a.min_u16)
    await asyncio.sleep(5)
    motor_a.stop()
    await asyncio.sleep(1)
    print('Reverse')
    motor_a.set_state('R')
    motor_a.rotate_u16(motor_a.min_u16)
    await asyncio.sleep(5)
    print('Stop')
    motor_a.stop()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('execution complete')
 