
import base64
import configparser
from ..NTRIP import *
from ..StreamSettings.UdpSettings import *
from ..StreamSettings.SerialSettings import *
from ..StreamSettings.TcpSettings import *
from ..StreamConfig.Stream import StreamType , Stream
from ..StreamConfig.Preferences import Preferences


def conf_file_preference(preference : Preferences ,conf_file : configparser.SectionProxy) :
    """
        Configure preferences value with data form a config file
    """
    if preference is None :
        raise Exception("need a preference to be configured")
    try :
        preference.max_streams =  int(conf_file.get("numberOfPortPanels"))
    except :
        pass
    for connectid in range(preference.max_streams):
        try :
            preference.connect[connectid] = ( True if conf_file.get(f"connect{connectid}").lower() == "true" else False )
        except :
            pass
    try : 
        preference.line_termination  = conf_file.get("linetermination").replace("\\n","\n").replace("\\r","\r")
    except : 
        pass
    try: 
        if len(conf_file.get("configname")) != 0 : 
            preference.config_name = str(conf_file.get("configname"))
    except : 
        pass
            
def conf_file_config(stream : Stream ,conf_file : configparser.SectionProxy) :
    """
    Init a stream and it's settings with a configuration file 
    
    Args:
        conf_file (configparser.SectionProxy): section of a stream in a configuration file
    """
    if stream is None :
        raise Exception('need a stream to be configured')
    
    stream.serial_settings = conf_file_serial(conf_file, stream.debug_logging)
    stream.tcp_settings= conf_file_tcp(conf_file , stream.debug_logging)
    
    stream.udp_settings = conf_file_udp(conf_file ,  stream.debug_logging )
    stream.ntrip_client = conf_file_ntrip_client(conf_file ,  stream.debug_logging )
    try :
        
        stream.stream_type = StreamType(int(conf_file.get("connectionType")))
    except :
        stream.stream_type = StreamType.NONE
    links = conf_file.get("linksChecked").replace("[","").replace(" ","").replace("]","").split(",")
    for link in links:
        if link != '':
            stream.linked_ports.append(int(link))
    stream.startup_script = conf_file.get("startupscriptfile")
    try :
        stream.send_startup_script = True if conf_file.get("startupscript").lower() == "true" else False
    except :
        stream.send_startup_script = False
    stream.close_script = conf_file.get("closescriptfile")
    try :
        stream.send_close_script = True if conf_file.get("closescript").lower() == "true" else False
    except : 
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
    except : 
        baudrate : BaudRate = BaudRate.eBAUD115200
    try :    
        parity : Parity = Parity(conf_file.get('Serial.Parity'))
    except : 
        parity : Parity = Parity.PARITY_NONE
    try : 
        stopbits : StopBits = StopBits(conf_file.get('Serial.StopBits') )
    except :
        stopbits : StopBits = StopBits.STOPBITS_ONE
    try :
        bytesize : ByteSize= ByteSize(conf_file.get('Serial.ByteSize'))
    except : 
        bytesize : ByteSize = ByteSize.EIGHTBITS
    try : 
        rtscts : bool = True if conf_file.get('Serial.RtcCts').lower() == "true" else False
    except :
        rtscts = False
    return SerialSettings(port = port , baudrate=baudrate , parity=parity ,
                          stopbits=stopbits,bytesize=bytesize , rtscts=rtscts,debug_logging=debug_logging)

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
    except :
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
    except : 
        port = 28784
    try: 
        dataflow : DataFlow = DataFlow(conf_file.get('dataDirUDP'))
    except :
        dataflow : DataFlow = DataFlow.BOTH
    try  :
        specific_host : bool  = True if conf_file.get('specificIpUDP').lower() == "true" else False
    except : 
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
    except:
        port = 2101
    mountpoint : str = conf_file.get('NTRIP.mountPoint')
    try :
        auth : bool = True if conf_file.get('NTRIP.authenticationenabled').lower() == "true" else False
    except : 
        auth = False
    username : str = conf_file.get('NTRIP.user')
    try :
        password : str = base64.b64decode((conf_file.get('NTRIP.password')).encode()).decode()
    except : 
        password : str = ""
    try :
        tls : bool = True if conf_file.get('NTRIP.TLS').lower() == "true" else False
    except : 
        tls = False
    try :
        fixed_pos : bool = True if conf_file.get('NTRIP.fixedpositionset').lower() == "true" else False
    except : 
        fixed_pos = False

    try :
        latitude : float = float(conf_file.get('NTRIP.fixedlatitude'))
    except :
        latitude = 00.000000000
    try :
        longitude : float = float(conf_file.get('NTRIP.fixedlongitude'))
    except :
        longitude = 000.000000000
    try :
        height : int = int(conf_file.get('NTRIP.fixedheight'))
    except :
        height = 0


    return NtripClient(host=host , port=port , auth=auth , username=username , password= password,
                       mountpoint=mountpoint, tls= tls ,fixed_pos=fixed_pos , latitude = latitude ,
                       longitude = longitude , height = height , debug_logging= debug_logging )
