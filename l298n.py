# l298n.py
""" model L298N motor controller
    - developed for Famous Trains Derby by David Jones
    - shared with MERG by member 9042
"""

from machine import Pin, PWM


class L298nChannel:
    """ L298N H-bridge channel
        - states: 'S': stopped, 'F': forward, 'R': reverse (, 'H': halt)
        - frequency and duty cycle: no range checking
        - RP2040 processor: 2 PWM "slice" channels share a common frequency
        -- slices are pins (0 and 1), (2 and 3), ...
    """

    # for (IN1, IN2) or (IN3, IN4)
    STATES = {'S': (1, 1), 'F': (1, 0), 'R': (0, 1), 'H': (0, 0)}

    def __init__(self, pwm_pin, motor_pins_, frequency):
        self.enable = PWM(Pin(pwm_pin))  # L298N pins are labelled 'EN'
        self.sw_1 = Pin(motor_pins_[0], Pin.OUT)
        self.sw_2 = Pin(motor_pins_[1], Pin.OUT)
        self.set_freq(frequency)
        self.set_dc_u16(0)

    def set_freq(self, frequency):
        """ set pulse frequency """
        self.enable.freq(frequency)

    def set_dc_u16(self, dc_u16):
        """ set duty cycle by 16-bit integer """
        self.enable.duty_u16(dc_u16)

    def set_state(self, state):
        """ set H-bridge switch states """
        if state in self.STATES:
            sw_in = self.STATES[state]
            print(f'Setting states: {self.sw_1} {self.sw_2} {sw_in}')
            self.sw_1.value(sw_in[0])
            self.sw_2.value(sw_in[1])

    def set_logic_off(self):
        """ set all logic output off """
        self.set_dc_u16(0)
        self.sw_1.value(0)
        self.sw_2.value(0)


class L298N:
    """ control a generic L298N H-bridge board
        - 2 channels labelled A and B
        - EN inputs (PWM) are labelled: ENA and ENB
        - bridge-switch setting inputs are labelled (IN1, IN2) and (IN3, IN4)
        - connections: Pico GPIO => L298N
        -- pwm_pins => (ENA, ENB)
        -- sw_pins  => (IN1, IN2, IN3, IN4)
    """

    def __init__(self, pwm_pins_, sw_pins_, f):

        # channel A: PWM input to ENA; bridge-switching inputs to IN1 and IN2
        self.channel_a = L298nChannel(
            pwm_pins_[0], (sw_pins_[0], sw_pins_[1]), f)

        # channel B: PWM input to ENB; bridge-switching inputs to IN3 and IN4
        self.channel_b = L298nChannel(
            pwm_pins_[1], (sw_pins_[2], sw_pins_[3]), f)

        print(f'L298N initialised: {pwm_pins_}; {sw_pins_}; {self.channel_a.enable.freq()}')
