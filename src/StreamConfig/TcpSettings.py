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


class StreamMode(Enum):
    CLIENT = "Client"
    SERVER = "Server"


class TcpSettings: 
    """
    Represents the TCP settings for a stream.
    
    """

    def __init__(self , host : str = "localhost" , port : int =28784 , streamMode : StreamMode = StreamMode.CLIENT) -> None:
            self.host : str = host
            self.port : int = port
            self.StreamMode : StreamMode = streamMode
            if self.StreamMode == StreamMode.SERVER : 
                self.host = ''
       


    def connect(self) -> socket.socket:
        """
        Connects to the specified host and port.
        
        Returns:
            socket.socket: The socket object used for the Stream.
        
        Raises:
            socket.error: If there is an error while connecting.
        """
        try : 
            newsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            newsocket.settimeout(5)
        except socket.error as e :
            raise e 
        match self.StreamMode : 
            case StreamMode.CLIENT :
                try : 
                    newsocket.connect((self.host, self.port))
                    return newsocket
                except socket.error as e :
                    raise e
            case StreamMode.SERVER :
                try : 
                    newsocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    newsocket.bind(('', self.port))
                    return newsocket
                except socket.error as e :
                    raise e


    def setHost(self, NewHost : str):
        """
        set the Host name of the TCP Stream
        
        Args:
            NewHost (str): the new Host name
        """
        self.host = NewHost

    def setPort(self, NewPort : int):
        """
        set the Port of the TCP Stream

        Args:
            NewPort (int): The new Port 
        """
        self.port = NewPort

    def set_StreamMode(self, NewMode : StreamMode):
        """
        set the stream mode of the tcp stream.
        Args:
            NewMode (StreamMode): The new stream mode.
        """
        self.StreamMode = NewMode
        
    def isServer(self):
        """
        Return current stream mode of the stream
        Returns:
            Bool : True if the current Stream is in Server mode , False otherwise
        """
        return True if self.StreamMode == StreamMode.SERVER else False
        
    def toString(self) -> str :
        """
        Return current class as a string

        Returns:
            str: class as string
        """
        return f" Host : {self.host} \n Port :{self.port} \n StreamMode : {self.StreamMode.value}"
    
    
    def SaveConfig(self , sectionName : str,SaveConfigFile  : configparser.ConfigParser):
        """
            Add current class values in the configFile
        Args:
            sectionName (str): name of the current section
            SaveConfigFile (configparser.ConfigParser): configparser of the configuration file
        """
        SaveConfigFile.set(sectionName,"hostName",self.host)
        SaveConfigFile.set(sectionName,"portNumber",str(self.port))
        SaveConfigFile.set(sectionName,"TCPserver",str(self.isServer()))