""" UML State Machine framework """


class StateMachine:
    """ State Machine (SM) """

    def __init__(self, states, events):
        self.states = states
        self.events = events


class State:
    """ SM State """

    def __init__(self, name):
        self.name = name
        self.transitions = {'A1': self.a1, 'B1': self.b1, 'C1: self.c1'}
        self.enter()

    def enter(self):
        """ action on state entry """
        print(f'Enter state {self.name}')

    def exit(self):
        """ action on state exit """
        print(f'Exit state {self.name}')

    async def event_response(self, event_):
        """ respond to a specific Event """
        if event_ in self.transitions:
            await self.transitions[event_]()

    async def a1(self):
        """ respond to event A1 """
        return 'B1'

    async def b1(self):
        """ respond to event B1 """
        return 'C1'

    async def c1(self):
        """ respond to event C1 """
        return 'A1'


async def main():
    states = {'run', 'auto', 'cal'}
    events = {'A1', 'B1', 'C1'}
    state_machine = StateMachine(states, events)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('execution complete')
