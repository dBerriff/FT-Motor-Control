# motor_control.py
""" run 2 x dc motor under PWM control
    - developed using MicroPython v1.22.0
    - user button-press initiates motor movement
    - moves Forward and Reverse alternatively
    - subsequent button-press is blocked for a set period
"""

import asyncio
from collections import namedtuple
from l298n import L298N
from motor_ctrl import MotorCtrl
from buttons import Button
from led import Led


class InputButtons:
    """ input buttons """

    def __init__(self, run_pin, kill_pin):
        self.run_btn = Button(run_pin)
        self.kill_btn = Button(kill_pin)

    async def poll_buttons(self):
        """ start button polling """
        # buttons: self-poll to set state
        asyncio.create_task(self.run_btn.poll_state())
        asyncio.create_task(self.kill_btn.poll_state())


async def main():
    """ test of motor control """

    Speed = namedtuple('Speed', ['f', 'r'])  # forward, reverse percentages

    async def monitor_kill_btn(kill_btn_, controller_):
        """ monitor for kill-button press
            - this Event should invoke layout switch-off
        """
        await kill_btn_.press_ev.wait()
        kill_btn_.press_ev.clear()
        controller_.set_logic_off()
        print('Kill button pressed - control board logic switched OFF')

    async def run_incline(
            demand_btn_,
            motor_a_, motor_b_, motor_a_speed_, motor_b_speed_, hold_period_,
            led_):
        """ run the incline motors under button control """

        block_period = 5  # s; block next button press
        state_ = 'S'
        while True:
            print('Waiting for button press...')
            led_.led.on()
            await demand_btn_.press_ev.wait()
            led_.led.off()
            if state_ != 'F':
                print('Move Forward  ')
                state_ = 'F'
                motor_a_.set_state('F')
                motor_b_.set_state('F')
                print('Accelerate')
                await asyncio.gather(
                    motor_a_.accel(motor_a_speed_.f),
                    motor_b_.accel(motor_b_speed_.f))
                await asyncio.sleep(hold_period_)
                print('Decelerate')
                await asyncio.gather(
                    motor_a_.accel(0),
                    motor_b_.accel(0))
            else:
                print('Move Reverse')
                state_ = 'R'
                motor_a_.set_state('R')
                motor_b_.set_state('R')
                print('Accelerate')
                await asyncio.gather(
                    motor_a_.accel(motor_a_speed_.r),
                    motor_b_.accel(motor_b_speed_.r))
                await asyncio.sleep(hold_period_)
                print('Decelerate')
                await asyncio.gather(
                    motor_a_.accel(0),
                    motor_b_.accel(0))

            # not strictly required but set state 'S'
            await motor_a.stop()
            await motor_b.stop()
            # block button response
            await asyncio.sleep(block_period)
            demand_btn_.press_ev.clear()  # clear any intervening press

    # === parameters

    pwm_pins = (2, 3)
    bridge_pins = (4, 5, 6, 7)
    run_btn = 20
    kill_btn = 22

    pulse_f = 500  # adjust for physical motor and controller
    motor_start_pc = 30
    motor_a_speed = Speed(f=100, r=95)
    motor_b_speed = Speed(f=95, r=95)
    motor_hold_period = 5

    # ===
    
    onboard = Led('LED')

    controller = L298N(pwm_pins, bridge_pins, pulse_f)
    motor_a = MotorCtrl(controller.channel_a, name='A', start_pc=motor_start_pc)
    motor_b = MotorCtrl(controller.channel_b, name='B', start_pc=motor_start_pc)

    # set initial state to 'S'
    await motor_a.stop()
    await motor_b.stop()

    ctrl_buttons = InputButtons(run_btn, kill_btn)
    asyncio.create_task(ctrl_buttons.poll_buttons())  # buttons self-poll

    asyncio.create_task(
        run_incline(ctrl_buttons.run_btn,
                    motor_a, motor_b, motor_a_speed, motor_b_speed, motor_hold_period,
                    onboard))
    await monitor_kill_btn(ctrl_buttons.kill_btn, controller)
    
    # kill button has been pushed
    await asyncio.sleep_ms(20)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('execution complete')
