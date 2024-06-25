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

import base64
import configparser
from ..NTRIP import NtripSettings , NtripClient
from ..StreamSettings.TcpSettings import StreamMode , TcpSettings
from ..StreamSettings.UdpSettings import DataFlow , UdpSettings
from ..StreamSettings.SerialSettings import ByteSize, Parity, BaudRate, StopBits , SerialSettings
from ..StreamConfig.Stream import StreamType , Stream
from ..StreamConfig.Preferences import Preferences


class FileConfigurationException(Exception):
    """
        Exception class for File Configuration 
    """
    def __init__(self, message, error_code = None):
        super().__init__(message)
        self.error_code = error_code
        
class PreferencesMissingException(FileConfigurationException):
    """Raised when the preference parameter is none
    """
class StreamMissingException(FileConfigurationException):
    """Raised when the stream parameter is none
    """

def conf_file_preference(preference : Preferences ,conf_file : configparser.SectionProxy) :
    """
        Configure preferences value with data form a config file
    """
    if preference is None :
        raise PreferencesMissingException("the preference can't be empty")
    try :
        preference.max_streams =  int(conf_file.get("numberOfPortPanels"))
    except (TypeError, ValueError):
        pass
    for connectid in range(preference.max_streams):
        try :
            preference.connect[connectid] = ( True if conf_file.get(f"connect{connectid}").lower() == "true" else False )
        except (TypeError, ValueError) :
            pass
    try :
        preference.line_termination  = str(conf_file.get("linetermination")).replace("\\n","\n").replace("\\r","\r")
    except (TypeError, ValueError) :
        pass
    try:
        if len(conf_file.get("configname")) != 0 :
            preference.config_name = str(conf_file.get("configname"))
    except  (TypeError, ValueError):
        pass

def conf_file_config(stream : Stream ,conf_file : configparser.SectionProxy) :
    """
    Init a stream and it's settings with a configuration file 
    
    Args:
        conf_file (configparser.SectionProxy): section of a stream in a configuration file
    """
    if stream is None :
        raise StreamMissingException('need a stream to be configured')

    stream.serial_settings = conf_file_serial(conf_file, stream.debug_logging)
    stream.tcp_settings= conf_file_tcp(conf_file , stream.debug_logging)
    stream.udp_settings = conf_file_udp(conf_file ,  stream.debug_logging )
    stream.ntrip_client = conf_file_ntrip_client(conf_file ,  stream.debug_logging )
    try :

        stream.stream_type = StreamType(int(conf_file.get("connectionType")))
    except (TypeError, ValueError):
        stream.stream_type = StreamType.NONE
    links = str(conf_file.get("linksChecked")).replace("[","").replace(" ","").replace("]","").split(",")
    for link in links:
        if link != '':
            stream.linked_ports.append(int(link))
    stream.startup_script = conf_file.get("startupscriptfile")
    try :
        stream.send_startup_script = True if str(conf_file.get("startupscript")).lower() == "true" else False
    except (TypeError, ValueError):
        stream.send_startup_script = False
    stream.close_script = conf_file.get("closescriptfile")
    try :
        stream.send_close_script = True if str(conf_file.get("closescript")).lower() == "true" else False
    except (TypeError, ValueError): 
        stream.send_close_script = False
    stream.logging_file = conf_file.get("logfile")
    if stream.logging_file != "":
        stream.logging = True
    
def conf_file_serial(conf_file :configparser.SectionProxy, debug_logging :bool):
    """
    Init Serial settings of the current stream with value from a configuration file.
    If no value in configuration file , default value will be use

    Args:
        conf_file (configparser.SectionProxy): configuration file 

    Returns:
        SerialSetting: return a new SerialSettings
    """
    port : str = conf_file.get('Serial.Port')
    try :
        baudrate : BaudRate = BaudRate(conf_file.get('Serial.BaudRate'))
    except (TypeError, ValueError):
        baudrate : BaudRate = BaudRate.eBAUD115200
    try :
        parity : Parity = Parity(conf_file.get('Serial.Parity'))
    except (TypeError, ValueError) :
        parity : Parity = Parity.PARITY_NONE
    try :
        stopbits : StopBits = StopBits(conf_file.get('Serial.StopBits') )
    except (TypeError, ValueError):
        stopbits : StopBits = StopBits.STOPBITS_ONE
    try :
        bytesize : ByteSize= ByteSize(conf_file.get('Serial.ByteSize'))
    except (TypeError, ValueError):
        bytesize : ByteSize = ByteSize.EIGHTBITS
    try :
        rtscts : bool = True if conf_file.get('Serial.RtcCts').lower() == "true" else False
    except (TypeError, ValueError):
        rtscts = False
    return SerialSettings(port = port , baudrate=baudrate , parity=parity ,
                          stopbits=stopbits,bytesize=bytesize ,
                          rtscts=rtscts,debug_logging=debug_logging)

