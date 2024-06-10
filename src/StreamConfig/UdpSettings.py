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
import socket


class DataFlow(Enum):
    """
    Possible Data Flow for a UDP Stream
    """
    OnlyTransmit = 0
    OnlyListen = 1
    Both  = 2
   


class UdpSettings: 
    """
    Represents the UDP settings for a Stream.
    
    Attributes:
        host (str): The host IP address to connect to. Default is "127.0.0.1".
        port (int): The port number to connect to. Default is 28784.
        DataFlow (DataFlow): The data flow mode. Default is DataFlow.Both.
        socket (socket): The socket object used for the Stream.
        specificHost (str): The specific host IP address to bind to.
    """

    def __init__(self , host : str =  "localhost", port : int = 28784 , dataflow : DataFlow = DataFlow.Both , specificHost : bool = False) -> None:
        """
        Initializes a new instance of the UDPSettings class.
        
        Args:
            port (int, optional): The port number to connect to. Default is 28784.
            dataflow (DataFlow, optional): The data flow mode. Default is DataFlow.Both.
        """
        self.host : str = host
        self.port : int = port
        self.DataFlow : DataFlow = dataflow
        self.specificHost : bool  = specificHost
            



    def connect(self) -> socket.socket:
        """
        Connects to the specified host and port.
        
        Returns:
            socket.socket: The socket object used for the Stream.
        
        Raises:
            socket.error: If there is an error while connecting.
        """
        try : 
            newsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            newsocket.settimeout(5)
        except socket.error as e :
            raise e 
        try : 
            if self.specificHost is False:
                newsocket.bind(('', self.port))
            return newsocket
        except socket.error as e :
                    raise e


    def setHost(self, NewHost : str):
        """
        Sets the host IP address.
        
        Args:
            NewHost (str): The new host IP address.
        """
        self.host = NewHost

    def setPort(self, NewPort : int):
        """
        Sets the port number.
        
        Args:
            NewPort (int): The new port number.
        """
        self.port = NewPort
        
    def set_DataFlow(self, NewDataFlow : DataFlow):
        """
        Sets the Data flow.
        
        Args:
            NewDataFlow (DataFlow): The new Data Flow.
        """        
        self.DataFlow = NewDataFlow
        
        
    def toString(self) -> str : 
        """
        Return current class as a string

        Returns:
            str: class as string
        """
        return f" Host : {self.host} \n Port : {self.port} \n SpecificHost : {self.specificHost} \n DataFlow : {self.DataFlow.name}\n"
   
    def SaveConfig(self , sectionName : str,SaveConfigFile  : configparser.ConfigParser):
        """
            Add current class values in the configFile
        Args:
            sectionName (str): name of the current section
            SaveConfigFile (configparser.ConfigParser): configparser of the configuration file
        """
        SaveConfigFile.set(sectionName,"hostNameUDP", self.host )
        SaveConfigFile.set(sectionName,"portNumberUDP",str(self.port))
        SaveConfigFile.set(sectionName,"specificIpUDP",str(self.specificHost))
        SaveConfigFile.set(sectionName,"dataDirUDP",str(self.DataFlow.value))