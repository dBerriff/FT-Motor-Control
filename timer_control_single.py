# timer_control_single.py
""" run a dc motor under PWM control
    - files 2298n.py and motor_ctrl.py must be uploaded to the Pico
    - developed for Famous Trains Derby by David Jones
    - shared with MERG by member 9042
"""

import asyncio
from collections import namedtuple
from l298n import L298N
from motor_ctrl import MotorCtrl


async def main():
    """ test of motor control """

    Speed = namedtuple('Speed', ['f', 'r'])  # forward, reverse percentages
    
    async def run_sequence(motor_, motor_speed_, steady_period=2):
        """ run the locomotive """
        motor_.set_state('F')
        print('Accelerate')
        await motor_.accel_u16(motor_speed_.f, 1000)
        print('Hold speed')
        await asyncio.sleep(steady_period)
        print('Decelerate')
        await motor_.accel_u16(0, 1000)
        print('Pause')
        await asyncio.sleep(5)
        motor_.set_state('R')
        print('Accelerate')
        await motor_.accel_u16(motor_speed_.r, 1000)
        print('Hold speed')
        await asyncio.sleep(steady_period)
        print('Decelerate')
        await motor_.accel_u16(0, 1000)

    # === parameters

    pwm_pins = (2, 3)
    motor_pins = (4, 5, 6, 7)
    pulse_freq = 400  # adjust for physical motor and controller
    
    motor_speeds = Speed(f=90, r=90)

    # ===

    controller = L298N(pwm_pins, motor_pins, pulse_freq)
    motor = MotorCtrl(controller.channel_a, name='A', min_pc=25)

    # initialise state
    motor.stop()

    for _ in range(10):
        await run_sequence(motor, motor_speeds, 1.5)
        print('Pause')
        await asyncio.sleep(5)

    motor.set_logic_off()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('execution complete')
