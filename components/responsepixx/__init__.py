#!/usr/bin/env python
# -*- coding: utf-8 -*-



__all__ = ['ResponsepixxComponent']

from os import path
import json
from pathlib import Path
from psychopy.experiment.components import BaseComponent, getInitVals
from psychopy.localization import _translate, _localized as __localized

_localized = __localized.copy()


_localized.update({'forceEndRoutineOnPress': _translate('End Routine on press'),
                   'lights': _translate('Button lights'),
                   'clickable': _translate('Clickable buttons')})

class ResponsepixxComponent(BaseComponent):  # or (VisualComponent)
    """A class for the viewpixx buttonbox responsepixx
    """
    categories = ['Responses']
    targets = ['PsychoPy']
    iconFile = Path(__file__).parent / 'mouse.png'
    tooltip = _translate('Responsepixx: Record Responsepixx buttonpresses')
    plugin = "psychopy-pixx"
    
    def __init__(self, exp, parentName, name='responsepixx',
                 startType='time (s)', startVal=0.0,
                 stopType='duration (s)', stopVal=1.0,
                 startEstim='', durationEstim='', 
                 forceEndRoutineOnPress="any click", lights=True,
                 clickable=['red','green','yellow','blue','white'],
                 timeRelativeTo='responsepixx onset'):
        super(ResponsepixxComponent, self).__init__(
            exp, parentName, name=name,
            startType=startType, startVal=startVal,
            stopType=stopType, stopVal=stopVal,
            startEstim=startEstim, durationEstim=durationEstim)

        self.type = 'Responsepixx'
        self.url = ""

        self.order += [
            'forceEndRoutineOnPress', 'lights', 'clickable',
            ]

        # params

        msg = _translate("Should a button press force the end of the routine"
                         " (e.g end the trial)?")
        self.params['forceEndRoutineOnPress'] = Param(
            forceEndRoutineOnPress, valType='str', inputType="choice", categ='Basic',
            allowedVals=['never', 'any click'],
            updates='constant', direct=False,
            hint=msg,
            label=_localized['forceEndRoutineOnPress'])
        
        msg = _translate("Should the button lights be turned on?")
        self.params['lights'] = Param(
            True, valType='bool', inputType="bool", categ='Basic',
            updates='constant',
            hint=msg,
            label=_localized['lights'])
        
        msg = _translate('A comma-separated list of the buttons (colors) '
                         'that can be clicked.')
        self.params['clickable'] = Param(
            '', valType='list', inputType="single", categ='Basic',
            updates='constant',
            hint=msg,
            label=_localized['clickable'])


    def writeInitCode(self, buff):
        inits = getInitVals(self.params, 'PsychoPy')
        code = ('{} = visual.BaseVisualStim('.format(inits['name']) +
                'win=win, name="{}")\n'.format(inits['name'])
                )
        buff.writeIndentedLines(code)

    def writeFrameCode(self, buff):
        pass

    def writeFrameCodeJS(self, buff):
        pass

    def writeExperimentEndCode(self, buff):
        pass
