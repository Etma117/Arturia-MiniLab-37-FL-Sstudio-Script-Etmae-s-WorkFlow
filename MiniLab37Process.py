import channels
import mixer
import patterns
import transport
import ui
import device
import plugins
import midi

import ArturiaVCOL
import MiniLab37Plugin
from MiniLab37Dispatch import MidiEventDispatcher
from MiniLab37Dispatch import send_to_device
from MiniLab37Display import MiniLabDisplay
from MiniLab37Pages import MiniLabPagedDisplay
from MiniLab37Navigation import NavigationMode
from MiniLab37Dispatch import send_to_device
from MiniLab37Plugin import KNOB_HW_VALUE




# This class processes all CC coming from the controller
# The class creates new handler for each function
# The class calls the right fonction depending on the incoming CC


## CONSTANT


PORT_MIDICC_ANALOGLAB = 10
WidMixer = 0
WidChannelRack = 1
WidPlaylist = 2
WidPianoRoll = 3
WidBrowser = 4
WidPlugin = 5


# Event code indicating stop event
SS_STOP = 0

# Event code indicating start start event
SS_START = 2

# Shift HW Function
SHIFT = 0

ANALOGLAB_KNOB_ID = (
                    9,
                    16,
                    17,
                    18,
                    19,
                    71,
                    74,
                    76,
                    77,
                    82,
                    83,
                    85,
                    93,
                    112,
                    113,
                    114,
                    115,
                    )


KNOB_ID = (
            86,
            87,
            89,
            90,
            110,
            111,
            116,
            117
            )


PAD_MATRIX = [
        0x38, 0x39, 0x3A, 0x3B,
        0x34, 0x35, 0x36, 0x37,
        0x48, 0x49, 0x4A, 0x4B,
        0x44, 0x45, 0x46, 0x47,
]

PAD_MATRIX_STATE = [
        0, 0, 0, 0,
        0, 0, 0, 0,
        0, 0, 0, 0,
        0, 0, 0, 0
]

                    

# FPC MAP
FPC_MAP = {
            "36":37,
            "37":36,
            "38":42,
            "39":54,
            "40":40,
            "41":38,
            "42":46,
            "43":44,
            
            "44":48,
            "45":47,
            "46":45,
            "47":43,
            "48":49,
            "49":55,
            "50":51,
            "51":53
            }
            
# KNOB HW VALUE
KNOB_HW_ID = [
            0x07,
            0x08,
            0x09,
            0x0A,
            0x0B,
            0x0C,
            0x0D,
            0x0E,
            ]
            
# UPDATE KNOBS
UPDATE_KNOB = 0

            


