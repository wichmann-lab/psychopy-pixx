from psychopy.hardware import findPhotometer as psychopy_findPhotometer
from psychopy import hardware

from ._s470_photometer import S470


def getAllPhotometers():
    """Mock psychopy's getAllPhotometers function to
    add out S470 photometer.
    """
    from psychopy.hardware import pr, minolta, crs
    photometers = [pr.PR650, pr.PR655, minolta.LS100, S470]
    if hasattr(crs, "ColorCAL"):
        photometers.append(crs.ColorCAL)

    return photometers


def findPhotometer(ports=None, device=None):
    psychopy_getAllPhotometers = hardware.getAllPhotometers
    try:
        hardware.getAllPhotometers = getAllPhotometers
        photometer = psychopy_findPhotometer(ports, device)
    finally: 
        hardware.getAllPhotometers = psychopy_getAllPhotometers
        
    return photometer
