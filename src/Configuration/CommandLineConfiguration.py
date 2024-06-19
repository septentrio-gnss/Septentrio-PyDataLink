

from ..NTRIP import *
from ..StreamSettings.UdpSettings import *
from ..StreamSettings.SerialSettings import *
from ..StreamSettings.TcpSettings import *
from ..StreamConfig.Stream import StreamType , Stream

def CommandLineConfig(stream : Stream,commandLineConfig : str):
    """
    Configure a Stream with a single line of configuration 
    
    Args:
        commandLineConfig (str): Configuration line 

    """
    PortToLink = []
    try :
            streamType :str = commandLineConfig.split("://")[0]
            config: str = commandLineConfig.split("://")[1]
            if '#' in config : 
                PortToLink = config.split("#")[1].split(",")
                config = config.split("#")[0]
            if streamType.lower() == "serial":
                ConfigSerialStream(stream , commandConfig=config)
            elif streamType.lower() == "tcpcli":
                ConfigTCPStream(stream ,isServer=False , commandConfig=config)
            elif streamType.lower() == "tcpsrv":
                ConfigTCPStream(stream ,isServer=True, commandConfig=config)
            elif streamType.lower() == "udp":
                ConfigUDPStream(stream ,commandConfig=config)
            elif streamType.lower() == "udpspe":
                ConfigUDPStream(stream ,specificHost=True, commandConfig= config)
            elif streamType.lower() == "ntrip":
                ConfigNTRIPStream(stream ,config)
                
    except Exception as e  : 
            raise Exception(f"config line is not correct ! , {e}")

    if len(PortToLink) > 0 :
        for i in PortToLink:
            try :
                link = int(i)
                if link != stream.id:
                    stream.linkedPort.append(link)
            except :
                pass
    try:
        stream.Connect(stream.StreamType)
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
        stream.ntripClient = NtripClient(host = host[0], port = int(host[1].split("/")[0]), auth= (True if len(credentials[0]) > 0 and len(credentials[1]) > 0  else False) ,username= credentials[0],password= credentials[1],mountpoint=mountpoint[1])
        stream.StreamType = StreamType.NTRIP
    except Exception as e : 
        raise Exception(f"Error : given parameters for a NTRIP Client stream are incorrect : \n{e}")
    
def ConfigUDPStream(stream : Stream,specificHost : bool = False, commandConfig : str = None):
    """
        Init a UDP stream with a configuration line
    Args:
        specificHost (bool, optional): if True the UDP Stream will stream only to a specific host name. Defaults to False.
        commandConfig (str, optional): Configuration line. Defaults to None.

    Raises:
        Exception: too few or too much parameter
        Exception: Given parameter incorrect 
        Exception: Given parameter incorrect (Specific host)
    """
    if specificHost :
        config = commandConfig.split(":")[0]
        if len(config) != 2 : 
            raise Exception("Error : too few or too much parameter") 
        else :
            try:
                stream.udpSettings = UdpSettings(host=config[0],  port=int(config[1]), specificHost=specificHost)
                stream.StreamType = StreamType.UDP
            except Exception as e : 
                raise Exception("Error : given parameter for a UDP stream are incorrect : \n{e}")
    else :
        try:
            stream.udpSettings = UdpSettings(port=int(commandConfig))
            stream.StreamType = StreamType.UDP
        except Exception as e : 
            raise Exception("Error : given parameter for a UDP stream are incorrect : \n{e}")      
    
def ConfigTCPStream(stream : Stream,isServer : bool = False ,commandConfig : str = None) -> None:
    """
        Init a TCP stream with a configuration line
    Args:
        isServer (bool, optional): If True the TCP stream will be configure as a Server. Defaults to False.
        commandConfig (str, optional): Configuration line . Defaults to None.

    Raises:
        Exception: too few or too much parameter
        Exception: Given parameter incorrect (Server)
        Exception: Given parameter incorrect (Client)
    """
    if isServer : 
        config = commandConfig.split(":")
        if len(config) != 2 : 
            raise Exception("Error : too few or too much parameter") 
        try : 
            stream.tcpSettings = TcpSettings(host=config[0] , port=int(config[1]), streamMode= StreamMode.SERVER)        
        except Exception as e : 
            raise Exception("Error : given parameters for a TCP Server stream are incorrect : \n{e}")   
    else : 
        try : 
            stream.tcpSettings = TcpSettings(port=int(commandConfig) , streamMode= StreamMode.CLIENT)
        except Exception as e : 
            raise Exception("Error : given parameters for a TCP Client stream are incorrect : \n{e}")   
    stream.StreamType = StreamType.TCP
    
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
        stream.serialSettings = SerialSettings(Port= port , baudrate=baudrate , parity=parity , stopbits=stopbits,bytesize=bytesize , Rtscts=rtscts)
        stream.StreamType = StreamType.Serial
    except Exception as e :
        raise Exception("Error : given parameters for a Serial stream are incorrect : \n{e}")   