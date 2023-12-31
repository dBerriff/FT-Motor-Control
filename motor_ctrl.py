# motor_control.py
""" run dc motor(s) under PWM control
    - developed for Famous Trains Derby by David Jones
    - shared with MERG by member 9042
"""

import asyncio


class MotorCtrl:
    """ control state/direction and speed of a motor
        - negative speeds are not supported
        - call set_state() to change direction
    """
    
    @staticmethod
    def pc_u16(percentage):
        return 0xffff * percentage // 100

    def __init__(self, channel, name, start_pc=0):
        self.channel = channel
        self.name = name  # for print or logging
        self.start_u16 = self.pc_u16(start_pc)  # start-up speed
        self.state = ''
        self.speed_u16 = 0

    def set_state(self, state):
        """ set 'F' forward, 'R' reverse, or 'S' stop  """
        self.channel.set_state(state)
        self.state = state

    def rotate(self, dc_u16):
        """ rotate motor in state direction at u16 duty cycle """
        self.channel.set_dc_u16(dc_u16)
        self.speed_u16 = dc_u16

    async def accel(self, target_pc, trans_period_ms=5_000):
        """ accelerate from current to target speed in trans_period_ms
            - supports (target < current) for deceleration
        """
        # consider passing period as parameter
        n_steps = 25
        target_u16 = abs(self.pc_u16(target_pc))
        # check for start from rest
        if self.speed_u16 == 0 and target_u16 > 0:
            self.speed_u16 = self.start_u16
        step = (target_u16 - self.speed_u16) // n_steps
        # check for stepped acceleration
        if step != 0:
            pause_ms = trans_period_ms // n_steps
            for speed in range(self.speed_u16, target_u16, step):
                self.rotate(speed)
                await asyncio.sleep_ms(pause_ms)
        self.rotate(target_u16)

    async def halt(self):
        """ set speed immediately to 0 but retain state """
        self.rotate(0)

    async def stop(self):
        """ set state to 'S'; halt the motor """
        self.set_state('S')
        self.rotate(0)

    def set_logic_off(self):
        """ turn off channel logic """
        self.channel.set_logic_off()
