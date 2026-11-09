from MiniLab37Dispatch import send_to_device

# This class handles the connexion messages


class MiniLabConnexion :
    
    def __init__(self):
        
        self._isArturia = 0
        self._isDAW = 0
        
        
    def ArturiaConnexion(self) :
        # Only send on transition — spam resets pad LED colors to white
        if self._isArturia == 1 :
            return
        send_to_device(bytes([0x04, 0x01, 0x60, 0x01, 0x00, 0x02, 0x00]))
        self._isArturia = 1
        
    def ArturiaDisconnection(self) :
        # Only send on transition — 0x6A 0x10 was wiping all pad colors every refresh
        if self._isArturia == 0 :
            return
        send_to_device(bytes([0x04, 0x01, 0x60, 0x0A, 0x0A, 0x5F, 0x51, 0x00]))
        send_to_device(bytes([0x02, 0x02, 0x40, 0x6A, 0x10]))
        self._isArturia = 0
        
    def DAWConnexion(self) : 
        if self._isDAW == 1 :
            return
        send_to_device(bytes([0x02, 0x02, 0x40, 0x6A, 0x21]))
        self._isDAW = 1
        
    def DAWDisconnection(self) : 
        if self._isDAW == 0 :
            return
        send_to_device(bytes([0x02, 0x02, 0x40, 0x6A, 0x20]))
        self._isDAW = 0
        
    def MemoryRequest(self) :
        send_to_device(bytes([0x01, 0x00, 0x40, 0x01]))

    def TestArturia(self) :
        send_to_device(bytes([0x04, 0x01, 0x60, 0x01, 0x31, 0x32, 0x33, 0x00]))
        
