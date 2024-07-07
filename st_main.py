# st_main.py
""" control dc motors """

import asyncio
import gc
from l298n import L298N
from motor_ctrl import MotorCtrl
from buttons import Button, HoldButton
import lcd_1602


class ControlState:
    """
        control State-Transition logic
        - dict stores: event: transitions
    """

    def __init__(self, lcd_, **kwargs):
        self.lcd = lcd_
        self.state = None
        self.end_fade = True
        self.state_hsv = {}
        self.state_rgb = {}
        if 'lcd_s' in kwargs:
            self.lcd_str_dict = kwargs['lcd_s']
        else:
            self.lcd_str_dict = {}

        # state-transition logic
        # outer key: current state
        # inner key: button event as: '<name><event>'
        # <event>: 1 is click, 2 is hold
        self.transitions = {
            'off': {'A1': self.set_day,
                    'B1': self.set_by_clock,
                    'U1': self.no_t},
            'day': {'A1': self.set_night,
                    'B1': self.no_t,
                    'U1': self.set_off},
            'night': {'A1': self.set_day,
                      'B1': self.no_t,
                      'U1': self.set_off},
            'clock': {'A1': self.no_t,
                      'B1': self.no_t,
                      'B2': self.set_by_clock,
                      'U1': self.set_off
                      }
        }
        self.fade_steps = 1000
        self.fade_pause = 20 * vt.m_interval // self.fade_steps  # over 20 v min
        self.vt.init_clock(
            self.hm_dict['hm'], self.hm_dict['dawn'], self.hm_dict['dusk'])

    # set LED strip display state

    # state-transition methods

    async def set_off(self):
        """ coro: set state 'off' """
        # end possible existing tasks
        self.end_fade = True
        self.vt.change_state_ev.set()
        await asyncio.sleep_ms(self.fade_pause)

        self.vt.change_state_ev.clear()
        await self.write_strip_by_state('off')
        self.lcd.write_line(0, self.lcd_str_dict['state'])
        self.lcd.write_line(1, self.lcd_str_dict['off'])
        self.state = 'off'

    async def set_run(self):
        """ coro: set state 'day' """
        await self.write_strip_by_state('day')
        self.lcd.write_line(0, self.lcd_str_dict['state'])
        self.lcd.write_line(1, self.lcd_str_dict['day'])
        self.state = 'day'

    async def set_calibrate(self):
        """ coro: set state 'night' """
        await self.write_strip_by_state('night')
        self.lcd.write_line(0, self.lcd_str_dict['state'])
        self.lcd.write_line(1, self.lcd_str_dict['night'])
        self.state = 'night'

    async def set_auto(self):
        """ coro: set state 'clock' """
        # end possible existing tasks
        self.end_fade = True
        self.vt.change_state_ev.set()
        await asyncio.sleep_ms(self.fade_pause)

        self.vt.change_state_ev.clear()
        self.vt.init_clock(
            self.hm_dict['hm'], self.hm_dict['dawn'], self.hm_dict['dusk'])
        self.end_fade = False
        asyncio.create_task(self.clock_transitions())
        self.state = 'clock'

    @staticmethod
    async def no_t():
        """ coro: no transition """
        await asyncio.sleep_ms(1)

    # transition methods

    async def state_transition_logic(self, btn_state):
        """ coro: invoke transition for state & button-press event """
        transitions = self.transitions[self.state]
        if btn_state in transitions:
            await transitions[btn_state]()  # invoke transition method

    async def clock_transitions(self):
        """ coro: set output by virtual clock time """

        async def fade(state_0, state_1):
            """ coro: fade transition """

            async def do_fade(state_0_, state_1_):
                """ coro: do the fade """
                steps = self.fade_steps // 2
                h_0, s_0, v_0 = self.state_hsv[state_0_]
                d_h = (self.state_hsv[state_1_][0] - h_0) / steps
                d_s = (self.state_hsv[state_1_][1] - s_0) / steps
                d_v = (self.state_hsv[state_1_][2] - v_0) / steps
                i = 0
                while i < steps:
                    if self.end_fade:
                        break
                    rgb = self.cs.rgb_g(self.cs.hsv_rgb((h_0, s_0, v_0)))
                    self.nps.set_strip_rgb(rgb)
                    self.nps.write()
                    await asyncio.sleep_ms(self.fade_pause)
                    h_0 += d_h
                    s_0 += d_s
                    v_0 += d_v
                    i += 1
                # ensure target state is set
                await self.write_strip_by_state(state_1_)

            # fade in 2 steps via red sunset/sunrise
            print(f'Fade from {state_0}')
            await do_fade(state_0, 'mid')
            await do_fade('mid', state_1)

        # clock_transitions
        day_night = self.vt.state
        await self.write_strip_by_state(day_night)
        # fade rgb between states
        while not self.end_fade:
            await self.vt.change_state_ev.wait()
            self.vt.change_state_ev.clear()
            if self.end_fade:
                break
            if day_night == 'day':
                target_state = 'night'
            else:
                target_state = 'day'
            await fade(day_night, target_state)
            day_night = target_state


