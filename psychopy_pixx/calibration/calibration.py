import time 

import numpy as np
import click
import matplotlib.pyplot as plt

from psychopy_pixx.calibration.photometer import findPhotometer
from psychopy_pixx.devices import ViewPixx

def measure_luminances(
    levels,
    window, 
    photometer,
    gamma=1.0,
    allGuns=True,
    autoMode='auto',
    random=False,
    stimSize=4,
    n_measures=50):
    """Automatically measures a series of gun values and measures
    the luminance with a photometer.
    
    This function is based on psychopy's getLumSeries function.
    
    :Parameters:
        photometer : a photometer object
            e.g. a :class:`~        print(np.mean(lums), np.median(lums), lums)
psychopy.hardware.pr.PR65` or
            :class:`~psychopy.hardware.minolta.LS100` from
            hardware.findPhotometer()
        levels : 
            array of values to test
        gamma : (default=1.0) the gamma value at which to test
        autoMode : 'auto' or 'semi'(='auto')
            If 'auto' the program will present the screen
            and automatically take a measurement before moving on.
            If set to 'semi' the program will wait for a keypress before
            moving on but will not attempt to make a measurement (use this
            to make a measurement with your own device).
            Any other value will simply move on without pausing on each
            screen (use this to see that the display is performing as
            expected).
        n_measures : Averaging this number of measurements per level, only for S470 photometer.
    """
    from psychopy import event, visual, core

    if gamma == 1:
        initRGB = 0.5 ** (1 / 2.0) * 2 - 1
    else:
        initRGB = 0.8
    # setup screen and "stimuli"

    
    instructions = ("Point the photometer at the central bar. "
                    "Hit a key when ready (or wait 30s)")
    message = visual.TextStim(window, text=instructions, height=0.1,
                              pos=(0, -0.85), color=[1, -1, -1])
    noise = np.random.rand(512, 512).round() * 2 - 1
    backPatch = visual.PatchStim(window, tex=noise, size=2, units='norm', 
                                 sf=[window.clientSize[0] / 512.0, window.clientSize[1] / 512.0])
    testPatch = visual.PatchStim(window, tex='sqr', size=stimSize,
                                 color=initRGB, units='norm')

    if autoMode != 'semi':
        message.setText('Q to quit at any time')
    else: 
        message.setText('Spacebar for next patch')

    # LS100 likes to take at least one bright measurement
    if photometer.type == 'LS100':
        junk = photometer.getLum()
    if photometer.type == 'S470' and n_measures is not None:
        photometer.n_repeat = n_measures

    if random:
        shuffled_index = np.random.permutation(len(levels))
        toTest = levels[shuffled_index]
    else:
        toTest = levels

    if allGuns:
        guns = [0, 1, 2, 3]  # gun=0 is the white luminance measure
    else:
        guns = [0]
    # this will hold the measured luminance values
    lumsList = np.zeros((4, len(toTest)))
    # for each gun, for each value run test
    for gun in guns:
        for valN, DACval in enumerate(toTest):
            lum = (DACval * 2) - 1  # from range 0:1 into -1:1
            # only do luminanc=-1 once
            if lum == -1 and gun > 0:
                continue
            # set the patch color
            if gun > 0:
                rgb = [-1, -1, -1]
                rgb[gun - 1] = lum
            else:
                rgb = [lum, lum, lum]

            backPatch.draw()
            testPatch.setColor(rgb)
            testPatch.draw()
            message.draw()
            window.flip()

            # allowing the screen to settle (no good reason!)
            time.sleep(0.5)

            # take measurement
            if autoMode == 'auto':
                actualLum = photometer.getLum()
                print(f"\t{valN + 1}/{len(toTest)} At DAC value {DACval:.2f}\t: {actualLum:.2f}cd/m^2")
                lumsList[gun, valN] = actualLum
                # check for quit request
                for thisKey in event.getKeys():
                    if thisKey in ('q', 'Q', 'escape'):
                        window.close()
                        return np.array([])

            elif autoMode == 'semi':
                print(f"\t{valN + 1}/{len(toTest)} At DAC value {DACval:.2f}")

                done = False
                while not done:
                    # check for quit request
                    for thisKey in event.getKeys():
                        if thisKey in ('q', 'Q', 'escape'):
                            return np.array([])
                        elif thisKey in (' ', 'space'):
                            done = True

    if random:  # revert shuffling
        lumsList = lumsList[:, shuffled_index.argsort()]
    return lumsList


