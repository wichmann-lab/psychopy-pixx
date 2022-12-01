import time


class ResponsePixx:
    NAME_BY_INCODE = {65534: 'red', 65533: 'yellow', 65531: 'green', 65527: 'blue', 65519: 'white'}
    OUTCODE_BY_NAME = {'red': 0x10000, 'yellow': 0x20000, 'green': 0x40000, 'blue': 0x80000, 'white': 0x100000}
    INCODE_BY_NAME = {l: c for c, l in NAME_BY_INCODE.items()}
    BUTTON_NAMES = list(NAME_BY_INCODE.values())
    BUTTON_CODES = list(NAME_BY_INCODE.keys())
    
    def __init__(self, device, buttons=BUTTON_NAMES, events=['up', 'down'], lights=True):
        self._log = None
        self._starttime = None
        self._old_state = None
        self.watch_buttons = buttons
        self.watch_events = events
        self._pixxdevice = device
        
        self._pixxdevice.din.setBitDirection(0x1F0000)  # enable output pins for lights
        if lights is True:
            self.button_lights = buttons
            self.light_intensity = 1
        elif isinstance(lights, (tuple, list)):
            self.button_lights = lights
            self.light_intensity = 1
        elif isinstance(lights, float):
            self.button_lights = buttons
            self.light_intensity = lights
        else:
            self.button_lights = []
        self._pixxdevice.updateRegisterCache()


    def _buttons_from_output_bits(self, bitmask) -> list:
        buttons = []
        for name, code in ResponsePixx.OUTCODE_BY_NAME.items():
            if ~(bitmask & code):
                buttons.append(name)
        return buttons
    
    def _state_from_input_bits(self, bitmask) -> dict:
        state = {}
        for name, code in ResponsePixx.INCODE_BY_NAME.items():
            if ~(bitmask | code) & 65535:
                state[name] = 'down'
            else:
                state[name] = 'up'
        return state

    @property
    def button_state(self) -> dict:
        self._pixxdevice.updateRegisterCache()
        bitmask = self._pixxdevice.din.getValue()
        return self._state_from_input_bits(bitmask)

    @property
    def button_lights(self) -> list:
        self._pixxdevice.updateRegisterCache()
        bitmask = self._pixxdevice.din.getOutputValue()
        return self._buttons_from_output_bits(bitmask)

    @button_lights.setter
    def button_lights(self, button_names: list):
        if set(button_names) == set(self.button_lights):
            return
        
        bitmask = 0
        for name in button_names:
            bitmask = bitmask | ResponsePixx.OUTCODE_BY_NAME[name]
        self._pixxdevice.din.setOutputValue(str(bitmask))
        self._pixxdevice.updateRegisterCache()

    @property
    def light_intensity(self) -> float:
        self._pixxdevice.updateRegisterCache()
        return self._pixxdevice.din.getOutputStrength()

    @light_intensity.setter
    def light_intensity(self, value: float):
        if self.light_intensity == value:
            return
        
        self._pixxdevice.din.setOutputStrength(value)
        self._pixxdevice.updateRegisterCache()

    def start(self):
        # log voltage changes and thus button push and release
        self._log = self._pixxdevice.din.setDinLog(12e6, 1000)
        self._starttime = self._pixxdevice.getTime()
        self._old_state = self.button_state
        self._pixxdevice.din.startDinLog()
        self._pixxdevice.din.setDebounce(True)  # smooth responses for 30ms to avoid noise
        self._pixxdevice.updateRegisterCache()

    def getKeys(self):
        if self._starttime is None:
            raise RuntimeError("Event watching not started. Call .start() first!")

        self._pixxdevice.din.getDinLogStatus(self._log)
        self._pixxdevice.updateRegisterCache()
        num_events = self._log["newLogFrames"]

        events = []
        if num_events > 0:
            dpixx_events = self._pixxdevice.din.readDinLog(self._log, num_events)

            for dpixx_event in dpixx_events:
                event_time, bitmask = dpixx_event
                new_state = self._state_from_input_bits(bitmask)
                dtime = round(event_time - self._starttime, 2)

                events += [{'name': name, 'state': state, 'time': dtime}
                           for name, state in new_state.items()
                           if name in self.watch_buttons
                           and state in self.watch_events
                           and state != self._old_state[name]]
            self._old_state = new_state
        return events

    def waitKeys(self, maxWait=float('inf'), clear=True):
        if clear:
            self.clearEvents()

        starttime = time.time()
        while (time.time() - starttime) < maxWait:
            events = self.getKeys()
            if events:
                return events
            time.sleep(0.00001)
        return None

    def clearEvents(self):
        if self._starttime is None:
            raise RuntimeError("Event watching not started. Call .start() first!")
        self._pixxdevice.din.readDinLog(self._log)

    def stop(self):
        if self._starttime is None:
            raise RuntimeError("Event watching not started. Call .start() first!")
        self._pixxdevice.din.stopDinLog()
        self._pixxdevice.updateRegisterCache()
        self._log = None
        self._starttime = None
        self._old_state = None


if __name__ == '__main__':
    from pypixxlib.viewpixx import VIEWPixx

    device = ResponsePixx(VIEWPixx(), buttons=['red', 'green'], events=['down'], lights=True)
    device.start()
    keys = device.waitKeys()
    device.stop()
    print(keys)

