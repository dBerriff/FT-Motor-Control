# buttons.py

import asyncio
from machine import Pin, Signal
from micropython import const
from time import ticks_ms, ticks_diff


class Button:
    """
        button with click state - no debounce
        self._hw_in = Signal(
            pin, Pin.IN, Pin.PULL_UP, invert=True)
    """
    WAIT = const(0)
    CLICK = const(1)
    HOLD = const(2)
    POLL_INTERVAL = const(20)  # ms

    def __init__(self, pin, name=''):
        # Signal wraps pull-up logic with invert
        self._hw_in = Signal(pin, Pin.IN, Pin.PULL_UP, invert=True)
        if name:
            self.name = name
        else:
            self.name = str(pin)
        self.state = self.WAIT
        self.prev_state = self.WAIT
        self.active_states = (self.CLICK,)
        self.press_ev = asyncio.Event()
        self.press_ev.clear()

    def get_state(self):
        """ check for button click state """
        pin_state = self._hw_in.value()
        if pin_state != self.prev_state:
            self.prev_state = pin_state
            if not pin_state:
                return self.CLICK
        return self.WAIT

    async def poll_state(self):
        """ poll self for press event
            - button state must be cleared by event handler
        """
        while True:
            self.state = self.get_state()
            if self.state in self.active_states:
                self.press_ev.set()
            await asyncio.sleep_ms(self.POLL_INTERVAL)

    def clear_state(self):
        """ set state to 0 """
        self.state = self.WAIT
        self.press_ev.clear()


class HoldButton(Button):
    """ add hold state """

    T_HOLD = const(750)  # ms - adjust as required

    def __init__(self, pin, name=''):
        super().__init__(pin, name)
        self.active_states = (self.CLICK, self.HOLD)
        self.on_time = 0

    def get_state(self):
        """ check for button click or hold state """
        pin_state = self._hw_in.value()
        if pin_state != self.prev_state:
            self.prev_state = pin_state
            time_stamp = ticks_ms()
            if pin_state:
                # pressed, start timer
                self.on_time = time_stamp
            else:
                # released, determine action
                if ticks_diff(time_stamp, self.on_time) < self.T_HOLD:
                    return self.CLICK
                else:
                    return self.HOLD
        return self.WAIT


class ButtonGroup:
    """ 
        buttons working as a group
        - buttons must be named by string
        - hold button name must start with 'H'
    """

    def __init__(self, pins, names):
        self.buttons = {}
        for pin in pins:
            name = names[pin]
            if name.startswith("H"):
                self.buttons[name] = HoldButton(pin, name)
            else:
                self.buttons[name] = Button(pin, name)
        self.button_pressed = ""
        self.button_state = 0
        self.button_group_ev = asyncio.Event()

    async def poll_group(self):
        """ poll buttons for press"""
        pass


async def main():
    """ coro: test Button and HoldButton classes """

    # Plasma 2040 buttons
    buttons = {
        'A': Button(20, 'A'),
        'B': HoldButton(21, 'B'),
        'U': HoldButton(22, 'C')
    }

    async def keep_alive(period=600):
        """ coro: keep scheduler running """
        t = 0
        while t < period:
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

    await keep_alive(60)  # run scheduler until keep_alive() times out


if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('execution complete')
