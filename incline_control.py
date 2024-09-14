# motor_control.py
""" run 2 x dc motors under PWM control
    - developed using MicroPython v1.22.0
    - user button-press initiates motor movement
    - moves Forward and Reverse alternatively
    - button-press is blocked for a set period when pressed
"""

import asyncio
import time
from l298n import L298N
from motor_ctrl import MotorCtrl
from buttons import Button, HoldButton
from lcd_1602 import LcdApi


class InputButtons:
    """ input buttons """

    def __init__(self, buttons):
        self.run_btn = Button(buttons["run"])
        self.kill_btn = Button(buttons["kill"])
        # self.n_btn = HoldButton(buttons["N"])
        # self.s_btn = Button(buttons["S"])
        # self.e_btn = Button(buttons["E"])
        # self.w_btn = Button(buttons["W"])

    async def poll_buttons(self):
        """ start button polling """
        # buttons self-poll to set Event when clicked
        asyncio.create_task(self.run_btn.poll_state())
        asyncio.create_task(self.kill_btn.poll_state())
        # asyncio.create_task(self.n_btn.poll_state())
        # asyncio.create_task(self.s_btn.poll_state())
        # asyncio.create_task(self.e_btn.poll_state())
        # asyncio.create_task(self.w_btn.poll_state())                                                                                                                                                          


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

    async def monitor_kill_btn(kill_btn_, controller_):
        """ monitor for kill-button click
            - intended as emergency or end-of-day switch-off
        """
        await kill_btn_.press_ev.wait()
        controller_.set_logic_off()
        lcd.clear()
        lcd.write_line(0, 'End execution')
        lcd.write_line(1, 'Turn motors off')

    async def run_incline(
            demand_btn_,
            motor_a_, motor_b_, m_a_speed_, m_b_speed_, hold_s_,
            block_period):
        """ run the incline motors under button control """

        state_ = 'S'
        while True:
            lcd.clear()
            lcd.write_line(0, "Waiting...")
            await demand_btn_.press_ev.wait()
            lcd.clear()
            if state_ != 'F':
                lcd.write_line(0, 'Fwd accel ')
                state_ = 'F'
                motor_a_.set_state('F')
                motor_b_.set_state('F')
                lcd.write_line(1,
                               f'A: {m_a_speed_['F']:02d}% B: {m_b_speed_['F']:02d}%')
                await asyncio.gather(
                    motor_a_.accel_pc(m_a_speed_['F']),
                    motor_b_.accel_pc(m_b_speed_['F']))
                lcd.write_line(0, 'Fwd hold  ')
                await asyncio.sleep(hold_s_)
                lcd.write_line(0, 'Fwd decel ')
                lcd.write_line(1, f'A: {0:02d}% B: {0:02d}%')
                await asyncio.gather(
                    motor_a_.accel_pc(0),
                    motor_b_.accel_pc(0))
                lcd.write_line(0, 'Fwd stop  ')

            else:
                lcd.write_line(0, 'Rev accel ')
                state_ = 'R'
                motor_a_.set_state('R')
                motor_b_.set_state('R')
                lcd.write_line(1,
                               f'A: {m_a_speed_['R']:02d}% B: {m_b_speed_['R']:02d}%')
                await asyncio.gather(
                    motor_a_.accel_pc(m_a_speed_['R']),
                    motor_b_.accel_pc(m_b_speed_['R']))
                lcd.write_line(0, 'Rev hold  ')
                await asyncio.sleep(hold_s_)
                lcd.write_line(0, 'Rev decel ')
                lcd.write_line(1, f'A: {0:02d}% B: {0:02d}%')
                await asyncio.gather(
                    motor_a_.accel_pc(0),
                    motor_b_.accel_pc(0))
                lcd.write_line(0, 'Rev stop  ')

            # not strictly required but set state 'S'
            motor_a.stop()
            motor_b.stop()
            # block button response
            await asyncio.sleep(block_period)
            demand_btn_.press_ev.clear()  # clear any intervening press

    # === user parameters
    # dictionary can be saved as JSON file

    params = {
        'pwm_pins': (22, 17),
        'bridge_pins': (21, 20, 19, 18),
        'run_btn': 20,
        'kill_btn': 22,
        'pulse_f': 10_000,
        'motor_start_pc': 5,
        'motor_a_speed': {'F': 50, 'R': 50},
        'motor_b_speed': {'F': 70, 'R': 50},
        'motor_hold_period': 5
    }

    params = {
        'i2c_pins': {'sda': 0, 'scl': 1},
        'cols_rows': {'cols': 16, 'rows': 2},
        'buttons': {'run': 6, 'kill': 7},
        'pulse_f': 10_000,
        'motor_start_pc': 25,
        'motor_a_speed': {'F': 90, 'R': 50},
        'motor_b_speed': {'F': 50, 'R': 90},
        'motor_hold_period': 5
    }

    lcd = LcdApi(params['i2c_pins'])
    if lcd.lcd_mode:
        print(f'LCD 1602 I2C address: {lcd.I2C_ADDR}')
        lcd.write_line(0, f'FT IC V1.1')
        lcd.write_line(1, f'I2C addr: {lcd.I2C_ADDR}')
    else:
        print('LCD Dispaly not found')
    await asyncio.sleep_ms(1_000)

    board = L298N(params['pwm_pins'], params['bridge_pins'], params['pulse_f'],
                       start_pc=params['motor_start_pc'])
    a_speeds = {'F': pc_u16(params['motor_a_speed']['F']),
                'R': pc_u16(params['motor_a_speed']['R'])
                }
    b_speeds = {'F': pc_u16(params['motor_b_speed']['F']),
                'R': pc_u16(params['motor_b_speed']['R'])
                }
    
    controller = MotorCtrl(board, a_speeds, b_speeds)

    ctrl_buttons = InputButtons(params['buttons'])
    asyncio.create_task(ctrl_buttons.poll_buttons())  # buttons self-poll

    asyncio.create_task(run_incline(ctrl_buttons.run_btn,
                                    motor_a, motor_b,
                                    params['A_speed'], params['B_speed'],
                                    params['hold_s'], 5))
    await monitor_kill_btn(ctrl_buttons.kill_btn, controller)

    # kill button has been pressed; wait for motors to stop
    time.sleep_ms(5000)
    lcd.clear()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('execution complete')
