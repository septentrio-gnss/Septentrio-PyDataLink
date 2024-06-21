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

from src.StreamSettings import TcpSettings , UdpSettings
from src.StreamSettings.SerialSettings import SerialSettings ,  BaudRate, ByteSize, Parity, StopBits
from ..NTRIP import NtripClient, NtripSettings
from ..StreamConfig.Stream import StreamType , Stream

class CommandLineConfigurationException(Exception):
    """
        Exception class for CommandLine Configuration 
    """
    def __init__(self, message, error_code = None):
        super().__init__(message)
        self.error_code = error_code

class IncorrectStreamException(CommandLineConfigurationException):
    """Raised when the given stream type is not supported or incorect
    """
class ConfigurationException(CommandLineConfigurationException):
    """Raised when the configuration failed
    """
class PortLinkedException(CommandLineConfigurationException):
    """Raised when adding link to a stream failed
    """

class BeginStreamException(CommandLineConfigurationException):
    """Raised when the startup of the stream failed
    """

class MissingParameterException(CommandLineConfigurationException) :
    """Raised when a parameter is missing """

class InccorectParameterException(CommandLineConfigurationException) :
    """Raised when stream settings are incorrect """

def command_line_config(stream : Stream, command_line : str):
    """
    Configure a Stream with a single line of configuration 
    
    Args:
        command_line_config (str): Configuration line 

    """
    port_to_link = []
    try :
        stream_type :str = command_line.split("://")[0]
        config: str = command_line.split("://")[1]
        if '#' in config :
            port_to_link = config.split("#")[1].split(",")
            config = config.split("#")[0]
        if stream_type.lower() == "serial":
            config_serial_stream(stream , command_config=config)
        elif stream_type.lower() == "tcpcli":
            config_tcp_stream(stream ,is_server=False , command_config=config)
        elif stream_type.lower() == "tcpsrv":
            config_tcp_stream(stream ,is_server=True, command_config=config)
        elif stream_type.lower() == "udp":
            config_udp_stream(stream ,command_config=config)
        elif stream_type.lower() == "udpspe":
            config_udp_stream(stream ,specific_host=True, command_config= config)
        elif stream_type.lower() == "ntrip":
            config_ntrip_stream(stream ,config)
        else :
            raise IncorrectStreamException("Stream type not found or incorrect")
    except Exception as e  :
        raise ConfigurationException(f"Config line is incorrect : {e}") from e

    if len(port_to_link) > 0 :
        for i in port_to_link:
            try :
                link = int(i)
                if link != stream.id:
                    stream.linked_ports.append(link)
            except (TypeError, ValueError) as e :
                raise PortLinkedException(e) from e
    try:
        stream.connect(stream.stream_type)
    except Exception as e:
        raise BeginStreamException(e) from e

def config_ntrip_stream(stream : Stream ,command_config : str ):
    """
    Init a NTRIP Client with a configuration line

    Args:
        command_config (str): configuration line
    """
    credentials = command_config.split("@")[0].split(":")
    if len(credentials) != 2 :
        raise MissingParameterException("Missing a credential paremeter !")

    host = command_config.split("@")[1].split(":")
    if len(host) != 2:
        raise MissingParameterException("Missing a host paremeter !")

    mountpoint = command_config.split("@")[1].split("/")
    if len(mountpoint) != 2:
        raise MissingParameterException("Missing a MountPoint paremeter !")

    try :
        settings = NtripSettings(host = host[0], port = int(host[1].split("/")[0]),
                                 auth= (True if len(credentials[0]) > 0 and len(credentials[1]) > 0  else False),
                                 username= credentials[0],password= credentials[1],
                                 mountpoint=mountpoint[1])
        stream.ntrip_client = NtripClient(settings)
        stream.stream_type = StreamType.NTRIP
    except Exception as e :
        raise InccorectParameterException(f"Parameters for a NTRIP Client stream are incorrect : \n{e}") from e

