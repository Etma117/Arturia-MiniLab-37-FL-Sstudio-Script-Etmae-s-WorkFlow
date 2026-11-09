# name=MiniLab 37
# supportedHardwareIds=00 20 6B 02 00 04 05

"""
[[
	Surface:	MiniLab3
	Developer:	Farès MEZDOUR
	Version:	1.2

    Copyright (c) 2022 Farès MEZDOUR
]]
"""


import time
import midi
import ui
import sys
import mixer
import transport
import channels
import playlist
import patterns
import plugins
import device




from MiniLab37Process import MiniLabMidiProcessor
from MiniLab37Return import MiniLabLightReturn
from MiniLab37Display import MiniLabDisplay
from MiniLab37Pages import MiniLabPagedDisplay
from MiniLab37Connexion import MiniLabConnexion
from MiniLab37Dispatch import send_to_device
import ArturiaVCOL

## CONSTANT

TEMP = 0.5
COLOUR = [0x10,0x11,0x04,0x05,0x14,0x7F,0x01]
PORT_MIDICC_ANALOGLAB = 10

# Created in OnInit — guard callbacks during reload / dual-port load
_mk3 = None
_processor = None


def _is_ready():
    return _mk3 is not None and _processor is not None

#-----------------------------------------------------------------------------------------

# This is the master class. It will run the init lights pattern 
# and call the others class to process MIDI events


class MidiControllerConfig :

    def __init__(self):
        self._lightReturn = MiniLabLightReturn()
        self._display = MiniLabDisplay()
        self._paged_display = MiniLabPagedDisplay(self._display)
        self._connexion = MiniLabConnexion()
        self._disp = 0
        

    def LightReturn(self) :
        return self._lightReturn
        
    def display(self):
        return self._display

    def paged_display(self):
        return self._paged_display
        
    def connexion(self) :
        return self._connexion
        
    def Idle(self):
        self._paged_display.Refresh()
        
    def Sync(self):
        # Update display

        active_index = channels.selectedChannel()
        channel_name = channels.getChannelName(active_index)
        for i in range(len(channel_name)) :
            if (ord(channel_name[i]) not in range(0,127)) :
                str1 = channel_name[0:i]
                str2 = channel_name[i+1::]
                channel_name = str1 + '?' + str2
        pattern_number = patterns.patternNumber()
        pattern_name = patterns.getPatternName(pattern_number)    

        if active_index != -1 :  
            self._paged_display.SetPageLines(
                'main',
                10,
                line1='%d-%s' % (active_index + 1, channel_name),
                line2='%s' % pattern_name 
                )
            self.paged_display().SetActivePage('main', 1500)
        
        else :
            self._paged_display.SetPageLines(
                'main',
                10,
                line1='No Selection',
                line2='%s' % pattern_name 
                )
            self.paged_display().SetActivePage('main', 1500)


#----------------------------------------------------------------------------------------

# Function called for each event 


def OnMidiMsg(event) :
    if not _is_ready():
        return
    if _processor.ProcessEvent(event):
        event.handled = False


# Function called when FL Studio is starting

def OnInit():
    print('Loaded MIDI script for Arturia MiniLab 37')
    init()
    _mk3.LightReturn().init()
    _mk3.Sync()
    _mk3.paged_display().SetPageLines('welcome', 10, line1=ui.getProgTitle(), line2="Connected")
    _mk3.paged_display().SetActivePage('welcome', expires=1500)
    _mk3.paged_display().SetActivePage('main')
    print("### Messages successfully sent to MiniLab 37 ###")
    print('Pad colors need: Minilab37 DAW OUTPUT enabled + same Port as DAW INPUT (use 236)')


        
def init() :
    
    # Connxexion
    global _mk3 
    global _processor
    _mk3 = MidiControllerConfig()
    _processor = MiniLabMidiProcessor(_mk3) 
    _mk3.connexion().DAWConnexion()
    print("### Successfully created class objects ###")
    
    
# Handles the script when FL Studio closes

def OnDeInit():
    global _mk3
    global _processor
    if _is_ready():
        _mk3.connexion().DAWDisconnection()
    _mk3 = None
    _processor = None
    return
   
  
# Function called when Play/Pause button is ON

def OnUpdateBeatIndicator(value):
    if not _is_ready():
        return
    _mk3.LightReturn().ProcessPlayBlink(value)
    _mk3.LightReturn().ProcessRecordBlink(value)
 

# Function called at refresh, flag value changes depending on the refresh type 

def OnRefresh(flags) :
    if not _is_ready():
        return
    _mk3.LightReturn().PluginParamReturn()
    
    if plugins.isValid(channels.selectedChannel()) :
        string = plugins.getPluginName(channels.selectedChannel())
        if string in ArturiaVCOL.V_COL :
            if not ui.getFocused(5) :
                _mk3.connexion().ArturiaDisconnection()
            else :
                _mk3.connexion().ArturiaConnexion()
        else :
            _mk3.connexion().ArturiaDisconnection()
    else :
        _mk3.connexion().ArturiaDisconnection()

    # Paint LAST — connexion sysex / firmware feedback can flash pads white
    _mk3.LightReturn().PadFunctionColors()

    #print("flags : ", flags)
    if flags not in [4,256,260,4608,4096] :
        _mk3.Sync()
    


# Function called time to time mainly to update the beat indicator

_color_idle = 0

def OnIdle():
    global _color_idle
    if not _is_ready():
        return
    _mk3.Idle()
    # Re-assert pad colors periodically (Stop/firmware can leave them white)
    _color_idle += 1
    if _color_idle >= 25 :
        _color_idle = 0
        _mk3.LightReturn().PadFunctionColors()
    