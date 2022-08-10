from pathlib import Path

from psychopy.visual import shaders
from psychopy.tools import gltools
from OpenGL import GL
import ctypes
import numpy as np


def load_shader_source(mode):
    src = Path(__file__).parent / 'shaders' / f'{mode.lower()}_frag.glsl'
    return src.read_text()
    

class ViewPixx:
    def __init__(self, win, gamma=None):
        """
        Parameters
        ----------

        win : a PsychoPy :class:`~psychopy.visual.Window` object, required
        mode : 'C24', 'M16', 'C48' video modes

        """
        # import pyglet.GL late so that we can import this without it
        global GL
        import pyglet.gl as GL

        try:
            from pypixxlib.viewpixx import VIEWPixx

            self._pixxdevice = VIEWPixx()
        except ImportError:
            raise ImportError("Cannot import 'pypixxlib', is it installed?\n"
                              "See https://www.vpixx.com/manuals/python/html/gettingStartd.html")
        
        if not win.useFBO:
            raise ValueError(f"Expects window with useFBO=True.")
        self.window = win
        self._shader_progs = {'C24': win._progFBOtoFrame}
        self._clut_texture = None
        self._shader_clut = None
        self._setup_shader()

    
    def linearize_luminance(self, assert_register=True):
        if assert_register:
           try:
               calib_reg = self.window.monitor.currentCalib['viewpixx']['register'] 
           except KeyError:
               raise ValueError("No register data found in calibration file.\n"
                    "This means, the calibration was probably not created with the psychopy-pixx tools.\n"
                    "Hide this error with `assert_register=False`.")
           register = self.register
           for k, v in calib_reg.items():
               assert register[k] == v, f"Expects {k}={v}, got {k}={register[k]}"
                
        self.shader_clut = interp_clut(self.window.monitor)
        
    @property
    def shader_clut(self) -> np.ndarray:
        return self._shader_clut
        
    @shader_clut.setter
    def shader_clut(self, clut: np.ndarray):
        if clut is not None and clut.shape != (4, 2**16):  
            raise ValueError(f"Expects clut.shape == (4, 2**16), got {clut.shape}")
        self._shader_clut = clut
        
        if self._clut_texture is not None:  # delete old texture
            gltools.deleteTexture(self._clut_texture)
            self._clut_texture = None
     
        if clut is not None:  # add new texture
            # swap (LRGB, pixels) to (pixels, RGBA) for texture
            ctype_clut = np.ascontiguousarray(
                clut[[1, 2, 3, 0], :].T.reshape(256, 256, 4), dtype='float32').ctypes
            #GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, 1)
            self._clut_texture = gltools.createTexImage2D(
                256, 256, target=GL.GL_TEXTURE_2D, internalFormat=GL.GL_RGBA32F,
                pixelFormat=GL.GL_RGBA, dataType=GL.GL_FLOAT, data=ctype_clut,
                texParams={ GL.GL_TEXTURE_MIN_FILTER: GL.GL_LINEAR, 
                            GL.GL_TEXTURE_MAG_FILTER: GL.GL_LINEAR, 
                            GL.GL_TEXTURE_WRAP_S: GL.GL_CLAMP_TO_EDGE, 
                            GL.GL_TEXTURE_WRAP_T: GL.GL_CLAMP_TO_EDGE})
        
        self._setup_shader()  # update clut variables in shader
        
        
    def _prepareFBOrender(self):
        prog = self._shader_progs[self.mode]
        GL.glUseProgram(prog)
        if self._clut_texture:
            # gltools.bindTexture sets the active texture incorrectly 
            GL.glActiveTexture(GL.GL_TEXTURE1)
            gltools.bindTexture(self._clut_texture, unit=1, enable=True)
                    
        
    def _finishFBOrender(self):
        if self._clut_texture:
            gltools.unbindTexture(self._clut_texture)
        GL.glUseProgram(0)

    def _afterFBOrender(self):
        pass

    def _setup_shader(self):
        mode = self.mode
 
        if mode not in self._shader_progs:
            try:
                src = load_shader_source(mode)
                prog = shaders.compileProgram(shaders.vertSimple, src)
            except FileNotFoundError:
                raise ValueError(f"Unsupported video mode '{mode}'.")
            self._shader_progs[mode] = prog   
        else: 
            prog = self._shader_progs[mode]

        HIGH_RES_MODES = ('M16', 'C48') 
        if mode in HIGH_RES_MODES:
            if any(gamma != 1 for gamma in self.window.gamma):
                raise ValueError(f"High luminance resolution (mode={self.mode}) is incompatible"
                                 f"with psychopy's default gamma correction.\n"
                                 f"Expects `visual.Window(..., gamma=1)`, got gamma={self.window.gamma}.")   
                                  
            GL.glUseProgram(prog)
            if self._clut_texture is None:
                GL.glUniform1i(GL.glGetUniformLocation(prog, b"gamma_correction_flag"), 0)
            else:
                GL.glUniform1i(GL.glGetUniformLocation(prog, b"clut"), 1)
                GL.glUniform1i(GL.glGetUniformLocation(prog, b"gamma_correction_flag"), 1)
            GL.glUseProgram(0)
        else:
            if self._clut_texture is not None:
                raise ValueError(f"Software clut is only supported with"
                                 f" high luminance-resolution modes {HIGH_RES_MODES}, got '{mode}'")
        
    @property
    def window(self):
        return self._window

    @window.setter
    def window(self, value):
        self._window = value

        self._window._prepareFBOrender = self._prepareFBOrender
        self._window._finishFBOrender = self._finishFBOrender
        self._window._afterFBOrender = self._afterFBOrender

    @property
    def mode(self):
        self._pixxdevice.updateRegisterCache()
        return self._pixxdevice.getVideoMode()

    @mode.setter
    def mode(self, value):
        if value != self.mode:
            self._pixxdevice.setVideoMode(value)
            self._pixxdevice.updateRegisterCache() 

        self._setup_shader()
        

    @property
    def size(self) -> (int, int):
        """ Visible pixels (width, height) """
        self._pixxdevice.updateRegisterCache()
        return (self._pixxdevice.getVisiblePixelsPerHorizontalLine(),
                self._pixxdevice.getVisibleLinePerVerticalFrame())
    
    @property
    def backlight(self) -> int:
        """ Intensity between 0 and 255 """
        self._pixxdevice.updateRegisterCache()
        return self._pixxdevice.getBacklightIntensity()
    
    @backlight.setter
    def backlight(self, value):
        if self.backlight != value:
            self._pixxdevice.setBacklightIntensity(value)
            self._pixxdevice.updateRegisterCache()
      
    @property
    def scanning_backlight(self) -> bool:
        self._pixxdevice.updateRegisterCache()
        return self._pixxdevice.isScanningBackLightEnabled()
    
    @scanning_backlight.setter
    def scanning_backlight(self, value):
        if self.scanning_backlight != value:
            self._pixxdevice.setScanningBackLight(value)
            self._pixxdevice.updateRegisterCache()
            
    @property
    def register(self) -> dict:
        setters = (attr for attr in dir(self._pixxdevice)
                   if attr.startswith('set'))
        reg = {}
        self._pixxdevice.updateRegisterCache()
        for setter in setters:
            key = setter[3:]
            if key.startswith("Vesa"):  # avoid problem: vesa registers returned "random" entries
                continue
            if hasattr(self._pixxdevice, 'get' + key):
                reg[key] = getattr(self._pixxdevice, 'get' + key)()
            elif hasattr(self._pixxdevice, f'is{key}Enabled'):
                reg[key] = getattr(self._pixxdevice, f'is{key}Enabled')()
        return reg
    
    @register.setter
    def register(self, reg: dict):
        for key, value in reg.items():
            getattr(self._pixxdevice, 'set' + key, value)
        self._pixxdevice.updateRegisterCache()

    def use_calibration_register(self):
        self.register = self.window.monitor.currentCalib['viewpixx']['register'] 
    

