import asyncio
from micropython import const
from machine import Pin, I2C, ADC
from lcd_1602 import LcdApi
from buttons import Button, HoldButton
import json


class Adc:
    """ input from potentiometer to ADC """
    pc_factor = const(655)

    def __init__(self, pin):
        self.adc = ADC(Pin(pin))

    def get_pc(self):
        """ return input setting in range 0 - 99 """
        return self.adc.read_u16() // self.pc_factor


async def main():

    async def keep_alive():
        """ coro: to be awaited """
        t = 0
        while t < 60:
            await asyncio.sleep(1)
            t += 1

    async def process_btn_event(btn):
        """ coro: passes button events to the system """
        while True:
            # wait until press_ev is set
            await btn.press_ev.wait()
            lcd.write_line(0, f'{btn.name}{btn.state}')
            btn.clear_state()

    async def process_adc(adc_a, adc_b):
        """ coro: poll adc inputs """
        fwd_prev = -1
        rev_prev = -1        
        while True:
            fwd_pc = adc_a.get_pc()
            rev_pc = adc_b.get_pc()
            if fwd_pc != fwd_prev or rev_pc != rev_prev:
                lcd.write_line(1, f'F: {fwd_pc:02d}%  R: {rev_pc:02d}%')
                fwd_prev = fwd_pc
                rev_prev = rev_pc
            await asyncio.sleep_ms(200)

    buttons = (Button(6, 'A'),
               HoldButton(7, 'B'),
               HoldButton(8, 'C'),
               HoldButton(9, 'D')
               )

    # create tasks to test each button
    for b in buttons:
        asyncio.create_task(b.poll_state())  # buttons self-poll
        asyncio.create_task(process_btn_event(b))  # respond to event

    params = {
        'i2c_pins': {'sda': 0, 'scl': 1},
        'cols_rows': {'cols': 16, 'rows': 2},
        }

    lcd = LcdApi(params['i2c_pins'])
    if lcd.lcd_mode:
        lcd.write_line(0, f'ADC Test')
        lcd.write_line(1, f'I2C addr: {lcd.I2C_ADDR}')
    else:
        print('LCD Display not found')
    await asyncio.sleep_ms(1000)

    adc_in_a = Adc(26)
    adc_in_b = Adc(27)
    asyncio.create_task(process_adc(adc_in_a, adc_in_b))

    print(f'System initialised \n{params}')

    await keep_alive()  # run scheduler until keep_alive() times out


if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('execution complete')
