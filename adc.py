import asyncio
from micropython import const
from machine import Pin, I2C, ADC
from lcd_1602 import LcdApi
import json


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
    
    def __init__(self, buttons_):
        self.trigger = None
        self.buttons = buttons_
        # create tasks to test each button
        for b in buttons_:
            asyncio.create_task(buttons_[b].poll_event())  # buttons_ self-poll
            asyncio.create_task(self.process_event(buttons_[b]))  # respond to event

    async def process_event(self, btn):
        """ coro: process system button events """
        while True:
            await btn.press_ev.wait()
            self.buttons[btn.name].state = btn.state
            btn.clear_state()
            print(self.buttons)

    async def st_logic(self, btn_state):
        """ respond to btn_ state """
        self.trigger = btn_state
        print(self.trigger)
        await asyncio.sleep_ms(200)

    async def process_adc_event(self, btn, system_):
        """ coro: process system adc events """
        pass


async def main():

    params = {
        'i2c_pins': (0, 1),
        'cols_rows': {'cols': 16, 'rows': 2}
        }

    lcd_pins = LcdApi.I2CTuple
    pins = params['i2c_pins']
    lcd = LcdApi(lcd_pins(*pins))
    if lcd.lcd_mode:
        lcd.write_line(0, f'ADC Test')
        lcd.write_line(1, f'I2C addr: {lcd.I2C_ADDR}')
    else:
        print('LCD Display not found')
    await asyncio.sleep_ms(1000)


    adc_input_a = Adc(26)
    adc_input_b = Adc(27)

    track = 'A'
    fwd_prev = 0
    rev_prev = 0
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
