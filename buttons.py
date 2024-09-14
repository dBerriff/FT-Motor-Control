# buttons.py
"""
    implement press and hold buttons
    class Button implements a click button
    class HoldButton extends Button to include a hold event
    - button methods are coroutines and include self-polling methods
"""

import asyncio
from machine import Pin, Signal
from micropython import const
from time import ticks_ms, ticks_diff


class Button:
    """ button with click state"""
    # button states
    WAIT = const('0')
    CLICK = const('1')

    POLL_INTERVAL = const(20)  # ms

    def __init__(self, pin, name=''):
        # Signal wraps pull-up logic with invert
        self._hw_in = Signal(
            pin, Pin.IN, Pin.PULL_UP, invert=True)
        if name:
            self.name = name
        else:
            self.name = str(pin)        
        self.press_ev = asyncio.Event()  # starts cleared
        self.state = self.WAIT

    async def poll_state(self):
        """ poll self for click event
            - event is set on button release
            - event handler must call clear_state
        """
        prev_pin_state = self._hw_in.value()
        while True:
            pin_state = self._hw_in.value()
            if pin_state != prev_pin_state:
                if not pin_state:
                    self.state = self.CLICK
                    self.press_ev.set()
                prev_pin_state = pin_state
            await asyncio.sleep_ms(self.POLL_INTERVAL)

    def clear_state(self):
        """ set state to WAIT """
        self.state = self.WAIT
        self.press_ev.clear()


class HoldButton(Button):
    """ button add hold state """
    # additional button state
    HOLD = const('2')
    T_HOLD = const(750)  # ms - adjust as required

    def __init__(self, pin, name=''):
        super().__init__(pin, name)

    async def poll_state(self):
        """ poll self for click or hold events
            - button state must be cleared by event handler
            - elapsed time measured in ms
        """
        on_time = None
        prev_pin_state = self._hw_in.value()
        while True:
            pin_state = self._hw_in.value()
            if pin_state != prev_pin_state:
                time_stamp = ticks_ms()
                if pin_state:
                    on_time = time_stamp
                else:
                    if ticks_diff(time_stamp, on_time) < self.T_HOLD:
                        self.state = self.CLICK
                    else:
                        self.state = self.HOLD
                    self.press_ev.set()
                prev_pin_state = pin_state
            await asyncio.sleep_ms(self.POLL_INTERVAL)

    def __str__(self):
        return f'{self.name} {self.state}'

    def __repr__(self):
        return f'{self.name} {self.state}'


async def main():
    """ coro: test Button and HoldButton classes """

    # Plasma 2040 buttons
    buttons = {
        '1': Button(6, 'A'),
        '2': HoldButton(7, 'B'),
        '3': HoldButton(8, 'C'),
        '4': HoldButton(9, 'D')
    }

    async def keep_alive():
        """ coro: to be awaited """
        t = 0
        while t < 60:
            await asyncio.sleep(1)
            t += 1

    async def process_event(btn):
        """ coro: passes button events to the system """
        while True:
            # wait until press_ev is set
            await btn.press_ev.wait()
            print(btn.name, btn.state)
            btn.clear_state()

    # create tasks to test each button
    for b in buttons:
        asyncio.create_task(buttons[b].poll_state())  # buttons self-poll
        asyncio.create_task(process_event(buttons[b]))  # respond to event
    print('System initialised')

    await keep_alive()  # run scheduler until keep_alive() times out


if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('execution complete')
