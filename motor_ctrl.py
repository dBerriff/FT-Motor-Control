# motor_control.py
""" run dc motor(s) under PWM control """

import asyncio


class MotorCtrl:
    """ control speed and direction of dc motor """
    
    @staticmethod
    def pc_u16(percentage):
        return 0xffff * percentage // 100

    def __init__(self, channel, name, start_pc=0):
        self.channel = channel
        self.name = name  # for print or logging
        self.start_u16 = self.pc_u16(start_pc)
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

    async def accel(self, target_pc, n_steps=25):
        """ accelerate from stop to target speed over n_steps """
        target_u16 = self.pc_u16(target_pc)
        step = (target_u16 - self.speed_u16) // n_steps
        for speed in range(self.speed_u16, target_u16, step):
            self.rotate(speed)
            await asyncio.sleep_ms(5000//n_steps)  # period // n_steps
        self.rotate(target_u16)

    async def halt(self):
        """ set speed instantly to 0 but retain state """
        self.rotate(0)
        # allow some time to halt
        await asyncio.sleep_ms(500)

    async def stop(self):
        """ set state to 'S', halt the motor """
        self.set_state('S')
        await self.halt()

    def set_logic_off(self):
        """ turn off channel logic """
        self.channel.set_logic_off()