class MiniLabMidiProcessor:
    @staticmethod
    def _is_pressed(event):
        return event.controlVal != 0

    def __init__(self, mk3):
        def by_midi_id(event) : return event.midiId
        def by_control_num(event) : return event.controlNum
        def by_velocity(event) : return event.data2
        def by_status(event) : return event.status
        def by_sysex(event) : return event.sysex
        def ignore_release(event): return self._is_pressed(event)
        def ignore_press(event): return not self._is_pressed(event)

        self._mk3 = mk3

        self._midi_id_dispatcher = (
            MidiEventDispatcher(by_midi_id)
            .NewHandler(176, self.OnCommandEvent)
            .NewHandler(224, self.OnWheelEvent)  
            )
            
        self._sysex_dispatcher = (
            MidiEventDispatcher(by_sysex)
            .NewHandler(b'\xf0\x00 k\x7fB\x02\x00@b\x01\xf7', self.ArturiaMemory, ignore_release)
            .NewHandler(b'\xf0\x00 k\x7fB\x02\x00@b\x02\xf7', self.DAWMemory, ignore_release)
            )
        
        self._midi_command_dispatcher = (
            MidiEventDispatcher(by_control_num)
            
            # MAPPING PAD (Bank 1 / DAW CCs 102-109)
            # Top: Mixer | Playlist | Piano Roll | Undo
            # Bottom: Stop | Play | Record | Metronome
            
            .NewHandler(102, self.ToggleMixer, ignore_press)
            .NewHandler(103, self.TogglePlaylist, ignore_press)
            .NewHandler(104, self.TogglePianoRoll, ignore_press)
            .NewHandler(105, self.Undo, ignore_press)
            .NewHandler(106, self.Stop)
            .NewHandler(107, self.Start, ignore_press)
            .NewHandler(108, self.Record, ignore_press)
            .NewHandler(109, self.SetClick, ignore_press)
            .NewHandler(118, self.SwitchWindow, ignore_release)
            .NewHandler(28, self.OnKnobEvent)
            .NewHandler(29, self.PluginTest)
            #.NewHandler(29, self.AllLEDs, ignore_release)
            .NewHandler(119, self.ToggleBrowserChannelRack, ignore_release)
            .NewHandler(27, self.ShiftOn)
            
            
            # MAPPING KNOBS
            
            .NewHandler(14, self.SetVolumeTrack)
            .NewHandler(31, self.SetPanTrack)
            .NewHandlerForKeys(ANALOGLAB_KNOB_ID, self.ForwardAnalogLab)
            .NewHandlerForKeys(KNOB_ID, self.Plugin)
            .NewHandler(1, self.OnWheelEvent)
            .NewHandler(15, self.Plugin)
            .NewHandler(30, self.Plugin)
            
            
        )
        
        self._knob_dispatcher = (
            MidiEventDispatcher(by_velocity)
            .NewHandlerForKeys(range(65,73), self.Navigator)
            .NewHandlerForKeys(range(55,63), self.Navigator)
        )
        
            # MAPPING WHEEL
        
        self._wheel_dispatcher = (
            MidiEventDispatcher(by_status)
            
        )
        
            #~NAVIGATION
        
        self._navigation = NavigationMode(self._mk3.paged_display())



    # DISPATCH



    def ProcessEvent(self, event) :
        # Pads may arrive as ch10 (153/137) or as plain note on/off in 36-51
        nibble = event.status & 0xF0
        if event.status in [153, 137] or (nibble in (0x90, 0x80) and 36 <= event.data1 <= 51) :
            return self.OnDrumEvent(event)
        else :
            return self._midi_id_dispatcher.Dispatch(event)


    def OnCommandEvent(self, event):
        self._midi_command_dispatcher.Dispatch(event)

    def OnWheelEvent(self, event):
        if channels.selectedChannel(1) != -1 :
            if plugins.isValid(channels.selectedChannel()) : 
                if plugins.getPluginName(channels.selectedChannel()) in ArturiaVCOL.V_COL :
                    device.forwardMIDICC(event.status + (event.data1 << 8) + (event.data2 << 16) + (PORT_MIDICC_ANALOGLAB << 24))
        # self._wheel_dispatcher.Dispatch(event)

    def OnKnobEvent(self, event):
        self._knob_dispatcher.Dispatch(event)

    def OnDrumEvent(self, event) :
        # Bank 2 (notes 44-51): Momentum / sampling — pass notes as-is
        # Bank 1 (notes 36-43): window/transport (or Shift = optional FPC drums)
        # Note layout is vertically flipped vs pad icons:
        #   36-39 = bottom (Stop/Play/Rec/Metro), 40-43 = top (Mixer/Playlist/Piano/Undo)
        global SHIFT
        index = event.data1
        nibble = event.status & 0xF0
        is_on = event.status in (153, 144) or (nibble == 0x90 and event.data2 > 0)
        is_off = event.status in (137, 128) or nibble == 0x80 or (nibble == 0x90 and event.data2 == 0)

        if index >= 44 :
            if is_on :
                self.PadOn(index)
            elif is_off :
                self.PadOff(index)
            event.handled = False
            return False

        if SHIFT :
            if is_on :
                self.PadOn(index)
            elif is_off :
                self.PadOff(index)
            mapped = FPC_MAP.get(str(index))
            if mapped is not None :
                event.data1 = mapped
            event.handled = False
            return False

        # Bank 1 as workflow pads — don't grey out function colors on press
        if is_on and 36 <= index <= 43 :
            self.PadNoteAction(index, event)
        event.handled = True
        return False


    def PadNoteAction(self, note, event) :
        # Bottom row (icons Stop/Play/Rec/Tap)
        if note == 36 :
            self.Stop(event)
        elif note == 37 :
            self.Start(event)
        elif note == 38 :
            self.Record(event)
        elif note == 39 :
            self.SetClick(event)
        # Top row (icons Arp/Pad/Prog/Loop)
        elif note == 40 :
            self.ToggleMixer(event)
        elif note == 41 :
            self.TogglePlaylist(event)
        elif note == 42 :
            self.TogglePianoRoll(event)
        elif note == 43 :
            self.Undo(event)

    # WINDOW



    def _show_and_focus(self, window):
        if not ui.getVisible(window):
            ui.showWindow(window)
        if not ui.getFocused(window):
            ui.setFocused(window)
  
  
    def _hideAll(self, event) :
        for i in range (channels.channelCount()) :
            channels.showCSForm(i, 0)


    def SwitchWindow(self, event) :
        if ui.getFocused(WidChannelRack) :
            self.showPlugin(event)
        elif ui.getFocused(WidPlugin) :
            self.showPlugin(event)
        elif ui.getFocused(WidMixer) :
            mixer.armTrack(mixer.trackNumber())
            #plugin = channels.selectedChannel()
            # for i in range(plugins.getParamCount(plugin)) :
                # print(i, plugins.getPluginName(channels.selectedChannel()),plugins.getParamName(i,plugin), plugins.getParamValue(i,plugin))
            #self.GetConnexionMessage()
        elif ui.getFocused(WidBrowser) :
            nodeFileType = ui.getFocusedNodeFileType()
            if nodeFileType == -1:
                return
            if nodeFileType <= -100:
                ui.toggleBrowserNode()
            else:
                ui.selectBrowserMenuItem()
                if not ui.isInPopupMenu() :
                    self._navigation.PressRefresh()
                else :
                    transport.globalTransport(midi.FPT_No, 1)
                    self._show_and_focus(WidPlugin)
        



    # NAVIGATION



    def ToggleBrowserChannelRack(self, event) :
        if ui.getFocused(WidBrowser) != True :
            self._hideAll(event)
            self._show_and_focus(WidBrowser)
            self._navigation.BrowserRefresh()
        else :
            self._hideAll(event)
            self._show_and_focus(WidChannelRack)
            self._navigation.ChannelRackRefresh()
            
    def TogglePlaylistChannelRack(self, event) :
        if ui.getFocused(WidPlaylist) != True :
            self._hideAll(event)
            self._show_and_focus(WidPlaylist)
        else :
            self._hideAll(event)
            self._show_and_focus(WidChannelRack)


    def ToggleMixer(self, event) :
        if ui.getFocused(WidMixer) :
            ui.hideWindow(WidMixer)
            self._navigation.WindowRefresh('Mixer Off')
        else :
            self._hideAll(event)
            self._show_and_focus(WidMixer)
            self._navigation.WindowRefresh('Mixer')


    def TogglePlaylist(self, event) :
        if ui.getFocused(WidPlaylist) :
            ui.hideWindow(WidPlaylist)
            self._navigation.WindowRefresh('Playlist Off')
        else :
            self._hideAll(event)
            self._show_and_focus(WidPlaylist)
            self._navigation.WindowRefresh('Playlist')


    def TogglePianoRoll(self, event) :
        if ui.getFocused(WidPianoRoll) :
            ui.hideWindow(WidPianoRoll)
            self._navigation.WindowRefresh('Piano Off')
        else :
            self._hideAll(event)
            self._show_and_focus(WidPianoRoll)
            self._navigation.WindowRefresh('Piano Roll')


    def Undo(self, event) :
        transport.globalTransport(midi.FPT_Undo, 1)
        self._navigation.UndoRefresh()


    def Navigator(self, event):
    
        if event.data2 in range(65,73) :
            event.data2 = 65
        elif event.data2 in range(55,63) :
            event.data2 = 62
            
        if ui.getFocused(WidPlugin) == True :
            self._hideAll(event)         
        elif ui.getFocused(WidBrowser) :
            if not ui.isInPopupMenu() :  
                if event.data2 == 62 :
                    ui.previous()
                elif event.data2 == 65 :
                    ui.next()
                ui.previewBrowserMenuItem()
                self._navigation.HintRefresh(ui.getFocusedNodeCaption())
            else :
                if event.data2 == 62 :
                    ui.up()
                elif event.data2 == 65 :
                    ui.down()
                self._navigation.HintRefresh(ui.getFocusedNodeCaption())
        elif ui.getFocused(WidChannelRack) :
            self._show_and_focus(WidChannelRack)
            if event.data2 == 62 :
                self._show_and_focus(WidChannelRack)
                self._hideAll(event)
                ui.previous()
                mixer.setTrackNumber(channels.getTargetFxTrack(channels.selectedChannel()),3)
            elif event.data2 == 65 :  
                self._show_and_focus(WidChannelRack)
                self._hideAll(event)
                ui.next()
                mixer.setTrackNumber(channels.getTargetFxTrack(channels.selectedChannel()),3)
        else :
            ui.setFocused(WidChannelRack)
            

    def PluginTest(self, event) :
        if ui.getFocused(WidPlugin) :
            if channels.selectedChannel(1) != -1 :
                string = plugins.getPluginName(channels.selectedChannel())
                if string in ArturiaVCOL.V_COL :
                    self.ForwardAnalogLab(event)
                else :
                    self.PluginPreset(event)
        else :
            if event.data2 > 64 :
                self.FastForward(event)
            else :
                self.Rewind(event)


    def showPlugin(self, event) :
        channels.showCSForm(channels.selectedChannel(), -1)


    # FUNCTIONS



    def Record(self, event) :
        transport.record()
        self._mk3.LightReturn().PadFunctionColors()
    
    
    def Start(self, event) :
        transport.start()
        self._mk3.LightReturn().PadFunctionColors()
    
    
    def Stop(self, event) :
        # Do not send white to 0x58 — that resets all pad colors on MiniLab 37
        if self._is_pressed(event) :
            transport.stop()
        self._mk3.LightReturn().PadFunctionColors()
     

    def Loop(self, event) :
        transport.globalTransport(midi.FPT_LoopRecord,1)
        self._navigation.LoopRefresh()
        self._mk3.LightReturn().PadFunctionColors()

    def Overdub(self, event) :
        transport.globalTransport(midi.FPT_Overdub,1)
        self._navigation.OverdubRefresh()
        
   
    def FastForward(self, event) :
        pos = transport.getSongPos(2)
        transport.setSongPos(pos+24,2)
        self._navigation.FastForwardRefresh()

    
    def Rewind(self, event) :
        pos = transport.getSongPos(2)
        transport.setSongPos(pos-24,2)
        self._navigation.RewindRefresh()


    def SetClick(self, event) :
        transport.globalTransport(midi.FPT_Metronome,1)
        self._navigation.MetronomeRefresh()
        self._mk3.LightReturn().PadFunctionColors()
        
    
    def TapTempo(self, event) :
        if self._is_pressed(event) :
            transport.globalTransport(midi.FPT_TapTempo,1)
            self._navigation.TapTempoRefresh()
        self._mk3.LightReturn().PadFunctionColors()
      
      
    def SetVolumeTrack(self, event) :
        if not ui.getFocused(WidPlugin) : 
            value = event.data2/127
            mixer.setTrackVolume(mixer.trackNumber(),value, 2)
            self._navigation.VolumeChRefresh(value, 4)
        else :
            self.Plugin(event)
            
   
    def SetPanTrack(self, event) :
        if not ui.getFocused(WidPlugin) :
            value = round(event.data2*(128/127)-64)/64
            mixer.setTrackPan(mixer.trackNumber(),value, 2)
            self._navigation.PanChRefresh(value, 3)
        else :
            self.Plugin(event)
            

    def AnalogLabPreset(self, event) :
        if event.data2 == 65 :
            device.forwardMIDICC(event.status + (0x1D << 8) + (0x7F << 16) + (PORT_MIDICC_ANALOGLAB << 24))
        elif event.data2 == 63 :
            device.forwardMIDICC(event.status + (0x1C << 8) + (0x7F << 16) + (PORT_MIDICC_ANALOGLAB << 24))


    def Plugin(self, event) :

        global UPDATE_KNOB
        global KNOB_HW_VALUE
        
        if event.data1 != 29 :
            #if ui.getFocused(WidPlugin) :
            global DISPLAY_TYPE
            if event.status != 224 :
                clef = event.data1
            else :
                clef = 224
                
            parameter, value, mapped = MiniLab37Plugin.Plugin(event.data1, event.data2, 1)

            if event.data1 in KNOB_ID :
                self._navigation.PluginRefresh(parameter, value, mapped, event.data2, 3)
                DISPLAY_TYPE = 3
            elif event.data1 != 1 :
                self._navigation.PluginRefresh(parameter, value, mapped, event.data2, 4)
                DISPLAY_TYPE = 4
            #else :
            #self._navigation.NoPlugin()
        else :
            clef = event.data1
            KNOB_HW_VALUE, mapped = MiniLab37Plugin.Plugin(event, 0, 1)
        
            UPDATE_KNOB = mapped

            

    def PluginPreset(self, event) :
        if event.data2 in range(65,73) :
            if channels.selectedChannel(1) != -1 :
                plugins.nextPreset(channels.selectedChannel())
        elif event.data2 in range(55,63) :
            if channels.selectedChannel(1) != -1 :
                plugins.prevPreset(channels.selectedChannel())
        
    
    
    def ForwardAnalogLab(self, event) :
        if channels.selectedChannel(1) != -1 :
            if plugins.isValid(channels.selectedChannel(1)) : 
                if plugins.getPluginName(channels.selectedChannel()) in ArturiaVCOL.V_COL :
                    device.forwardMIDICC(event.status + (event.data1 << 8) + (event.data2 << 16) + (PORT_MIDICC_ANALOGLAB << 24))
                else :
                    self.Plugin(event, 0, 1)
        
        
    # UTILITY
   
   
        
    def FakeMIDImsg(self) :
        transport.globalTransport(midi.FPT_Punch,1)


    def ShiftIsPressed(self, event) :
        if ui.getFocused(WidBrowser) :
            if ui.isInPopupMenu():
                transport.globalTransport(midi.FPT_Escape, 1)
                self._navigation.BackRefresh()
        return self._is_pressed(event)


    def ShiftOn(self, event) :
        global SHIFT
        SHIFT = self.ShiftIsPressed(event)


    def PadOn(self, index) :
        index= index-36
        PAD_MATRIX_STATE[index] = 1
        self.PadRefresh(PAD_MATRIX_STATE)
 
    
    def PadOff(self, index) :
        index = index-36
        PAD_MATRIX_STATE[index] = 0
        self.PadRefresh(PAD_MATRIX_STATE)


    def PadRefresh(self, Matrix) :
        for i in range(16) :
            if PAD_MATRIX_STATE[i] :
                send_to_device(bytes([0x02, 0x02, 0x16, PAD_MATRIX[i], 0x58, 0x58, 0x58, 0x7F]))
            else :
                send_to_device(bytes([0x02, 0x02, 0x16, PAD_MATRIX[i], 0x14, 0x14, 0x14, 0x7F]))
                

        
    def SetParamValue(self, event) :
        
        self.Plugin(event)
        
        if UPDATE_KNOB :
            for i in range (8) :
                value = round(KNOB_HW_VALUE[i]*127)
                send_to_device(bytes([0x21, 0x10, 0x40, KNOB_HW_ID[i], 0x00, value]))
                
    
    def DAWMemory(self) :
        global MEMORY
        MEMORY = 2
        
    def ArturiaMemory(self) :
        global MEMORY
        MEMORY = 1
        
        
    
            
    

