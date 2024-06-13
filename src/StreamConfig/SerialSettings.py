# ###############################################################################
# 
# Copyright (c) 2024, Septentrio
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
# 
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import configparser
from enum import Enum
import logging
from serial import Serial
import serial.tools.list_ports

class BaudRate(Enum):
    eBAUD300 =  "300"
    eBAUD600 = "600"
    eBAUD1200 = "1200"
    eBAUD2400 = "2400"
    eBAUD4800 = "4800"
    eBAUD9600 = "9600"
    eBAUD19200 = "19200"
    eBAUD38400 = "38400"
    eBAUD57600 = "57600"
    eBAUD115200 = "115200"
    eBAUD230400 = "230400"
    eBAUD460800 = "460800"
    eBAUD500000 = "500000"
    eBAUD576000 = "576000"
    eBAUD921600 = "921600"
    eBAUD1000000 = "1000000"
    eBAUD1500000 = "1500000"
    eBAUD2000000 = "2000000"
    eBAUD2500000 = "2500000"
    eBAUD3000000 = "3000000"
    eBAUD3500000 = "3500000"
    eBAUD4000000 = "4000000"

class Parity(Enum):
    PARITY_NONE = 'N'
    PARITY_EVEN = 'E'
    PARITY_ODD = 'O'
    PARITY_MARK = 'M'
    PARITY_SPACE= 'S'

class StopBits(Enum):
    STOPBITS_ONE = 1
    STOPBITS_ONE_POINT_FIVE= 1.5
    STOPBITS_TWO = 2

class ByteSize(Enum):
    FIVEBITS = 5
    SIXBITS = 6
    SEVENBITS = 7
    EIGHTBITS = 8


class SerialSettings:
    """
    Represents the serial port settings for communication.

    """

    def __init__(self, Port: str = "", baudrate: BaudRate = BaudRate.eBAUD115200, parity: Parity = Parity.PARITY_NONE,
                 stopbits: StopBits = StopBits.STOPBITS_ONE, bytesize: ByteSize = ByteSize.EIGHTBITS,
                 Rtscts: bool = False , logFile : logging = None):
        """
        Initializes a new instance of the SerialSettings class.
        
        """
        self.port :str = Port
        self.baudrate : BaudRate = baudrate
        self.parity : Parity  = parity
        self.stopbits : StopBits = stopbits
        self.bytesize : ByteSize = bytesize
        self.rtscts : bool= Rtscts
                                             
        # Support Logging file 
        self.logFile : logging = logFile    


    def GetAvailablePort(self)-> list :
        """
        Gets the list of available ports.

        Returns:
            list: The list of available ports.
        """
        ports = serial.tools.list_ports.comports()
        availablePort = []
        for port, desc, hwid in sorted(ports):
            availablePort.append([port, desc])
        if self.logFile is not None : 
            self.logFile.debug("%s serial port detected" , str(len(availablePort)))
        return availablePort

    def Connect(self) -> Serial | None : 
        """
        Connects to the serial port.

        Returns:
            Serial: The serial port object.
        """
        try:
            newSerial = Serial(None, baudrate=self.baudrate.value, bytesize=self.bytesize.value,
                          parity=self.parity.value, stopbits=self.stopbits.value, rtscts=self.rtscts, timeout=0.01,exclusive=True)
            newSerial.port = self.port
            newSerial.open()
            return newSerial
        except Exception as e:
            if e.args[0] == 11 : 
                if self.logFile is not None :
                    self.logFile.error("Port %s is already in use" ,self.port )
                raise Exception ("PortError","Port already in use")
            else:
                self.logFile.error("Failed to open serial stream with port %s", self.port)
                self.logFile.error("%s", e)
                raise(e)

    def setPort(self, newport : str):
        """
        Sets the port name.

        Args:
            newport (str): The new port name.
        """
        self.port = newport

    def set_baudrate(self, newbaudrate : BaudRate):
        """
        Sets the baud rate.

        Args:
            newbaudrate (BaudRate): The new baud rate.
        """
        self.baudrate = newbaudrate

    def set_parity(self, newparity : Parity):
        """
        Sets the parity setting.

        Args:
            newparity (Parity): The new parity setting.
        """
        self.parity = newparity

    def set_stopbits(self, newStopBits : StopBits):
        """
        Sets the stop bits setting.

        Args:
            newStopBits (StopBits): The new stop bits setting.
        """
        self.stopbits = newStopBits

    def set_bytesize(self, newbytesize : ByteSize):
        """
        Sets the byte size setting.

        Args:
            newbytesize (ByteSize): The new byte size setting.
        """
        self.bytesize = newbytesize

    def set_rtscts(self, newrtccts : bool):
        """
        Sets the RTS/CTS flow control setting.

        Args:
            newrtccts (bool): The new RTS/CTS flow control setting.
        """
        self.rtscts = newrtccts

    def toString(self) -> str :
        """
        Return current class as a string

        Returns:
            str: class as string
        """
        parity = self.parity.name.replace("PARITY_","")
        return f"Port : {self.port} \n BaudRate :{self.baudrate.value} \n Parity : {parity} \n StopBits : {self.stopbits.value} \n ByteSize : {self.bytesize.value} \n rtscts : {self.rtscts}"
    
    def SaveConfig(self , sectionName : str,SaveConfigFile  : configparser.ConfigParser):
        """
            Add current class values in the configFile
        Args:
            sectionName (str): name of the current section
            SaveConfigFile (configparser.ConfigParser): configparser of the configuration file
        """
        
        SaveConfigFile.set(sectionName,"Serial.Port", str(self.port))
        SaveConfigFile.set(sectionName,"Serial.BaudRate",str(self.baudrate.value))
        SaveConfigFile.set(sectionName,"Serial.Parity",str(self.parity.value))
        SaveConfigFile.set(sectionName,"Serial.StopBits",str(self.stopbits.value))
        SaveConfigFile.set(sectionName,"Serial.ByteSize",str(self.bytesize.value))
        SaveConfigFile.set(sectionName,"Serial.RtcCts",str(self.rtscts))