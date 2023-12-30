# motor_control.py
""" run dc motor(s) under PWM control """

import asyncio
from collections import namedtuple
from l298n import L298N
from motor_ctrl import MotorCtrl


async def main():
    """ test of motor control """
    
    async def run_sequence(motor_, motor_speed_, steady_period=15):
        """ run the locomotive """
        motor_.set_state('F')
        print('Accelerate')
        await motor_.accel(motor_speed_.f)
        print('Hold speed')
        await asyncio.sleep(steady_period)
        print('Decelerate')
        await motor_.accel(0)
        print('Pause')
        await asyncio.sleep(15)
        
        motor_.set_state('R')
        print('Accelerate')
        await motor_.accel(motor_speed_.r)
        print('Hold speed')
        await asyncio.sleep(steady_period)
        print('Decelerate')
        await motor_.accel(0)

    Speed = namedtuple('Speed', ['f', 'r'])  # forward, reverse percentages
    
    pwm_pins = (2, 3)
    motor_pins = (4, 5, 6, 7)
    pulse_freq = 15_000  # adjust for physical motor and controller

    controller = L298N(pwm_pins, motor_pins, pulse_freq)
    motor_a = MotorCtrl(controller.channel_a, name='A', start_pc=25)
    # establish initial state
    await motor_a.stop()

    motor_a_speed = Speed(f=75, r=30)
    
    await asyncio.sleep(10)

    for _ in range(5):
        await run_sequence(motor_a, motor_a_speed)
        await asyncio.sleep(10)

    motor_a.set_logic_off()
    await asyncio.sleep_ms(20)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('execution complete')