def interp_clut(monitor):
    lums = monitor.getLumsPre()
    levels = monitor.getLevelsPre()
    
    if lums.shape[0] != 4 or lums.shape[1] != levels.shape[0]:
        raise ValueError(f"Expects matching levels and luminances,\n"
                         f"got {levels.shape} != {lums.shape}.")
    
    lums = (lums - lums[:, [0]]) / (lums[:, [-1]] - lums[:, [0]] + 1e-8)
    
    is_lum_incr = np.all(np.diff(lums) >= 0, axis=0)  # all guns have to be increasing
    if not np.all(is_lum_incr):
        lums = np.c_[lums[:, 0], lums[:, 1:][:, is_lum_incr]]
        levels = np.r_[levels[0], levels[1:][is_lum_incr]]
        print(f"WARNING: Expects increasing colors, got {len(is_lum_incr) - is_lum_incr.sum()} decreases and dropped them.")
    
    if not np.all(np.diff(levels) >= 0):
        raise ValueError(f"Expects levels to be increasing, got decreases.")
    if np.all(levels[0] != 0):
        raise ValueError(f"Expects levels starting with 0, got {levels[0]}")
    if np.all(levels[-1] == 255):
        levels = levels / 255
    elif np.any(levels[-1] != 1):
        raise ValueError(f"Expects levels ending with 1.0 or 255, got {levels[-1]}")
    
    nguns = lums.shape[0]
    desired_lums = np.linspace(0, 1, 2**16, endpoint=True)
    desired_levels = np.empty((nguns, len(desired_lums)))
    for gun in range(4):
        desired_levels[gun, :] = np.interp(x=desired_lums, xp=lums[gun], fp=levels)
    return desired_levels

                        
                        
def mock_vpixx_devices():
    import sys
    from unittest.mock import MagicMock
    sys.modules['pypixxlib.viewpixx'] = MagicMock()
    
    
def highlum_gradient_test(win):    
    gradient = np.linspace(-1, 1, 2**16).reshape(4, -1)
    #gradient = np.repeat(gradient, gradient.shape[1] / gradient.shape[0], axis=0)
    return visual.GratingStim(win, tex=gradient, units='norm', size=2)
    
    
if __name__ == '__main__':
    from psychopy import visual, core, monitors  # import some libraries from PsychoPy
    import numpy as np

    screen = 1
    mon = monitors.Monitor('ViewPixx')
    mywin = visual.Window(size=mon.getSizePix(), monitor=mon, units="deg", useFBO=True, 
                          screen=screen, fullscr=False, gamma=1)
    vpixx = ViewPixx(mywin)
    
    print("Showing test stimulus (no steps should be visible) ...")
    highlum_gradient_test(mywin).draw()
    mywin.update()
    core.wait(10.0)



