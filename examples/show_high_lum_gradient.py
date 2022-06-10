#!/usr/bin/env python
""" Example that visually demonstrates the high-luminance resolution by a smooth grey gradient.  """
def highlum_gradient_test(win):    
    gradient = np.linspace(-1, 1, 2**16).reshape(4, -1)
    #gradient = np.repeat(gradient, gradient.shape[1] / gradient.shape[0], axis=0)
    return visual.GratingStim(win, tex=gradient, units='norm', size=2)
    
    
if __name__ == '__main__':
    from psychopy import visual, core, monitors  # import some libraries from PsychoPy
    import numpy as np
    
    from psychopy_pixx.devices import ViewPixx

    screen = 1
    mon = monitors.Monitor('ViewPixx')
    mywin = visual.Window(size=mon.getSizePix(), monitor=mon, units="deg", useFBO=True, 
                          screen=screen, fullscr=False, gamma=1)
    vpixx = ViewPixx(mywin)

    print("Showing gradient with 8-bit luminance (steps should be visible) ...")
    vpixx.mode = 'C24'
    highlum_gradient_test(mywin).draw()
    mywin.update()
    core.wait(10.0)

    print("Showing gradient with 16-bit luminance (should be smooth) ...")
    vpixx.mode = 'M16'
    highlum_gradient_test(mywin).draw()
    mywin.update()
    core.wait(10.0)