@click.command()
@click.option('-l', '--levels', required=True, help='Number of grey levels to measure', type=int)
@click.option('-m', '--monitor', required=True, help='monitor name from psychopy monitor center')
@click.option('-s', '--screen', required=True, help='screen to show window, typically 0 is internal and 1 external', type=int)
@click.option('-p', '--photometer', required=True, help='photometer name supported by psychopy')
@click.option('--port', help='Port of the photometer', default=None)
@click.option('--random', help='Measure in randomized order.', is_flag=True)
@click.option('--levelspost', help='Number of measurements after linearization', default=100)
@click.option('--restests', help='Number of test points for luminance resolution', default=5)
@click.option('--plot', help='Show plots.', is_flag=True)
@click.option('--linearize/--no-linearize', help='Do (not) linearize the luminance. Default is linearizing.', default=True)
@click.option('--measures', help='Number of measurements to average per color level (only S470 photometer).', type=int, default=250)
def calibration_routine_cli(levels, monitor, screen, photometer, port, random, levelspost, restests, plot, linearize, measures):
    from psychopy import monitors, visual  # lazy import

    print(f"Setup monitor {monitor}, search for photometer {photometer} ...")
    monitor = monitors.Monitor(monitor)
    photometer = findPhotometer(device=photometer, ports=port)
    if photometer is None:
        raise ValueError('Photometer not found. You might specify (another) port or name.')
    
    monitor_size = monitor.getSizePix()
    if monitor_size is None:
        raise ValueError("No monitor size defined. Please setup monitor in psychopy's monitor center.")
    window = visual.Window(
        fullscr=0, size=monitor_size, gamma=1, units='norm', useFBO=True,
        monitor=monitor, allowGUI=True, winType='pyglet', screen=screen)
    vpixx = ViewPixx(window)
    
    monitor_state = {
        'Width': monitor.getWidth(), 
        'Distance': monitor.getDistance(),
        'SizePix': monitor_size,
        **vpixx.register}
    register_str = "\n".join(f"\t{key}: {val}" for key, val in monitor_state.items())
    click.confirm(f'This is your monitor state. Ok?\n{register_str}\n' , abort=True)

    measure_kwargs = dict(window=window, photometer=photometer, random=random,
                          allGuns=False, n_measures=measures)
    print(f"Measure a few black and white screens ...")
    blackwhiteLums = measure_luminances(np.array([1, 1, 1 , 0, 0, 0]), **measure_kwargs)[0]
    minLum, maxLum = blackwhiteLums[3], blackwhiteLums[0]
    if (blackwhiteLums[:3].max() - blackwhiteLums[:3].min() > 0.1
        or blackwhiteLums[3:].max() - blackwhiteLums[3:].min() > 0.1):
        raise ValueError(f"Black / white measurements are quite differerent."
                         f"Probably something is wrong.  {blackwhiteLums}")
    click.confirm(f'Your monitor shows {minLum:.2f} cd/m^2 to {maxLum:.2f} cd/m^2. Ok?', abort=True)
    
    print(f"Measure luminance series ...")
    levelsPre = np.linspace(0, 1, levels, endpoint=True)
    lumsPre = measure_luminances(levelsPre, **measure_kwargs)
    
    print("Create new monitor calibration.")
    monitor.newCalib(width=monitor.getWidth(), distance=monitor.getDistance())
    monitor.setSizePix(monitor_size)
    monitor.setLineariseMethod(3)  # interpolation
    monitor.setLumsPre(lumsPre)
    monitor.setLevelsPre(levelsPre)
    monitor.setGamma(1)  # disable psychopy gamma correction
    monitor.currentCalib['viewpixx'] = {
        'name': vpixx._pixxdevice.getName(),
        'info': vpixx._pixxdevice.getInfo(),
        'register': vpixx.register
    }
    monitor.currentCalib['photometer'] = {
        'type': photometer.type,
        'repeat_measures': measures,
        'random_measures': random,
    }
    
    if linearize:
        print("Linearize luminance ...")
        vpixx.linearize_luminance()
    
    if levelspost > 0:
        print(f"Measure luminances again for validation ...")
        levelsPost = np.linspace(0, 1, levelspost, endpoint=True)
        lumsPost = measure_luminances(levelsPost, **measure_kwargs)
        monitor.setLumsPost(lumsPost)
        monitor.setLevelsPost(levelsPost)

    if restests > 0:
        print("Measure small grey level differences to test luminance resolution ...")
        reslevels = np.linspace(0, 1, restests, endpoint=False)
        resoffset = np.r_[np.inf, np.arange(14, 6 - 1, -1).astype(float)]
        reslevels = reslevels.reshape(-1, 1) + 2**-resoffset.reshape(1, -1)
        reslums = measure_luminances(reslevels.ravel(), **measure_kwargs)
        reslums = reslums.reshape(4, reslevels.shape[0], reslevels.shape[1]).transpose(1, 0, 2)
        monitor.currentCalib['lumsRes'] = reslums
        monitor.currentCalib['levelsRes'] = reslevels
        monitor.currentCalib['offsetRes'] = resoffset 
        
    print("Save new monitor calibration ...")
    monitor.save()
    window.close()
    
    print("Plot measurements ...")
    plt.plot(levelsPre, lumsPre[0], label='pre')
    if levelspost > 0:
        plt.plot([0, 1], [lumsPre[0, 0], lumsPre[0, -1]], '--', linewidth=3, label='expected')
        plt.plot(levelsPost, lumsPost[0], label='post')
    plt.xlabel("Grey Level")
    plt.ylabel("Luminance [cd/m^2]")
    plt.legend(loc='best')
    plt.title(f'Luminance before and after calibration ({photometer.type}, {monitor.currentCalibName})')
    plot_file = f"{monitor.currentCalibName}_luminance.pdf"
    print(f"Save plot {plot_file}...")
    plt.savefig(plot_file)   
    if plot: 
        plt.show()  
    
    if restests > 0:
        for lums, levels in zip(monitor.currentCalib['lumsRes'], monitor.currentCalib['levelsRes']):
            lums = lums[0]
            plt.plot(-resoffset[1:], lums[1:] - lums[0], 
                     label=f'{levels[0]:.4f}')
        plt.xlabel("Log2(grey level difference)")
        plt.ylabel("Luminance difference")
        plt.yscale('log', base=2)
        plt.title(f'Luminance resolution ({photometer.type}, {monitor.currentCalibName})')
        plt.legend(loc='best', title='Grey level')
        plot_file = f"{monitor.currentCalibName}_resolution.pdf"
        print(f"Save plot {plot_file}...")
        plt.savefig(plot_file)
        if plot:
            plt.show()  

    
    print("Done.")
