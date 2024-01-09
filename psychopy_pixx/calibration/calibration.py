import time 

import numpy as np
import click
import matplotlib.pyplot as plt
import csv
import os
from datetime import datetime
import pandas as pd

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
    inverted=False,
    stimSize=4,
    n_measures=50,
    all_measurements=False,
    savefiles='no_savefile_f99fc889-c6e3-4588-ad44-4f8a9554f7b5'):
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
    
    date_time = datetime.now().strftime("%Y-%m-%d_%H-%M") # save date and time for file distinction

    if autoMode != 'semi':
        message.setText('Q to quit at any time')
    else: 
        message.setText('Spacebar for next patch')

    # LS100 likes to take at least one bright measurement
    if photometer.type == 'LS100':
        junk = photometer.getLum()
    if photometer.type == 'S470' and n_measures is not None:
        photometer.n_repeat = n_measures

    if random and inverted:
        print(f'ERROR: you can not set both random={random} and inverted={inverted}!')
        return 1
    if random and not inverted:
        shuffled_index = np.random.permutation(len(levels))
        toTest = levels[shuffled_index]
    elif not random and inverted:
        toTest = levels[::-1] 
    else:
        toTest = levels

    if allGuns:
        guns = [0, 1, 2, 3]  # gun=0 is the white luminance measure
    else:
        guns = [0]
    # this will hold the measured luminance values
    lumsList = np.zeros((4, len(toTest)))

    # create list for logging all measurments
    if all_measurements:
        allLums_data = []

    # prepare logging
    if all_measurements and savefiles!='no_savefile_f99fc889-c6e3-4588-ad44-4f8a9554f7b5':

        data_file = f"{savefiles}/allMeasurments{date_time}.csv"
        writer = csv.writer(open(data_file, 'w'))
        # create header
        header = ['levels']
        for i in range(1, n_measures + 1):
            header.append(f'measurement_{i:03}')
        writer.writerow(header)

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
                if all_measurements:
                    actualLum, lums = photometer.getLum(return_all=True)
                    allLums_data.append([DACval] + lums)
                else:
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

            if all_measurements and savefiles!='no_savefile_f99fc889-c6e3-4588-ad44-4f8a9554f7b5':
                writer.writerow(allLums_data[-1])

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
@click.option('--inverted', help='Measure in inverted order.', is_flag=True)
@click.option('--levelspost', help='Number of measurements after linearization', default=100)
@click.option('--restests', help='Number of test points for luminance resolution', default=5)
@click.option('--plot', is_flag=False, flag_value='.', help='Create, show and save plots.', default='no_plots_8e26a619-e688-4dcf-b010-7bd5fca459d8')
@click.option('--gamma', help='Gamma with which the monitor is to be corrected. (default: 1.0 (linearization))', type=float, default=1.0)
@click.option('--measures', help='Number of measurements to average per color level (only S470 photometer).', type=int, default=250)
@click.option('--savefiles', is_flag=False, flag_value='.', help='save measurements as files, not only in psychopys monitor', default='no_savefile_f99fc889-c6e3-4588-ad44-4f8a9554f7b5')
@click.option('--all_measurements', help='with this option, all measurments from the photometer are saved', is_flag=True)
@click.option('--script', help='prevents calibration from opening plots and user prompts to be able to use the tool more automated (for pre calibration)', is_flag=True)
@click.option('--no_scanning', help='with this option you swith from "scanning backlight" to "normal backlight"', is_flag=True)
@click.option('--lut', help='look up table (lut) the script should use for correction/calibration', is_flag=False, flag_value='.', default='no_lut_f99fc889-c6e3-4588-ad44-4f8a9554f7b5')
def calibration_routine_cli(levels, monitor, screen, photometer, port, random, inverted, levelspost, restests, plot, measures, gamma=1.0, 
savefiles='no_savefile_f99fc889-c6e3-4588-ad44-4f8a9554f7b5', all_measurements=False, script=False, no_scanning=False, lut='no_lut_f99fc889-c6e3-4588-ad44-4f8a9554f7b5'):
    
    from psychopy import monitors, visual  # lazy import

    # check if paths exist
    # Note: I have to use the string with the uuid as control, so if the option is not set, I dont log/plot
    if savefiles!='no_savefile_f99fc889-c6e3-4588-ad44-4f8a9554f7b5':
        if not os.path.isdir(savefiles):
            print(f'ERROR: "{savefiles}" is no valide directory')
            return 1
    if plot!='no_plots_8e26a619-e688-4dcf-b010-7bd5fca459d8':
        if not os.path.isdir(savefiles):
            print(f'ERROR: "{plot}" is no valide directory')
            return 1

    print(f"Setup monitor {monitor}, search for photometer {photometer} ...")
    monitor = monitors.Monitor(monitor)
    photometer = findPhotometer(device=photometer, ports=port)
    if photometer is None:
        raise ValueError('Photometer not found. You might specify (another) port or name.')
    
    # monitor setup
    monitor_size = monitor.getSizePix()
    if monitor_size is None:
        raise ValueError("No monitor size defined. Please setup monitor in psychopy's monitor center.")
    window = visual.Window(
        fullscr=0, size=monitor_size, gamma=1, units='norm', useFBO=True,
        monitor=monitor, allowGUI=True, winType='pyglet', screen=screen)
    vpixx = ViewPixx(window)
    vpixx.scanning_backlight = not no_scanning
    
    if not script:
        monitor_state = {
            'Width': monitor.getWidth(), 
            'Distance': monitor.getDistance(),
            'SizePix': monitor_size,
            **vpixx.register}
        register_str = "\n".join(f"\t{key}: {val}" for key, val in monitor_state.items())
        click.confirm(f'This is your monitor state. Ok?\n{register_str}\n' , abort=True)

    measure_kwargs = dict(window=window, photometer=photometer, random=random, inverted=inverted,
                          allGuns=False, n_measures=measures)
    print(f"Measure a few black and white screens ...")
    blackwhiteLums = measure_luminances(np.array([1, 1, 1 , 0, 0, 0]), **measure_kwargs)[0]
    minLum, maxLum = blackwhiteLums[3], blackwhiteLums[0]
    if (blackwhiteLums[:3].max() - blackwhiteLums[:3].min() > 0.1
        or blackwhiteLums[3:].max() - blackwhiteLums[3:].min() > 0.1):
        raise ValueError(f"Black / white measurements are quite differerent."
                         f"Probably something is wrong.  {blackwhiteLums}")
    if savefiles!='no_savefile_f99fc889-c6e3-4588-ad44-4f8a9554f7b5':
            data = np.vstack((100*np.array([1, 1, 1 , 0, 0, 0]), blackwhiteLums)).T
            date_time = datetime.now().strftime("%Y-%m-%d_%H-%M")        # save date and time for file distinction
            data_file = f"{savefiles}/blackwhiteLums_{date_time}.csv"
            np.savetxt(data_file, data, fmt="%.2f", delimiter=",", header='levels,luminance_gun1,luminance_gun2,luminance_gun3,luminance_gun4') # luminances in cd/m2"
    if not script:
        click.confirm(f'Your monitor shows {minLum:.2f} cd/m^2 to {maxLum:.2f} cd/m^2. Ok?', abort=True)
    
    # measurements
    print(f"Measure luminance series ...")
    levelsPre = np.linspace(0, 1, levels, endpoint=True)
    measure_kwargs_realMeasurment = dict(window=window, photometer=photometer, random=random, inverted=inverted,
                          allGuns=False, n_measures=measures, all_measurements=all_measurements, savefiles=savefiles)
    lumsPre = measure_luminances(levelsPre, **measure_kwargs_realMeasurment)
    if savefiles!='no_savefile_f99fc889-c6e3-4588-ad44-4f8a9554f7b5':
        data = np.vstack((100*levelsPre, lumsPre)).T   # percent for better accuracy, all 4 post guns
        date_time = datetime.now().strftime("%Y-%m-%d_%H-%M")        # save date and time for file distinction
        data_file = f"{savefiles}/luminancePre_{date_time}.csv"
        np.savetxt(data_file, data, fmt="%.2f", delimiter=",", header='levels,luminance_gun1,luminance_gun2,luminance_gun3,luminance_gun4') # luminances in cd/m2"

    #try to set pretrained lut
    if lut != 'no_lut_f99fc889-c6e3-4588-ad44-4f8a9554f7b5':
        lut = pd.read_csv(lut)
        lut = lut.sort_values(by='levels')
        print(lut)
        levelsPre = lut['levels'].values
        print(levelsPre)
        lumsPre = np.array([lut['prediciton'].values, lut['prediciton'].values, lut['prediciton'].values, lut['prediciton'].values])
    
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
    
    print(f'Correct luminance (gamma={gamma}) ...')
    vpixx.correct_luminance(gamma)
    
    if levelspost > 0:
        print(f"Measure luminances again for validation ...")
        levelsPost = np.linspace(0, 1, levelspost, endpoint=True)
        lumsPost = measure_luminances(levelsPost, **measure_kwargs_realMeasurment)
        monitor.setLumsPost(lumsPost)
        monitor.setLevelsPost(levelsPost)

    if restests > 0:
        print("Measure small grey level differences to test luminance resolution ...")
        reslevels = np.linspace(0, 1, restests, endpoint=False)
        resoffset = np.r_[np.inf, np.arange(14, 6 - 1, -1).astype(float)]
        reslevels = reslevels.reshape(-1, 1) + 2**-resoffset.reshape(1, -1)
        reslums = measure_luminances(reslevels.ravel(), **measure_kwargs_realMeasurment)
        reslums = reslums.reshape(4, reslevels.shape[0], reslevels.shape[1]).transpose(1, 0, 2)
        monitor.currentCalib['lumsRes'] = reslums
        monitor.currentCalib['levelsRes'] = reslevels
        monitor.currentCalib['offsetRes'] = resoffset 
        
    print("Save new monitor calibration ...")
    monitor.save()
    window.close()
    if savefiles!='no_savefile_f99fc889-c6e3-4588-ad44-4f8a9554f7b5' and levelspost > 0:
        data = np.vstack((100*levelsPost, lumsPost)).T    # percent for better accuracy, all 4 post guns
        date_time = datetime.now().strftime("%Y-%m-%d_%H-%M")        # save date and time for file distinction
        data_file = f"{savefiles}/luminancePost_{date_time}.csv"
        np.savetxt(data_file, data, fmt="%.2f", delimiter=",", header='levels,luminance_gun1,luminance_gun2,luminance_gun3,luminance_gun4') # luminances in cd/m2"
    
    if plot != 'no_plots_8e26a619-e688-4dcf-b010-7bd5fca459d8':
        print("Plot measurements ...")
        plt.plot(levelsPre, lumsPre[0], label='pre')
        if levelspost > 0:
            plt.plot([0, 1], [lumsPre[0, 0], lumsPre[0, -1]], '--', linewidth=3, label='expected')
            plt.plot(levelsPost, lumsPost[0], label='post')
        plt.xlabel("Grey Level")
        plt.ylabel("Luminance [cd/m^2]")
        plt.legend(loc='best')
        plt.title(f'Luminance before and after calibration ({photometer.type}, {monitor.currentCalibName})')
        plot_file = f"{plot}/{monitor.currentCalibName}_luminance.pdf"
        print(f"Save plot {plot_file}...")
        plt.savefig(plot_file)   
        if not script: 
            plt.show()
    
    if restests > 0:
        for lums, levels in zip(monitor.currentCalib['lumsRes'], monitor.currentCalib['levelsRes']):
            lums = lums[0]
            plt.plot(-resoffset[1:], lums[1:] - lums[0], 
                     label=f'{levels[0]:.4f}')
        if plot != 'no_plots_8e26a619-e688-4dcf-b010-7bd5fca459d8':
            plt.xlabel("Log2(grey level difference)")
            plt.ylabel("Luminance difference")
            plt.yscale('log', base=2)
            plt.title(f'Luminance resolution ({photometer.type}, {monitor.currentCalibName})')
            plt.legend(loc='best', title='Grey level')
            plot_file = f"{plot}/{monitor.currentCalibName}_resolution.pdf"
            print(f"Save plot {plot_file}...")
            plt.savefig(plot_file)
            if not script:
                plt.show()

    
    print("Done.")
