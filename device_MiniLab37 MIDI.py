# name=MiniLab 37 Arturia

"""
[[
	Surface:	MiniLab 37 MIDI
	Developer:	Farès MEZDOUR
	Version:	1.2
]]
"""

# Forwards Analog Lab CCs to port 10.
# Bank 1 pad notes (36-43) → transport / windows.
# Note layout is vertically flipped vs silk-screen icons:
#   36-39 bottom Stop/Play/Rec/Metro, 40-43 top Mixer/Playlist/Piano/Undo
# Bank 2 (44-51) still passes for Momentum.

import midi
import device
import transport
import ui
import channels

WidMixer = 0
WidPlaylist = 2
WidPianoRoll = 3


def _is_note_msg(event):
    nibble = event.status & 0xF0
    return nibble in (0x80, 0x90) or event.status in (128, 144, 137, 153)


def _is_note_on(event):
    nibble = event.status & 0xF0
    if event.status in (153, 144) or nibble == 0x90:
        return event.data2 > 0
    return False


def _show_and_focus(window):
    if not ui.getVisible(window):
        ui.showWindow(window)
    if not ui.getFocused(window):
        ui.setFocused(window)


def _hide_plugins():
    for i in range(channels.channelCount()):
        channels.showCSForm(i, 0)


def _toggle_window(window, name):
    if ui.getFocused(window):
        ui.hideWindow(window)
        print('Pad:', name, 'Off')
    else:
        _hide_plugins()
        _show_and_focus(window)
        print('Pad:', name)


def _pad_action(note):
    # Bottom row
    if note == 36:
        transport.stop()
        print('Pad: Stop')
    elif note == 37:
        transport.start()
        print('Pad: Play')
    elif note == 38:
        transport.record()
        print('Pad: Record')
    elif note == 39:
        transport.globalTransport(midi.FPT_Metronome, 1)
        print('Pad: Metronome')
    # Top row — toggle open/close
    elif note == 40:
        _toggle_window(WidMixer, 'Mixer')
    elif note == 41:
        _toggle_window(WidPlaylist, 'Playlist')
    elif note == 42:
        _toggle_window(WidPianoRoll, 'Piano Roll')
    elif note == 43:
        transport.globalTransport(midi.FPT_Undo, 1)
        print('Pad: Undo')


class TSimple():

    def OnMidiMsg(self, event):

        if _is_note_msg(event) and 36 <= event.data1 <= 43:
            if _is_note_on(event):
                _pad_action(event.data1)
            event.handled = True
            return

        if event.status == midi.MIDI_CONTROLCHANGE:
            msg = event.status + (event.data1 << 8) + (event.data2 << 16) + (10 << 24)
            device.forwardMIDICC(msg, 2)
            event.handled = False


Simple = TSimple()

def OnMidiMsg(event):
    Simple.OnMidiMsg(event)
