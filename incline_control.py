# motor_control.py
""" run 2 x dc motors under PWM control
    - developed using MicroPython v1.22.0
    - user button-press initiates motor movement
    - moves Forward and Reverse alternatively
    - button-press is blocked for a set period when pressed
"""

import asyncio
import time
from hb_l298n import L298N
from motor_ctrl import MotorCtrl
from buttons import Button, HoldButton
from lcd_1602 import LcdApi
from config import read_cf


class InputButtons:
    """ input buttons """

    def __init__(self, buttons):
        self.run_btn = Button(buttons["run"])
        self.kill_btn = HoldButton(buttons["kill"])

    async def poll_buttons(self):
        """ start button polling """
        # buttons self-poll to set Event when clicked
        asyncio.create_task(self.run_btn.poll_state())
        asyncio.create_task(self.kill_btn.poll_state())


class CtrlState:
    """ set states: Off, Run, Cal """

    def __init__(self):
        pass

    async def set_off(self):
        """ set state off """
        pass

    async def set_run(self):
        """ set state run """
        pass

    async def set_cal(self):
        """ set state cal (calibrate) """
        pass

    @staticmethod
    async def no_t():
        """ coro: no transition """
        await asyncio.sleep_ms(1)
        # no change in state


async def main():
    """ test of motor control """

    def pc_u16(percentage):
        """ convert positive percentage to 16-bit equivalent """
        if 0 < percentage <= 100:
            return 0xffff * percentage // 100
        else:
            return 0

    async def monitor_kill_btn(kill_btn_):
        """
            poll for kill-button hold
            - intended as emergency or end-of-day switch-off
            - main() should exit if this task ends
        """
        while True:
            kill_btn_.press_ev.clear()
            await kill_btn_.press_ev.wait()
            if kill_btn_.state == kill_btn_.HOLD:
                controller.set_logic_off()
                lcd.clear()
                lcd.write_line(0, 'End execution')
                lcd.write_line(1, 'Track power OFF')
                return
            await asyncio.sleep(1)

    async def run_incline(btns_, hold_ms, block_s):
        """ run the incline motors under button control """

        async def countdown(period_s):
            """ countdown period seconds """
            while period_s:
                lcd.write_line(1, f'{period_s:2d}')
                await asyncio.sleep_ms(1000)
                period_s -= 1

        run_btn_ = btns_.run_btn
        state_ = 'S'
        while True:
            lcd.clear()
            lcd.write_line(0, "Waiting...")
            await run_btn_.press_ev.wait()
            lcd.clear()
            if state_ != 'F':
                speed_string = (f'A:{controller.a_speeds['F']:05d} ' +
                                f'B:{controller.b_speeds['F']:05d} ')
                lcd.write_line(0, 'Fwd accel ')
                lcd.write_line(1, speed_string)
                               
                await controller.accel_a_b('F')
                lcd.write_line(0, 'Fwd hold  ')
                await asyncio.sleep_ms(hold_ms)
                lcd.write_line(0, 'Fwd stop  ')
                lcd.write_line(1, f'A:{0:05d} B:{0:05d} ')
                controller.stop_a_b()
                state_ = 'F'
            else:
                lcd.write_line(0, 'Rev accel ')
                lcd.write_line(1,
                               f'A:{controller.a_speeds['R']:05d} ' +
                               f'B:{controller.b_speeds['R']:05d} ')
                await controller.accel_a_b('R')
                lcd.write_line(0, 'Rev hold  ')
                await asyncio.sleep_ms(hold_ms)
                lcd.write_line(0, 'Rev stop  ')
                lcd.write_line(1, f'A:{0:05d} B:{0:05d} ')
                controller.stop_a_b()
                state_ = 'R'

            # block button response
            await countdown(block_s)
            run_btn_.press_ev.clear()  # clear all intervening presses

    # === default parameters: ignored if JSON file found

    io_p = {
        'i2c_pins': {'sda': 0, 'scl': 1},
        'cols_rows': (16, 2),
        'buttons': {'run': 6, 'kill': 9},
        'block': 60}  # s
    l298n_p = {
        'pins': (22, 21, 20, 19, 18, 17),  # enA, in1, in2, in3, in4, enB
        'pulse_f': 10_000}  # Hz
    motor_p = {   
        'start_pc': 25,  # %
        'a_speed': {'F': 50, 'R': 50},
        'b_speed': {'F': 50, 'R': 50},
        'hold': 5_000}  # ms

    # ===
    
    io_p = read_cf('io_p.json', io_p)
    l298n_p = read_cf('l298n_p.json', l298n_p)
    motor_p = read_cf('motor_p.json', motor_p)
    print('JSON parameters:')
    print(f'io_p: {io_p}')
    print(f'l298n_p: {l298n_p}')
    print(f'motor_p: {motor_p}')

    lcd = LcdApi(io_p['i2c_pins'])
    if lcd.lcd_mode:
        lcd.write_line(0, f'FT Incline V1.2')
        lcd.write_line(1, f'I2C addr: {lcd.I2C_ADDR}')
    else:
        print('LCD Display not found')

    board_pins = L298N.PinTuple
    pins = board_pins(*l298n_p['pins'])
    print(f'H-bridge pins: {pins}')
    board = L298N(pins, l298n_p['pulse_f'])

    a_speeds = {'F': pc_u16(motor_p['a_speed']['F']),
                'R': pc_u16(motor_p['a_speed']['R'])
                }
    b_speeds = {'F': pc_u16(motor_p['b_speed']['F']),
                'R': pc_u16(motor_p['b_speed']['R'])
                }
    
    controller = MotorCtrl(board, a_speeds, b_speeds)

    ctrl_buttons = InputButtons(io_p['buttons'])
    asyncio.create_task(ctrl_buttons.poll_buttons())  # buttons self-poll

    asyncio.create_task(run_incline(ctrl_buttons, motor_p['hold'], io_p['block']))
    print('\nIncline control active')
    await monitor_kill_btn(ctrl_buttons.kill_btn)

    # display kill message
    time.sleep_ms(3_000)
    lcd.clear()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('Execution complete')
