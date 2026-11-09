import device
import ui
import time
import transport
import mixer
import channels
import plugins

import MiniLab37Plugin
from MiniLab37Dispatch import send_to_device 



# This class handles visual feedback functions.


WidMixer = 0
WidChannelRack = 1
WidPlaylist = 2
WidBrowser = 4
WidPlugin = 5


# MAPS

PAD_MAP = [
        0x04, 0x05, 0x06, 0x07,
        0x08, 0x09, 0x0A, 0x0B]

        
COLOR_MAP = [
        [0x00, 0x7F, 0x10],
        [0x00, 0x7F, 0x19],
        [0x00, 0x7F, 0x32],
        [0x00, 0x7F, 0x4B],
        [0x00, 0x7F, 0x64],
        [0x00, 0x7F, 0x7F],
        [0x00, 0x64, 0x7F],
        [0x00, 0x4B, 0x7F],
        [0x00, 0x32, 0x7F],
        [0x00, 0x19, 0x7F],
        [0x00, 0x00, 0x7F],
        [0x19, 0x00, 0x7F],
        [0x32, 0x00, 0x7F],
        [0x4B, 0x00, 0x7F],
        [0x64, 0x00, 0x7F],
        [0x7F, 0x00, 0x7F],
        [0x7F, 0x00, 0x64],
        [0x7F, 0x00, 0x4B],
        [0x7F, 0x00, 0x32],
        [0x7F, 0x00, 0x19],
        [0x7F, 0x00, 0x00],
        [0x7F, 0x19, 0x00],
        [0x7F, 0x32, 0x00],
        [0x7F, 0x4B, 0x00],
        ]

# Hardware pad LED ids: Pad 1..8 = 0x04..0x0B (Arturia MiniLab 3/37)
# Pad 1-4 = top (Arp/Pad/Prog/Loop), Pad 5-8 = bottom (Stop/Play/Rec/Tap)
PAD_LED_IDS = [
    0x04, 0x05, 0x06, 0x07,  # top: Mixer / Playlist / Piano / Undo
    0x08, 0x09, 0x0A, 0x0B,  # bottom: Stop / Play / Record / Metronome
]

# R, G, B (0-127) — softer / less bright idle colors
PAD_LED_COLORS = [
    (0x00, 0x12, 0x32),  # Mixer — blue
    (0x00, 0x32, 0x28),  # Playlist — cyan
    (0x32, 0x00, 0x32),  # Piano roll — magenta
    (0x32, 0x18, 0x00),  # Undo — orange
    (0x1C, 0x1C, 0x1C),  # Stop — dim grey
    (0x00, 0x2C, 0x00),  # Play — green
    (0x2C, 0x00, 0x00),  # Record — red
    (0x2C, 0x2C, 0x00),  # Metronome — yellow
]

# Slightly brighter when that function is active
PAD_LED_COLORS_ACTIVE = [
    (0x00, 0x18, 0x40),
    (0x00, 0x40, 0x32),
    (0x40, 0x00, 0x40),
    (0x40, 0x20, 0x00),
    (0x28, 0x28, 0x28),
    (0x00, 0x48, 0x00),  # Play on
    (0x48, 0x00, 0x00),  # Record on
    (0x48, 0x48, 0x00),  # Metro on
]


class MiniLabLightReturn:

    def _set_pad_rgb(self, led_id, r, g, b) :
        send_to_device(bytes([0x02, 0x02, 0x16, led_id, r, g, b]))


    def PadFunctionColors(self) :
        """Paint Bank 1 pads; play/rec/metro a bit brighter when active."""
        colors = [list(c) for c in PAD_LED_COLORS]
        if transport.isPlaying() != 0 or mixer.getSongTickPos() != 0 :
            colors[5] = list(PAD_LED_COLORS_ACTIVE[5])
        if transport.isRecording() :
            colors[6] = list(PAD_LED_COLORS_ACTIVE[6])
        if ui.isMetronomeEnabled() :
            colors[7] = list(PAD_LED_COLORS_ACTIVE[7])

        for i in range(8) :
            r, g, b = colors[i]
            self._set_pad_rgb(PAD_LED_IDS[i], r, g, b)
        # DAW transport LED aliases (same colors — do NOT send full white)
        self._set_pad_rgb(0x58, *colors[4])
        self._set_pad_rgb(0x59, *colors[5])
        self._set_pad_rgb(0x5A, *colors[6])
        self._set_pad_rgb(0x5B, *colors[7])


    def init(self) :
        self.PadFunctionColors()
        print('Pad colors applied (dim)')


    def MetronomeReturn(self) :
        self.PadFunctionColors()

    def LoopReturn(self) :
        # Avoid transport LED writes that reset pad bank colors
        pass

    def RecordReturn(self) :
        self.PadFunctionColors()

    def PlayReturn(self) :
        self.PadFunctionColors()

    def ProcessPlayBlink(self, value):
        self.PadFunctionColors()

    def ProcessRecordBlink(self, value) :
        self.PadFunctionColors()
                
    
    def PluginParamReturn(self):
        if channels.selectedChannel(1) != -1 :
            if plugins.isValid(channels.selectedChannel()) : 
                if plugins.getPluginName(channels.selectedChannel()) in MiniLab37Plugin.NATIVE_PLUGIN_LIST : #Check if possible on ALL plugin and not only native ones
                    #print("Reresh parameter")
                    parameter, value, mapped = MiniLab37Plugin.Plugin(0, 0, 0)
    
    
    def LEDTest(self) :
        send_to_device(bytes([0x02, 0x02, 0x16, 0x04, 0x00, 0x00, 0x7f]))
        send_to_device(bytes([0x02, 0x02, 0x16, 0x05, 0x00, 0x00, 0x00]))
        time.sleep(0.1)
        send_to_device(bytes([0x02, 0x02, 0x16, 0x04, 0x00, 0x00, 0x00]))
        send_to_device(bytes([0x02, 0x02, 0x16, 0x05, 0x00, 0x00, 0x7f]))
        time.sleep(0.1)

    
        
    

         
           

 