async def main():
    """ coro: initialise then run tasks under asyncio scheduler """

    async def holding_task():
        """ coro: run forever """
        while True:
            await asyncio.sleep_ms(1_000)

    async def process_event(btn, system_):
        """ coro: passes button events to the system """
        while True:
            await btn.press_ev.wait()
            await system_.state_transition_logic(btn.state)
            btn.clear_state()

    async def show_time(vt_, lcd_, lcd_s):
        """ coro: print virtual time every 1s in 'clock' state """
        line_len = const(16)
        day_marker = vt_.get_day_marker()
        night_marker = vt_.get_night_marker()
        while True:
            await vt_.minute_ev.wait()
            vt_.minute_ev.clear()
            if system.state == 'clock':
                m = vt_.get_clock_m()
                time_str = vt_.get_time_hm().center(line_len)
                if day_marker <= m < night_marker:
                    p_str = lcd_s['day']
                else:
                    p_str = lcd_s['night']

                lcd_.write_line(0, time_str)
                lcd_.write_line(1, p_str)
                gc.collect()  # garbage collection

    # ====== parameters

    n_pixels = 119 + 119

    # state colours as HSV
    state_hsv = {
        'day': (240.0, 0.1, 0.95),
        'night': (359.0, 0.0, 0.15),
        'mid': (359.0, 1.0, 0.5),
        'off': (0.0, 0.0, 0.0)
    }

    clock_hm = {'hm': '19:30', 'dawn': '06:00', 'dusk': '20:00'}
    clock_speed = 720

    # for 16-char lines
    lcd_strings = {
        'blank': ''.center(16),
        'state': 'State'.center(16),
        'off': 'off'.center(16),
        'day': 'day'.center(16),
        'night': 'night'.center(16),
        'clock': 'clock'.center(16)
    }

    # ====== end-of-parameters

    # instantiate system objects
    cs = ColourSpace()
    board = Plasma2040()
    driver = Ws2812(board.DATA)
    nps = PixelStrip(driver, n_pixels)
    buttons = board.buttons
    lcd = LcdApi(scl=board.LCD_CLK, sda=board.LCD_DATA)
    vt = VTime(t_mpy=clock_speed)  # fast virtual clock
    system = DayNightST(cs, nps, vt, lcd, hsv=state_hsv, hm=clock_hm, lcd_s=lcd_strings)
    # initialise
    board.set_onboard((0, 15, 0))  # on
    await system.set_off()
    print('System initialised')

    # create tasks respond to events
    for b in buttons:
        asyncio.create_task(buttons[b].poll_state())  # buttons self-poll
        asyncio.create_task(process_event(buttons[b], system))  # respond to event
    asyncio.create_task(show_time(system.vt, lcd, lcd_strings))

    await holding_task()

    system.set_off()
    await asyncio.sleep_ms(200)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('execution complete')
