# motor_control.py
""" run dc motor(s) under PWM control """

import asyncio
from collections import namedtuple
from micropython import const
from l298n import L298N
from motor_ctrl import MotorCtrl
from buttons import Button


class Buttons:
    """ input buttons """

    def __init__(self, pins_):
        self.demand_btn = Button(pins_[0])

    async def poll_buttons(self):
        """ start button polling """
        # buttons: self poll to set state
        asyncio.create_task(self.demand_btn.poll_state())


async def main():
    """ test of motor control """
    
    async def run_incline(
        demand_btn_, motor_a_, motor_b_, motor_a_speed_, motor_b_speed_):
        """ run the incline motors """

        hold_period = 5  # s hold speed steady
        state_ = 'S'
        while True:
            print('Waiting for button press...')
            await demand_btn_.press_ev.wait()
            if state_ != 'F':
                print('Move forward')
                state_ = 'F'
                motor_a_.set_state('F')
                motor_b_.set_state('R')
                print('Accelerate')
                await asyncio.gather(
                    motor_a_.accel(motor_a_speed_.f),
                    motor_b_.accel(motor_b_speed_.r))
                print('Hold')
                await asyncio.sleep(hold_period)
                print('Decelerate')
                await asyncio.gather(
                    motor_a_.accel(0),
                    motor_b_.accel(0))
            else:
                print('Move in reverse')
                state_ = 'R'
                motor_a_.set_state('R')
                motor_b_.set_state('F')
                print('Accelerate')
                await asyncio.gather(
                    motor_a_.accel(motor_a_speed_.r),
                    motor_b_.accel(motor_b_speed_.f))
                print('Hold')
                await asyncio.sleep(hold_period)
                print('Decelerate')
                await asyncio.gather(
                    motor_a_.accel(0),
                    motor_b_.accel(0))

            # block button response
            print('Blocking button response')
            await asyncio.sleep(5)
            demand_btn_.press_ev.clear()


    # see PWM slice: frequency shared
    pwm_pins = (2, 3)
    motor_pins = (4, 5, 6, 7)
    pulse_f = 15_000  # adjust for physical motor and controller
    Speed = namedtuple('Speed', ['f', 'r'])  # forward, reverse percentages


    controller = L298N(pwm_pins, motor_pins, pulse_f)
    motor_a = MotorCtrl(controller.channel_a, name='A', start_pc=25)
    motor_b = MotorCtrl(controller.channel_b, name='B', start_pc=25)
    # establish initial state
    await motor_a.stop()
    await motor_b.stop()

    ctrl_buttons = Buttons([20])
    asyncio.create_task(ctrl_buttons.poll_buttons())  # buttons self-poll
    demand_btn = ctrl_buttons.demand_btn

    motor_a_speed = Speed(f=50, r=50)
    motor_b_speed = Speed(f=50, r=50)

    await run_incline(demand_btn, motor_a, motor_b, motor_a_speed, motor_b_speed)

    motor_a.set_logic_off()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('execution complete')
