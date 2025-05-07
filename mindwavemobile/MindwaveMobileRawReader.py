import bluetooth
import time
import textwrap


class MindwaveMobileRawReader:
    START_OF_PACKET_BYTE = 0xaa;
    def __init__(self, address="C4:64:E3:E8:42:90"): #A4:DA:32:6F:EB:B5
        self._buffer = [];
        self._bufferPosition = 0;
        self._isConnected = False;
        self._mindwaveMobileAddress = address
        
    def connectToMindWaveMobile(self):
        # First discover mindwave mobile address, then connect.
        if (self._mindwaveMobileAddress is None):
            self._mindwaveMobileAddress = self._findMindwaveMobileAddress()
        if (self._mindwaveMobileAddress is not None):            
            print ("Discovered Mindwave Mobile...")
            self._connectToAddress(self._mindwaveMobileAddress)
        else:
            self._printErrorDiscoveryMessage()
        
    def _findMindwaveMobileAddress(self):
        nearby_devices = bluetooth.discover_devices(lookup_names = True)
        for address, name in nearby_devices:
            if (name == "MindWave Mobile"):
                return address
        return None
        
    def _connectToAddress(self, mindwaveMobileAddress):
        self.mindwaveMobileSocket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        #self.mindwaveMobileSocket.settimeout(10)
        
        while (not self._isConnected):
            try:
                print("Attempting to connect")
                self.mindwaveMobileSocket.connect((mindwaveMobileAddress, 1))
                self._isConnected = True
            except bluetooth.btcommon.BluetoothError as error:
                print("Could not connect: ", error, "; Retrying in 5s...")
                time.sleep(5)
            #except socket.timeout:
                #print("Socket connection timed out")
           

    def isConnected(self):
        return self._isConnected

    def _printErrorDiscoveryMessage(self):
         print((textwrap.dedent("""\
                    Could not discover Mindwave Mobile. Please make sure the
                    Mindwave Mobile device is in pairing mode and your computer
                    has bluetooth enabled.""").replace("\n", " ")))

    def _readMoreBytesIntoBuffer(self, amountOfBytes):
        newBytes = self._readBytesFromMindwaveMobile(amountOfBytes)
        self._buffer += newBytes
    
    def _readBytesFromMindwaveMobile(self, amountOfBytes):
        missingBytes = amountOfBytes
        receivedBytes = b''   
        
        # Sometimes the socket will not send all the requested bytes
        # on the first request, therefore a loop is necessary...
        while(missingBytes > 0):
            receivedBytes += self.mindwaveMobileSocket.recv(missingBytes)
            missingBytes = amountOfBytes - len(receivedBytes)
        return receivedBytes;

    def peekByte(self):
        self._ensureMoreBytesCanBeRead();
        return ord(self._buffer[self._bufferPosition])

    def getByte(self):
        self._ensureMoreBytesCanBeRead(100);
        return self._getNextByte();
    
    def  _ensureMoreBytesCanBeRead(self, amountOfBytes):
        if (self._bufferSize() <= self._bufferPosition + amountOfBytes):
            self._readMoreBytesIntoBuffer(amountOfBytes)
    
    def _getNextByte(self):
        nextByte = self._buffer[self._bufferPosition]   
        self._bufferPosition += 1;
        return nextByte;

    def getBytes(self, amountOfBytes):
        self._ensureMoreBytesCanBeRead(amountOfBytes);
        return self._getNextBytes(amountOfBytes);
    
    def _getNextBytes(self, amountOfBytes):
        nextBytes = list(self._buffer[self._bufferPosition: self._bufferPosition + amountOfBytes]) 
        self._bufferPosition += amountOfBytes
        return nextBytes
    
    def clearAlreadyReadBuffer(self):
        self._buffer = self._buffer[self._bufferPosition : ]
        self._bufferPosition = 0;
    
    def _bufferSize(self):
        return len(self._buffer);
        
#------------------------------------------------------------------------------ 
