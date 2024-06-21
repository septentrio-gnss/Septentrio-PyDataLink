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
import ssl
import logging
from .NtripSourceTable import NtripSourceTable
from ..constants import DEFAULTLOGFILELOGGER

class NtripSettingsException(Exception):
    """
        Exception class for ntrip settings 
    """
    def __init__(self, message, error_code = None):
        super().__init__(message)
        self.error_code = error_code

class InvalidHostnameError(NtripSettingsException):
    """Raised when invalid host name is given 
    """

class FailedHandshakeError(NtripSettingsException):
    """Raised when TLS Handshake failed with server
    """

class ConnectFailedError(NtripSettingsException):
    """Raised when creating a socket failed
    """

class NtripSettings:
    """
    Represents the TCP settings for a Stream.
    
    """

    def __init__(self , host : str = "" , port : int = 2101 ,
                 auth : bool = False, username : str = "" , password : str = "",
                 mountpoint : str = "" , tls : bool = False , fixed_pos : bool = False ,
                 latitude : float = 00.00 , longitude : float = 0.000 , height : int = 0 ,
                 debug_logging : bool  = False) -> None:
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

        self.ntrip_version : int = 2

        # Fixed Position GGA
        self.fixed_pos : bool = fixed_pos
        self.latitude : float = latitude
        self.longitude : float = longitude
        self.height : int = height

        self.source_table : list[NtripSourceTable] = []

        # Support Log
        if debug_logging :
            self.log_file : logging.Logger = DEFAULTLOGFILELOGGER
        else :
            self.log_file = None

    def connect(self):
        """Create the communication socket
        """
        if len(self.host) == 0:
            if self.log_file is not None :
                self.log_file.error("Invalid Hostname : hostname empty")
            raise InvalidHostnameError("Invalid Host Name or Host name Empty")
        if self.tls :
            ntrip_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if self.cert != "":
                context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
                context.load_verify_locations(self.cert)
            else :
                context = ssl.create_default_context()
            wrapped_socket = context.wrap_socket(ntrip_socket, server_hostname=self.host)
            wrapped_socket.settimeout(0.5)
            try:
                wrapped_socket.connect((self.host, self.port))
                return wrapped_socket
            except TimeoutError as e:
                if self.log_file is not None :
                    self.log_file.error("Error during the handshake for TLS connection : %s" ,  e)
                raise FailedHandshakeError("Error during the handshake") from e
            except Exception as e :
                if self.log_file is not None :
                    self.log_file.error("Failed to open TLS socket : %s", e)
                raise ConnectFailedError("Failed to open TLS socket") from e
        else :
            try:
                ntrip_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                ntrip_socket.connect((self.host, self.port))
                return ntrip_socket
            except Exception as e:
                if self.log_file is not None :
                    self.log_file.error("Failed to open socket : %s", e )
                raise ConnectFailedError("Failed to open communication socket") from e


    def set_host(self, new_host : str):
        """
        Sets the host IP address.
        
        Args:
            new_host (str): The new host IP address.
        """
        self.host = new_host

    def set_port(self, new_port : int):
        """
        Sets the port number.
        
        Args:
            new_port (int): The new port number.
        """
        self.port = new_port

    def set_mountpoint(self, new_mountpoint : str):
        """
        Sets the mountpoint.
        
        Args:
            new_mountpoint (str): The new mountpoint.
        """
        self.mountpoint = new_mountpoint

    def set_auth(self, new_auth : bool):
        """
        Sets the authentication.
        
        Args:
            new_auth (bool): The new authentication.
        """
        self.auth = new_auth

    def set_username(self, new_username : str):
        """
        Sets the username.
        
        Args:
            new_username (str): The new username.
        """
        self.username = new_username

    def set_password(self, new_password : str):
        """
        Sets the password.
        
        Args:
            new_password (str): The new password.
        """
        self.password = new_password

    def set_fixed_pos(self, new_fixed_pos : bool):
        """
        Sets the fixed position.
        
        Args:
            new_fixed_pos (bool): The new fixed position.
        """
        self.fixed_pos = new_fixed_pos

    def set_latitude(self, new_latitude : str):
        """
        Sets the latitude.
        
        Args:
            new_latitude (str): The new latitude.
        """
        if "S" in new_latitude :
            new_latitude = "-" + new_latitude.split("S ")[1]
        else :
            new_latitude = new_latitude.split("N ")[1]
        self.latitude = float(new_latitude)

    def set_longitude(self, new_longitude : str):
        """
        Sets the longitude.
        
        Args:
            new_longitude (str): The new longitude.
        """
        if "W" in new_longitude :
            new_longitude = "-" + new_longitude.split("W ")[1]
        else :
            new_longitude = new_longitude.split("E ")[1]
        self.longitude = float(new_longitude)

    def set_tls(self , new_tls : bool):
        """ Set the use of tls 
        """
        self.tls = new_tls

    def set_cert(self,new_cert):
        """Set the path to the certificate
        """
        self.cert = new_cert

    def get_latitude(self) -> str:
        """
        Gets the latitude.
        
        Returns:
            str: The latitude.
        """
        if self.latitude < 0 :
            return "S {:012.9f}".format(self.latitude)
        else :
            return "N {:012.9f}".format(self.latitude)

    def get_longitude(self) -> str :
        """
        Gets the longitude.
        
        Returns:
            str: The longitude.
        """
        if self.longitude < 0 :
            return "W {:013.9f}".format(self.longitude)
        else :
            return "E {:013.9f}".format(self.longitude)

    def set_height(self, new_height : int):
        """
        Sets the height.
        
        Args:
            new_height (int): The new height.
        """
        self.height = new_height
    def to_string(self) ->str :
        """Return settings as a single string
        """
        return f"Host : {self.host} \n Port : {self.port} \n Username : {self.username} \n Password : {self.password} \n Mountpoint : {self.mountpoint} \n"
