# motor_control.py
""" run dc motor(s) under PWM control
    - developed using MicroPython v1.22.0
    - developed for Famous Trains Derby by David Jones
    - shared with MERG by member 9042
"""

import asyncio
import time
from micropython import const
from l298n import L298N


class MotorCtrl:
    """ control state/direction and speed of a motor
        - negative speeds are not supported
        - call set_state() to change direction to 'F' or 'R'
    """

    KICK_U16 = const(0xffff // 2)

    @staticmethod
    def pc_u16(percentage):
        """ convert positive percentage to 16-bit equivalent """
        if 0 < percentage <= 100:
            return 0xffff * percentage // 100
        else:
            return 0

    def __init__(self, channel, name, min_pc=0):
        self.channel = channel
        self.name = name  # for print or logging
        self.min_u16 = self.pc_u16(min_pc)  # start-up speed
        self.state = ''
        self.speed_u16 = 0
        self.states_set = channel.STATES_SET
        self.run_set = {'F', 'R', 'f', 'r'}

    def set_state(self, state):
        """ set 'F' forward, 'R' reverse, or 'S' stop  """
        if state in self.states_set:
            self.channel.set_state(state)
            self.state = state
        else:
            print(f'Unknown state: {state} in set_state()')

    def rotate_u16(self, dc_u16):
        """ rotate motor in state direction at u16 duty cycle """
        self.channel.set_dc_u16(dc_u16)
        self.speed_u16 = dc_u16

    def kick_start(self):
        """ send pulses to start a motor """
        if self.state in self.run_set:
            self.channel.set_dc_u16(self.KICK_U16)
            time.sleep_us(100)
            self.channel.set_dc_u16(self.min_u16)

    async def accel_u16(self, target_pc, period_ms=1_000):
        """ accelerate from current to target speed in trans_period_ms
            - supports (target < current) for deceleration
        """
        # consider passing period as parameter
        if self.state in self.run_set:
            n_steps = 25
            target_u16 = self.pc_u16(target_pc)
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

    def halt(self):
        """ set speed immediately to 0 but retain state """
        self.rotate_u16(0)

    def stop(self):
        """ set state to 'S'; halt the motor """
        self.set_state('S')
        self.rotate_u16(0)
        print(f'Motor {self.name} stopped')

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
        'pulse_f': 500,
        'motor_start_pc': 30,
        'motor_a_speed': {'f': 100, 'r': 95},
        'motor_b_speed': {'f': 95, 'r': 95},
        'motor_hold_period': 5
    }

    controller = L298N(params['pwm_pins'], params['bridge_pins'], params['pulse_f'])
    motor_a = MotorCtrl(controller.channel_a, name='A', min_pc=params['motor_start_pc'])
    motor_b = MotorCtrl(controller.channel_b, name='B', min_pc=params['motor_start_pc'])
    # set initial state to 'S'
    motor_a.stop()
    motor_b.stop()
    motor_a.kick_start()
    motor_a.stop()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('execution complete')
