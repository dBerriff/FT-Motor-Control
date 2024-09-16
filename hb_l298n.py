# hb_l298n.py
""" drive a L298N motor board
    - developed using MicroPython v1.22.0
    - for Famous Trains Derby by David Jones
    - shared with MERG by David Jones member 9042
"""

from machine import Pin, PWM
from collections import namedtuple


class L298nChannel:
    """ L298N H-bridge channel
        - states: 'S': stopped, 'F': forward, 'R': reverse, 'H': halt
        -- 'H' for possible future use
        - frequency and duty cycle: no range checking
        - RP2040 processor: 2 PWM "slice" channels share a common frequency
        -- slices are pins (0 and 1), (2 and 3), ...
    """

    # for pins (IN1, IN2) or (IN3, IN4)
    STATES = {'S': (1, 1), 'F': (1, 0), 'R': (0, 1), 'H': (0, 0)}

    def __init__(self, en_pin, h_pins_, frequency):
        self.enable = PWM(Pin(en_pin), freq=frequency, duty_u16=0)
        self.sw_0 = Pin(h_pins_[0], Pin.OUT)
        self.sw_1 = Pin(h_pins_[1], Pin.OUT)
        self.set_state('S')
        self.dc_u16 = 0

    def set_freq(self, frequency):
        """ set pulse frequency """
        self.enable.freq(frequency)

    def set_dc_u16(self, dc_u16):
        """ set duty cycle by 16-bit unsigned integer """
        self.dc_u16 = dc_u16
        self.enable.duty_u16(dc_u16)

    def set_state(self, state):
        """ set H-bridge switch states """
        self.sw_0.value(self.STATES[state][0])
        self.sw_1.value(self.STATES[state][1])

    def set_logic_off(self):
        """ set channel inputs off (0) """
        self.set_dc_u16(0)
        self.sw_0.value(0)
        self.sw_1.value(0)

    def stop(self):
        """ set state to 'S'; halt the motor """
        self.set_state('S')
        self.set_dc_u16(0)


class L298N:
    """ control a generic L298N H-bridge board
        - 2 channels labelled A and B
        - EN inputs (PWM) labelled: ENA and ENB
        - bridge-logic inputs labelled: IN1, IN2, IN3, IN4
    """

    STATES = L298nChannel.STATES
    STATES_SET = set(STATES.keys())
    L298Pins = namedtuple('L298Pins', ('enA', 'in1', 'in2', 'in3', 'in4', 'enB'))

    def __init__(self, pins_, f):

        # channel A: PWM input to ENA; bridge-switching inputs to IN1 and IN2
        self.channel_a = L298nChannel(
            pins_.enA, (pins_.in1, pins_.in2), f)
        # channel B: PWM input to ENB; bridge-switching inputs to IN3 and IN4
        self.channel_b = L298nChannel(
            pins_.enB, (pins_.in3, pins_.in4), f)

    def set_logic_off(self):
        """ set all control inputs off (0) """
        self.channel_a.set_logic_off()
        self.channel_b.set_logic_off()
