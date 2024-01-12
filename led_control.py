# led_control.py
"""
    set LED lighting under PWM control
    - developed using MicroPython v1.22.0
    - developed for Famous Trains Derby by David Jones
    - shared with MERG by member 9042
"""

import asyncio
from micropython import const
import random
from l298n import L298N


class LedCtrl:
    """ control state/brightness of lighting """
    
    PC_U16 = tuple([pc * 0xffff // 100 for pc in range(0, 101)])
    N_STEPS = const(100)

    def __init__(self, channel, name):
        self.channel = channel
        self.name = name  # for print or logging
        self.states = channel.STATES
        self.state = ''
        self.dc_u16 = 0
        self.off()  # set state to 'S' and speed to 0

    def set_state(self, state):
        """ set 'F' forward, 'R' reverse, or 'S' off  """
        if state in self.states:
            self.channel.set_state(state)
            self.state = state
        else:
            print(f'Unknown state: {state}')

    def set_u16(self, dc_u16):
        """ set lighting to u16 duty cycle """
        self.channel.set_dc_u16(dc_u16)
        self.dc_u16 = dc_u16

    async def dimmer_pc(self, target_pc, period_ms=1_000):
        """ change brightness to target duty cycle in trans_period_ms
            - supports (target < current) for dimming
        """
        target_u16 = self.PC_U16[target_pc]
        step_u16 = (target_u16 - self.dc_u16) // self.N_STEPS
        # check for stepped change
        if step_u16 != 0:
            pause_ms = period_ms // self.N_STEPS
            for duty_cycle in range(self.dc_u16, target_u16, step_u16):
                self.set_u16(duty_cycle)
                await asyncio.sleep_ms(pause_ms)
            self.set_u16(target_u16)
        else:
            self.off()

    def off(self):
        """ turn lighting off """
        self.set_state('S')
        self.set_u16(0)

    def set_logic_off(self):
        """ turn all channel logic off """
        self.channel.set_logic_off()

    async def random_flash(self):
        """ basic random flashing events """
        for _ in range(100):
            bright_pc = random.randrange(0, 21)
            pause = random.randrange(10, 500)
            off = random.randrange(0, 2)
            self.set_u16(self.PC_U16[bright_pc])
            await asyncio.sleep_ms(pause)
            if off:
                self.set_u16(0)
                await asyncio.sleep_ms(200)
        

async def main():
    """ test LED control methods """

    params = {
        'pwm_pins': (2, 3),
        'bridge_pins': (4, 5, 6, 7),
        'run_btn': 20,
        'kill_btn': 22,
        'pulse_f': 100,
    }

    controller = L298N(params['pwm_pins'], params['bridge_pins'], params['pulse_f'])
    led_a = LedCtrl(controller.channel_a, name='A')

    # 'R' gives required polarity
    led_a.set_state('R')
    await led_a.dimmer_pc(20, 5000)
    await asyncio.sleep(5)
    await led_a.dimmer_pc(0, 5000)
    await asyncio.sleep(5)
    await led_a.random_flash()
    led_a.off()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('execution complete')
 