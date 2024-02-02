# motor_control.py
""" run 2 x dc motor under PWM control
    - developed using MicroPython v1.22.0
    - user button-press initiates motor movement
    - moves Forward and Reverse alternatively
    - subsequent button-press is blocked for a set period
"""

import asyncio
from l298n import L298N
from motor_ctrl import MotorCtrl
from buttons import Button
from led import Led
from config import ConfigFile
import lcd_1602


class InputButtons:
    """ input buttons """

    def __init__(self, run_pin, kill_pin):
        self.run_btn = Button(run_pin)
        self.kill_btn = Button(kill_pin)

    async def poll_buttons(self):
        """ start button polling """
        # buttons self-poll to return change-state Event
        asyncio.create_task(self.run_btn.poll_state())
        asyncio.create_task(self.kill_btn.poll_state())


async def main():
    """ test of motor control """
    
    def lcd_print(row, text):
        lcd.set_cursor(0, row)
        lcd.printout(text)

    async def monitor_kill_btn(kill_btn_, controller_):
        """ monitor for kill-button press
            - this Event should invoke layout switch-off
        """
        await kill_btn_.press_ev.wait()
        kill_btn_.press_ev.clear()
        controller_.set_logic_off()
        lcd.clear()
        lcd.set_cursor(0, 0)
        lcd.printout('End execution!')

    async def run_incline(
            demand_btn_,
            motor_a_, motor_b_, motor_a_speed_, motor_b_speed_, hold_s_,
            block_period, led_):
        """ run the incline motors under button control """

        state_ = 'S'
        while True:
            lcd.clear()
            lcd.set_cursor(0, 0)
            lcd.printout("Waiting ")
            led_.led.on()
            await demand_btn_.press_ev.wait()
            lcd.clear()
            led_.led.off()
            if state_ != 'F':
                lcd_print(0, 'F accel ')
                state_ = 'F'
                motor_a_.set_state('F')
                motor_b_.set_state('F')
                lcd_print(1,
                    f'A: {motor_a_speed_['F']:02d}% B: {motor_b_speed_['F']:02d}%')
                await asyncio.gather(
                    motor_a_.accel_pc(motor_a_speed_['F']),
                    motor_b_.accel_pc(motor_b_speed_['F']))
                lcd_print(0, 'F hold ')
                await asyncio.sleep(hold_s_)
                lcd_print(0, 'F decel ')
                lcd_print(1, f'A: {0:02d}% B: {0:02d}%')
                await asyncio.gather(
                    motor_a_.accel_pc(0),
                    motor_b_.accel_pc(0))
                lcd_print(0, 'Stopped ')

            else:
                lcd.set_cursor(0, 0)
                lcd.printout('R accel ')
                state_ = 'R'
                motor_a_.set_state('R')
                motor_b_.set_state('R')
                lcd.set_cursor(0, 1)
                lcd.printout(
                    f'A: {motor_a_speed_['R']:02d}% B: {motor_b_speed_['R']:02d}%')
                await asyncio.gather(
                    motor_a_.accel_pc(motor_a_speed_['R']),
                    motor_b_.accel_pc(motor_b_speed_['R']))
                lcd.set_cursor(0, 0)
                lcd.printout('R hold  ')
                await asyncio.sleep(hold_s_)
                lcd.set_cursor(0, 0)
                lcd.printout('R decel ')
                lcd.set_cursor(0, 1)
                lcd.printout(f'A: {0:02d}% B: {0:02d}%')
                await asyncio.gather(
                    motor_a_.accel_pc(0),
                    motor_b_.accel_pc(0))
                lcd.set_cursor(0, 0)
                lcd.printout('Stopped ')
 
            # not strictly required but set state 'S'
            motor_a.stop()
            motor_b.stop()
            # block button response
            await asyncio.sleep(block_period)
            demand_btn_.press_ev.clear()  # clear any intervening press

    params = {
        'i2c_pins': (4, 5),  # sda, scl
        'pwm_pins': (8, 9),
        'bridge_pins': (10, 11, 12, 13),
        'run_btn': 20,
        'kill_btn': 22,
        'pulse_f': 20_000,
        'motor_start_pc': 25,
        'motor_a_speed': {'F': 90, 'R': 50},
        'motor_b_speed': {'F': 85, 'R': 90},
        'motor_hold_period': 5
    }

    # params = ConfigFile('incline.json', params).read_cf()

    onboard = Led('LED')
    lcd = lcd_1602.Lcd1602(*params['i2c_pins'])

    controller = L298N(params['pwm_pins'], params['bridge_pins'], params['pulse_f'])
    motor_a = MotorCtrl(controller.channel_a, name='A', min_pc=params['motor_start_pc'])
    motor_b = MotorCtrl(controller.channel_b, name='B', min_pc=params['motor_start_pc'])
    # set initial state to 'S'
    motor_a.stop()
    motor_b.stop()

    ctrl_buttons = InputButtons(params['run_btn'], params['kill_btn'])
    asyncio.create_task(ctrl_buttons.poll_buttons())  # buttons self-poll

    lcd.set_cursor(0, 0)
    lcd.printout("FT IC V1.0")
    await asyncio.sleep_ms(2000)

    asyncio.create_task(
        run_incline(ctrl_buttons.run_btn,
                    motor_a, motor_b,
                    params['motor_a_speed'], params['motor_b_speed'],
                    params['motor_hold_period'], 5, onboard))
    await monitor_kill_btn(ctrl_buttons.kill_btn, controller)
    
    # kill button has been pushed; wait a few ms for motors to stop
    await asyncio.sleep_ms(20)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('execution complete')
