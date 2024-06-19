

from ..NTRIP import *
from ..StreamSettings.UdpSettings import *
from ..StreamSettings.SerialSettings import *
from ..StreamSettings.TcpSettings import *
from ..StreamConfig.Stream import StreamType , Stream

def command_line_config(stream : Stream,command_line_config : str):
    """
    Configure a Stream with a single line of configuration 
    
    Args:
        command_line_config (str): Configuration line 

    """
    port_to_link = []
    try :
        stream_type :str = command_line_config.split("://")[0]
        config: str = command_line_config.split("://")[1]
        if '#' in config :
            port_to_link = config.split("#")[1].split(",")
            config = config.split("#")[0]
        if stream_type.lower() == "serial":
            ConfigSerialStream(stream , commandConfig=config)
        elif stream_type.lower() == "tcpcli":
            ConfigTCPStream(stream ,is_server=False , commandConfig=config)
        elif stream_type.lower() == "tcpsrv":
            ConfigTCPStream(stream ,is_server=True, commandConfig=config)
        elif stream_type.lower() == "udp":
            ConfigUDPStream(stream ,commandConfig=config)
        elif stream_type.lower() == "udpspe":
            ConfigUDPStream(stream ,specific_host=True, commandConfig= config)
        elif stream_type.lower() == "ntrip":
            ConfigNTRIPStream(stream ,config)

    except Exception as e  :
        raise Exception(f"config line is not correct ! , {e}")

    if len(port_to_link) > 0 :
        for i in port_to_link:
            try :
                link = int(i)
                if link != stream.id:
                    stream.linked_ports.append(link)
            except : pass
    try:
        stream.connect(stream.stream_type)
    except Exception as e:
        raise e

def ConfigNTRIPStream(stream : Stream ,CommandConfig : str ):
    """
    Init a NTRIP Client with a configuration line

    Args:
        CommandConfig (str): configuration line
    """
    credentials = CommandConfig.split("@")[0].split(":")
    if len(credentials) != 2 :
        raise Exception("Missing a credential paremeter !")
    
    host = CommandConfig.split("@")[1].split(":")
    if len(host) != 2:
        raise Exception("Missing a host paremeter !")
    
    mountpoint = CommandConfig.split("@")[1].split("/")
    if len(mountpoint) != 2:
        raise Exception("Missing a MountPoint paremeter !")
    
    try : 
        stream.ntrip_client = NtripClient(host = host[0], port = int(host[1].split("/")[0]), auth= (True if len(credentials[0]) > 0 and len(credentials[1]) > 0  else False) ,username= credentials[0],password= credentials[1],mountpoint=mountpoint[1])
        stream.stream_type = StreamType.NTRIP
    except Exception as e : 
        raise Exception(f"Error : given parameters for a NTRIP Client stream are incorrect : \n{e}")
    
def ConfigUDPStream(stream : Stream,specific_host : bool = False, commandConfig : str = None):
    """
        Init a UDP stream with a configuration line
    Args:
        specific_host (bool, optional): if True the UDP Stream will stream only to a specific host name. Defaults to False.
        commandConfig (str, optional): Configuration line. Defaults to None.

    Raises:
        Exception: too few or too much parameter
        Exception: Given parameter incorrect 
        Exception: Given parameter incorrect (Specific host)
    """
    if specific_host :
        config = commandConfig.split(":")[0]
        if len(config) != 2 : 
            raise Exception("Error : too few or too much parameter") 
        else :
            try:
                stream.udp_settings = UdpSettings(host=config[0],  port=int(config[1]), specific_host=specific_host)
                stream.stream_type = StreamType.UDP
            except Exception as e : 
                raise Exception("Error : given parameter for a UDP stream are incorrect : \n{e}")
    else :
        try:
            stream.udp_settings = UdpSettings(port=int(commandConfig))
            stream.stream_type = StreamType.UDP
        except Exception as e : 
            raise Exception("Error : given parameter for a UDP stream are incorrect : \n{e}")      
    
def ConfigTCPStream(stream : Stream,is_server : bool = False ,commandConfig : str = None) -> None:
    """
        Init a TCP stream with a configuration line
    Args:
        is_server (bool, optional): If True the TCP stream will be configure as a Server. Defaults to False.
        commandConfig (str, optional): Configuration line . Defaults to None.

    Raises:
        Exception: too few or too much parameter
        Exception: Given parameter incorrect (Server)
        Exception: Given parameter incorrect (Client)
    """
    if is_server : 
        config = commandConfig.split(":")
        if len(config) != 2 : 
            raise Exception("Error : too few or too much parameter") 
        try : 
            stream.tcp_settings = TcpSettings(host=config[0] , port=int(config[1]), stream_mode= StreamMode.SERVER)        
        except Exception as e : 
            raise Exception("Error : given parameters for a TCP Server stream are incorrect : \n{e}")   
    else : 
        try : 
            stream.tcp_settings = TcpSettings(port=int(commandConfig) , stream_mode= StreamMode.CLIENT)
        except Exception as e : 
            raise Exception("Error : given parameters for a TCP Client stream are incorrect : \n{e}")   
    stream.stream_type = StreamType.TCP
    
def ConfigSerialStream(stream : Stream,commandConfig :str) -> None:
    """
        Init a Serial stream with a configuration line
        exemple : 
    Args:
        commandConfig (str): Configuration line

    Raises:
        Exception: If too few argument for a proper configuration
        Exception: If given argument are Incorrect
    """
    config = commandConfig.split(":")
    if len(config) != 6 :
        raise Exception("Error : too few or too much parameter") 
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
        raise Exception("Error : given parameters for a Serial stream are incorrect : \n{e}")   