def config_udp_stream(stream : Stream,specific_host : bool = False, command_config : str = None):
    """
        Init a UDP stream with a configuration line
    Args:
        specific_host (bool, optional): if True the UDP Stream will stream only to a specific host name. Defaults to False.
        command_config (str, optional): Configuration line. Defaults to None.

    Raises:
        Exception: too few or too much parameter
        Exception: Given parameter incorrect 
        Exception: Given parameter incorrect (Specific host)
    """
    if specific_host :
        config = command_config.split(":")[0]
        if len(config) != 2 :
            if len(config) > 2 :
                raise MissingParameterException("Too much parameters for a UDP Stream") 
            else : 
                raise MissingParameterException("Not enough parameters for a UDP Stream")
        else :
            try:
                stream.udp_settings = UdpSettings.UdpSettings(host=config[0],  port=int(config[1]), specific_host=specific_host)
                stream.stream_type = StreamType.UDP
            except Exception as e :
                raise InccorectParameterException(f"Parameters for a UDP stream are incorrect : \n{e}") from e
    else :
        try:
            stream.udp_settings = UdpSettings.UdpSettings(port=int(command_config))
            stream.stream_type = StreamType.UDP
        except Exception as e :
            raise InccorectParameterException(f"Parameter for a UDP stream are incorrect : \n{e}") from e

def config_tcp_stream(stream : Stream,is_server : bool = False ,command_config : str= None) -> None:
    """
        Init a TCP stream with a configuration line
    Args:
        is_server (bool, optional): If True the TCP stream will be configure as a Server. Defaults to False.
        command_config (str, optional): Configuration line . Defaults to None.

    Raises:
        Exception: too few or too much parameter
        Exception: Given parameter incorrect (Server)
        Exception: Given parameter incorrect (Client)
    """
    if is_server :
        config = command_config.split(":")
        if len(config) != 2 :
            if len(config) > 2 :
                raise MissingParameterException("Too much parameters for a TCP Stream") 
            else :
                raise MissingParameterException("Not enough parameters for a TCP Stream")
        try :
            stream.tcp_settings = TcpSettings.TcpSettings(host=config[0] , port=int(config[1]), stream_mode= TcpSettings.StreamMode.SERVER)        
        except Exception as e :
            raise InccorectParameterException(f"Parameters for a TCP Server stream are incorrect : \n{e}") from e
    else :
        try :
            stream.tcp_settings = TcpSettings.TcpSettings(port=int(command_config) , stream_mode= TcpSettings.StreamMode.CLIENT)
        except Exception as e :
            raise InccorectParameterException(f"Parameters for a TCP Client stream are incorrect : \n{e}") from e
    stream.stream_type = StreamType.TCP

def config_serial_stream(stream : Stream,command_config :str) -> None:
    """
        Init a Serial stream with a configuration line
        exemple : 
    Args:
        command_config (str): Configuration line

    Raises:
        Exception: If too few argument for a proper configuration
        Exception: If given argument are Incorrect
    """
    config = command_config.split(":")
    if len(config) != 6 :
        if len(config) > 6 :
            raise MissingParameterException("Too much parameters for a Serial Stream") 
        else:
            raise MissingParameterException("Not enough parameters for a Serial Stream")

    port : str = config[0]
    try :
            baudrate : BaudRate = BaudRate(config[1])
    except : 
            baudrate : BaudRate = BaudRate.eBAUD115200
    try :
            parity : Parity = Parity(config[2])
    except : 
            parity : Parity = Parity.PARITY_NONE
    try :
            stopbits : StopBits = StopBits(config[3])
    except :
            stopbits : StopBits = StopBits.STOPBITS_ONE
    try :
            bytesize : ByteSize= ByteSize(config[4])
    except : 
            bytesize : ByteSize = ByteSize.EIGHTBITS

    rtscts : bool = True if config[5] == "1" else False
    try :
        stream.serial_settings = SerialSettings(port  = port , baudrate=baudrate , parity=parity , stopbits=stopbits,bytesize=bytesize , rtscts=rtscts)
        stream.stream_type = StreamType.Serial
    except Exception as e :
        raise InccorectParameterException(f"Parameters for a Serial stream are incorrect : \n{e}") from e