def conf_file_tcp(conf_file : configparser.SectionProxy, debug_logging : bool):
    """
    Init TCP settings of the current stream with value from a configuration file.
    If no value in configuration file , default value will be use

    Args:
        conf_file (configparser.SectionProxy): configuration file 

    Returns:
        TcpSettings: return a new TcpSettings
    """
    host : str = conf_file.get('hostName')
    try :
        port : int = int(conf_file.get('portNumber'))
    except (TypeError, ValueError) :
        port = 28784

    if bool(True if str(conf_file.get('TCPserver')).lower() == "true" else False ) is True :
        host = ''
        stream_mode = StreamMode.SERVER
    else:
        stream_mode = StreamMode.CLIENT

    return TcpSettings(host= host , port= port ,
                       stream_mode = stream_mode , debug_logging=debug_logging)

def conf_file_udp(conf_file : configparser.SectionProxy, debug_logging : bool):
    """
    Init UDP settings of the current stream with value from a configuration file.
    If no value in configuration file , default value will be use

    Args:
        conf_file (configparser.SectionProxy): configuration file 

    Returns:
        UdpSettings: return a new udpsettings
    """
    host : str = conf_file.get('hostNameUDP')
    try :
        port : int = int(conf_file.get('portNumberUDP'))
    except (TypeError, ValueError):
        port = 28784
    try:
        dataflow : DataFlow = DataFlow(conf_file.get('dataDirUDP'))
    except (TypeError, ValueError):
        dataflow : DataFlow = DataFlow.BOTH
    try  :
        specific_host : bool  = True if conf_file.get('specificIpUDP').lower() == "true" else False
    except (TypeError, ValueError):
        specific_host = False

    return UdpSettings(host=host,port=port , dataflow=dataflow,
                       specific_host=specific_host , debug_logging = debug_logging )

def conf_file_ntrip_client(conf_file : configparser.SectionProxy , debug_logging : bool):
    """
    Init a Ntrip client with value from a configuration file.
    If no value in configuration file , default value will be use

    Args:
        conf_file (configparser.SectionProxy): configuration file 

    Returns:
        NtripClient: return a new ntrip
    """
    host : str = conf_file.get('NTRIP.hostname')
    try :
        port : int = int(conf_file.get('NTRIP.portnumber'))
    except  (TypeError, ValueError):
        port = 2101
    mountpoint : str = conf_file.get('NTRIP.mountPoint')
    try :
        auth : bool = True if conf_file.get('NTRIP.authenticationenabled').lower() == "true" else False
    except  (TypeError, ValueError):
        auth = False
    username : str = conf_file.get('NTRIP.user')
    try  :
        password : str = base64.b64decode((conf_file.get('NTRIP.password')).encode()).decode()
    except  (TypeError, ValueError):
        password : str = ""
    try :
        tls : bool = True if conf_file.get('NTRIP.TLS').lower() == "true" else False
    except  (TypeError, ValueError):
        tls = False
    try :
        fixed_pos : bool = True if conf_file.get('NTRIP.fixedpositionset').lower() == "true" else False
    except  (TypeError, ValueError):
        fixed_pos = False

    try :
        latitude : float = float(conf_file.get('NTRIP.fixedlatitude'))
    except  (TypeError, ValueError):
        latitude = 00.000000000
    try :
        longitude : float = float(conf_file.get('NTRIP.fixedlongitude'))
    except  (TypeError, ValueError):
        longitude = 000.000000000
    try :
        height : int = int(conf_file.get('NTRIP.fixedheight'))
    except  (TypeError, ValueError) :
        height = 0

    settings = NtripSettings(host=host , port=port , auth=auth ,
                            username=username , password= password,
                            mountpoint=mountpoint, tls= tls ,fixed_pos=fixed_pos ,
                            latitude = latitude ,longitude = longitude ,
                            height = height , debug_logging= debug_logging )

    return NtripClient( ntrip_settings= settings ,debug_logging=debug_logging )
