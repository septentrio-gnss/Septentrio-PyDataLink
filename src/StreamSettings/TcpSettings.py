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
import logging
from enum import Enum
from ..constants import DEFAULTLOGFILELOGGER


class TCPSettingsException(Exception):
    """
        Exception class for tcp settings 
    """
    def __init__(self, message, error_code = None):
        super().__init__(message)
        self.error_code = error_code


class StreamMode(Enum):
    """ Stream mode of the TCP port
    """
    CLIENT = "Client"
    SERVER = "Server"


class TcpSettings:
    """
    Represents the TCP settings for a stream.
    
    """

    def __init__(self , host : str = "localhost" , port : int =28784 ,
                 stream_mode : StreamMode = StreamMode.CLIENT ,
                 debug_logging : bool =False) -> None:

        self.host : str = host
        self.port : int = port
        self.stream_mode : StreamMode = stream_mode
        if self.stream_mode == StreamMode.SERVER :
            self.host = ''

        if debug_logging :
            self.log_file : logging.Logger = DEFAULTLOGFILELOGGER
        else :
            self.log_file = None # type: ignore



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
            if self.log_file is not None :
                self.log_file.error("Failed to start socket : %s" , e)
            raise TCPSettingsException(e) from e
        match self.stream_mode :
            case StreamMode.CLIENT :
                try :
                    newsocket.connect((self.host, self.port))
                    return newsocket
                except socket.error as e :
                    if self.log_file is not None :
                        self.log_file.error("Failed to open the Client socket ( host : %s and port : %s) : %s",self.host , self.port , e)
                    raise TCPSettingsException(e) from e
            case StreamMode.SERVER :
                try :
                    newsocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    newsocket.bind(('', self.port))
                    return newsocket
                except socket.error as e :
                    if self.log_file is not None :
                        self.log_file.error("Failed to open the Server socket : %s" , e)
                    raise TCPSettingsException(e) from e


    def set_host(self, new_host : str):
        """
        set the Host name of the TCP Stream
        
        Args:
            new_host (str): the new Host name
        """
        self.host = new_host

    def set_port(self, new_port : int):
        """
        set the Port of the TCP Stream

        Args:
            new_port (int): The new Port 
        """
        self.port = new_port

    def set_stream_mode(self, new_mode : StreamMode):
        """
        set the stream mode of the tcp stream.
        Args:
            new_mode (StreamMode): The new stream mode.
        """
        self.stream_mode = new_mode

    def is_server(self):
        """
        Return current stream mode of the stream
        Returns:
            Bool : True if the current Stream is in Server mode , False otherwise
        """
        return True if self.stream_mode == StreamMode.SERVER else False

    def to_string(self) -> str :
        """
        Return current class as a string

        Returns:
            str: class as string
        """
        return f" Host : {self.host} \n Port :{self.port} \n StreamMode : {self.stream_mode.value}"