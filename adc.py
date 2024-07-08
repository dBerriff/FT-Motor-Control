from micropython import const
from machine import Pin, I2C, ADC
from lcd_1602 import Lcd1602
from buttons import HoldButton
import json

import asyncio


class Adc:
    """ input from potentiometer to ADC """
    pc_factor = const(655)

    def __init__(self, pin):
        self.adc = ADC(Pin(pin))

    def get_pc(self):
        """ return input setting in range 0 - 99 """
        return self.adc.read_u16() // self.pc_factor


class System:
    """ holding class for System """
    
    def __init__(self):
        self.trigger = None

    async def st_logic(self, btn_state):
        """ respond to btn_ state """
        self.trigger = btn_state
        print(self.trigger)
        await asyncio.sleep_ms(20)


async def main():

    def get_params(file_name):
        """ return char pixel indices """
        with open(file_name, 'r') as f:
            retrieved = json.load(f)
        return retrieved

    def save_params(parameters, file_name):
        """ return char pixel indices """
        with open(file_name, 'w') as f:
            json.dump(parameters, f)

    async def process_btn_event(btn, system_):
        """ coro: process system button events """
        while True:
            await btn.press_ev.wait()
            await system_.st_logic(btn.state)
            btn.clear_state()

    async def process_adc_event(btn, system_):
        """ coro: process system adc events """
        pass

    filename = 'parameters.json'
    params = get_params(filename)

    buttons = {
        'A': HoldButton(20, 'A'),
        'B': HoldButton(21, 'B'),
        'C': HoldButton(22, 'C')
        }

    system = System()

    # create tasks to test each button
    for b in buttons:
        asyncio.create_task(buttons[b].poll_state())  # buttons self-poll
        asyncio.create_task(process_btn_event(buttons[b], system))  # respond to event

    columns = 16
    rows = 2
    lcd = Lcd1602(sda=0, scl=1, col=columns, row=rows)

    adc_input_a = Adc(26)
    adc_input_b = Adc(27)

    fwd_prev = params['a_fwd']
    rev_prev = params['b_fwd']
    track = 'A'    
    print(f'System initialised \n{params}')

    lcd.write_line(0, f'{track}')
    while True:
        fwd_pc = adc_input_a.get_pc()
        rev_pc = adc_input_b.get_pc()
        if fwd_pc != fwd_prev or rev_pc != rev_prev:
            lcd.write_line(1, f'F: {fwd_pc:02d}%  R: {rev_pc:02d}%')
            fwd_prev = fwd_pc
            rev_prev = rev_pc
        await asyncio.sleep_ms(200)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('execution complete')
