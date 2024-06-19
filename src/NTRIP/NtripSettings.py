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

import socket
from .NtripSourceTable import NtripSourceTable
import ssl
import logging
from ..constants import DEFAULTLOGFILELOGGER


class InvalidHostnameError(Exception):
    def __init__(self, message = "Invalid Hostname", errors = "NTRIPSettings 1"):            
        super().__init__(message)
        self.errors = errors

class FailedHandshakeError(Exception):
    def __init__(self, message = "TLS connection Failed", errors = "NTRIPSettings 2"):            
        super().__init__(message)
        self.errors = errors

class ConnectFailedError(Exception):
    def __init__(self, message = "Connection to server Failed", errors = "NTRIPSettings 3"):            
        super().__init__(message)
        self.errors = errors

class NtripSettings: 
    """
    Represents the TCP settings for a Stream.
    
    """

    def __init__(self , host : str = "" , port : int = 2101 ,auth : bool = False, username : str = "" , password : str = "",
                 mountpoint : str = "" , tls : bool = False , fixedPos : bool = False , latitude : float = 00.00 , longitude : float = 0.000 , height : int = 0 , debugLogging : bool  = False) -> None:
        """
        Initializes a new instance of the NTRIPSettings class.
        """
        self.host : str = host
        self.port : int = port
        self.mountpoint : str = mountpoint
            
        self.auth : bool = auth
            
        self.username: str = username
        self.password :str = password
        self.tls : bool = tls 
        self.cert : str = ""
        
        self.ntripVersion : int = 2

        # Fixed Position GGA
        self.fixedPos : bool = fixedPos
        self.latitude : float = latitude
        self.longitude : float = longitude
        self.height : int = height
            
        self.sourceTable : list[NtripSourceTable] = []
        
        # Support Log
        if debugLogging : 
            self.logFile : logging.Logger = DEFAULTLOGFILELOGGER
        else :
            self.logFile = None
            
    def connect(self):    
            if len(self.host) == 0:
                if self.logFile is not None : 
                    self.logFile.error("Invalid Hostname : hostname empty")
                raise InvalidHostnameError()            
            if self.tls : 
                ntripsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                if self.cert != "":
                        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
                        context.load_verify_locations(self.cert)
                else :
                        context = ssl.create_default_context()
                wrappedSocket = context.wrap_socket(ntripsocket, server_hostname=self.host)
                wrappedSocket.settimeout(0.5)
                try:
                    wrappedSocket.connect((self.host, self.port))
                    return wrappedSocket
                except TimeoutError as e:
                    if self.logFile is not None :
                        self.logFile.error("Error during the handshake for TLS connection : %s" ,  e)
                    raise FailedHandshakeError()
                except Exception as e :
                    if self.logFile is not None : 
                        self.logFile.error("Failed to open TLS socket : %s", e)
                    raise e 
            else : 
                try:
                    ntripsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    ntripsocket.connect((self.host, self.port))
                    return ntripsocket
                except Exception as e:
                    if self.logFile is not None :
                        self.logFile.error("Failed to open socket : %s", e )
                    raise ConnectFailedError()


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

    def setMountpoint(self, NewMountpoint : str):
        """
        Sets the mountpoint.
        
        Args:
            NewMountpoint (str): The new mountpoint.
        """
        self.mountpoint = NewMountpoint
    
    def setAuth(self, Newauth : bool):
        """
        Sets the authentication.
        
        Args:
            Newauth (bool): The new authentication.
        """
        self.auth = Newauth
    
    def setUsername(self, NewUsername : str):
        """
        Sets the username.
        
        Args:
            NewUsername (str): The new username.
        """
        self.username = NewUsername
    
    def setPassword(self, NewPassword : str):
        """
        Sets the password.
        
        Args:
            NewPassword (str): The new password.
        """
        self.password = NewPassword
    
    def setFixedPos(self, NewFixedPos : bool):
        """
        Sets the fixed position.
        
        Args:
            NewFixedPos (bool): The new fixed position.
        """
        self.fixedPos = NewFixedPos

    def setLatitude(self, NewLatitude : str):
        """
        Sets the latitude.
        
        Args:
            NewLatitude (str): The new latitude.
        """
        if "S" in NewLatitude :
            NewLatitude = "-" + NewLatitude.split("S ")[1]
        else :
            NewLatitude = NewLatitude.split("N ")[1]
        self.latitude = float(NewLatitude)
        
    def setLongitude(self, NewLongitude : str):
        """
        Sets the longitude.
        
        Args:
            NewLongitude (str): The new longitude.
        """
        if "W" in NewLongitude :
            NewLongitude = "-" + NewLongitude.split("W ")[1]
        else :
            NewLongitude = NewLongitude.split("E ")[1]
        self.longitude = float(NewLongitude)
        
    def setTls(self , newTls):
        self.tls = newTls
        
    def setCert(self,newcert):
        self.cert = newcert
        
    def getLatitude(self) -> str:
        """
        Gets the latitude.
        
        Returns:
            str: The latitude.
        """
        if self.latitude < 0 :
            return "S {:012.9f}".format(self.latitude)
        else :
            return "N {:012.9f}".format(self.latitude)
        
    def getLongitude(self) -> str :
        """
        Gets the longitude.
        
        Returns:
            str: The longitude.
        """
        if self.longitude < 0 :
            return "W {:013.9f}".format(self.longitude)
        else :
            return "E {:013.9f}".format(self.longitude)
        
    def setHeight(self, NewHeight : int):
        """
        Sets the height.
        
        Args:
            NewHeight (int): The new height.
        """
        self.height = NewHeight
    def toString(self) ->str :
        return f"Host : {self.host} \n Port : {self.port} \n Username : {self.username} \n Password : {self.password} \n Mountpoint : {self.mountpoint} \n"
    
    