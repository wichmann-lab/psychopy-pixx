
from psychopy.monitors import MonitorCenter
from psychopy.localization import _translate

import wx


class MainFrame(MonitorCenter.MainFrame):
    """ Subclass of the psychopy monitor center for customization.

    This custom monitor center overrides the default monitor center once our plugin is loaded in the psychopy builder via the entry point in pyproject.toml.

    Override what needed from:
    https://github.com/psychopy/psychopy/blob/dev/psychopy/monitors/MonitorCenter.py
    """
    def updateCalibList(self, thisList=None):
        """ Overrides updateCalibList from MonitorCenter.py to show additional ViewPixx info."""
        if thisList is None:  # fetch it from monitor file
            thisList = self.currentMon.calibNames
        newList = []
        for name in thisList:
            calib = self.currentMon.calibs[name]
            if 'viewpixx' in calib:
                # ...show some info about the calib
                mode = calib["viewpixx"]['register']['VideoMode']
                newList.append(f'{name} ({mode})')
            else:
                newList.append(f'{name} (no viewpixx info)')
        super().updateCalibList(thisList=newList)


    def makeAdminBox(self, parent):
        adminBox = super().makeAdminBox(parent)
        #  TODO: Customize the list of calibrations
        return adminBox
