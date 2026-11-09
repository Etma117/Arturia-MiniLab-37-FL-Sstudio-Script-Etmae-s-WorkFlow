import channels

# This script contains the strings of the V Collection software

V_COL = [
    'Mellotron V',
    'Synthi V',
    'CZ V',
    'ARP 2600 V3',
    'Clavinet V',
    'CS-80 V4',
    'DX7 V',
    'Farfisa V',
    'Jup-8 V4',
    'Matrix-12 V2',
    'Mini V4',
    'Modular V3',
    'Buchla Easel V',
    'Piano V3',
    'Solina V2',
    'Stage-73 V2',
    'Synclavier V',
    'B-3 V2',
    'VOX Continental V2',
    'Wurli V3',
    'CMI V',
    'OP-Xa V',
    'Emulator II V',
    'Vocoder V',
    'Jun-6 V',
    'SQ80 V',
    'Prophet-5 V',
    'Prophet-VS V',
    'KORG MS-20 V',
    'Acid V',
    'Pigments',
    'MiniFreak V',
    'Augmented STRINGS',
    'Augmented VOICES',
    'Augmented GRAND PIANO',
    'Augmented BRASS',
    'Augmented WOODWINDS',
    'Augmented YANGTZE',
    'Augmented MALLETS',
    'MiniBrute V',
    'CP-70 V',
    'Synthx V',
    'Pure LoFi',
    'Jup-8000 V',
    'SEM V3',
    'Pure Sub',
    'Analog Lab V',
    'B-3 V',
    'CS-80 V3',
    'Jup-8 V3',
    'Mini V3',
    'Piano V',
    'Piano V2',
    'Prophet V3',
    'Stage-73 V',
    'Wurli V2',
    'SEM V2',
    ]
         

class ArturiaVCOLLECTION() :
    
    def __init__(self) :
        self._v_col = []
    
    def v_col_aff(self) :
        #print(self._v_col)
        return self._v_col
   
    def AddVST(self) :
        string = channels.getChannelName(channels.channelNumber())
        present = False
        for i in self._v_col :
            if string == i :
                present = True
        if present == False and string in V_COL :
            self._v_col.append(string)

    