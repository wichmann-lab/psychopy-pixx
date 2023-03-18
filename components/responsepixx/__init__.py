#!/usr/bin/env python
# -*- coding: utf-8 -*-



__all__ = ['ResponsepixxComponent']

from os import path
import json
from pathlib import Path
from psychopy.localization import _translate, _localized as __localized
from psychopy.experiment.components import (BaseComponent, Param, getInitVals)

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
        """write the code that will be called at initialization"""
        buff.writeIndented("# This is generated by writeInitCode\n")
        inits = getInitVals(self.params, 'PsychoPy')
        code = ('{} = visual.BaseVisualStim('.format(inits['name']) +
                'win=win, name="{}")\n'.format(inits['name'])
                )
        buff.writeIndentedLines(code)
        code = "from psychopy_pixx.devices import ResponsePixx\n"
        code += "{}Device = ResponsePixx(pixxdevice, buttons = {}, events = [\'down\'], lights = {})\n".format(self.params['name'], self.params["clickable"], self.params["lights"])
        buff.writeIndentedLines(code)

    def writeRoutineStartCode(self, buff):
        """Write the code that will be called at the start of the routine
        """
        buff.writeIndented("# This is generated by the writeStartCode\n")
        code = "# starting the responsepixx and setup a python list for storing the button presses\n"
        code += "{}Device.start()\n".format(self.params["name"])
        code += "{}Resp = []\n".format(self.params["name"])

        buff.writeIndentedLines(code)

    def writeFrameCode(self, buff):
        """Write the code that will be called every frame"""
        buff.writeIndented("# This is generated by the writeFrameCode\n")

        forceEnd = self.params['forceEndRoutineOnPress'].val

        #writes an if statement to determine whether to draw etc
        indented = self.writeStartTestCode(buff)
        buff.setIndentLevel(-indented, relative=True)

        
        indented = self.writeStopTestCode(buff)
        if indented:
            buff.setIndentLevel(-indented, relative=True)


        #if STARTED and not FINISHED!
        code = "if {}.status == STARTED:\n".format(self.params["name"])
        buff.writeIndented(code)
        buff.setIndentLevel(1, relative=True)
        code = "prevButtonState = {}Device.getKeys()\n".format(self.params["name"])
        buff.writeIndented(code)
        code = "if len(prevButtonState)>0:\n"
        buff.writeIndented(code)
        buff.setIndentLevel(1, relative=True)
        code = "last_key = prevButtonState[-1]\n"
        buff.writeIndented(code)
        code = "{}Resp.append(last_key)\n".format(self.params["name"])
        buff.writeIndented(code)
        code = ("currentLoop.addData(\"{}.key\", last_key[\"name\"])\n".format(self.params["name"])
        buff.writeIndented(code)
        code = ("currentLoop.addData(\"{}.rt\", last_key[\"time\"])\n".format(self.params["name"])
        buff.writeIndented(code)
        if forceEnd:
            code ="continueRoutine = False #end routine on click\n"
            buff.writeIndented(code)
        buff.setIndentLevel(-2, relative=True)  # to get out of if statement

        


    def writeRoutineEndCode(self, buff):
        """Write the code that will be called at the end of the routine"""
        buff.writeIndented("# This is generated by the writeStartCode\n")
        code = "{}Device.stop()\n".format(self.params["name"])
        buff.writeIndented(code)