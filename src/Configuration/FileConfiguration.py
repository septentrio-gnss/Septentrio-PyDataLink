import base64
import configparser
from ..NTRIP import *
from ..StreamSettings.UdpSettings import *
from ..StreamSettings.SerialSettings import *
from ..StreamSettings.TcpSettings import *
from ..StreamConfig.Stream import StreamType , Stream
from ..StreamConfig.Preferences import Preferences
            
            
def ConfFilePreference(preference ,confFile : configparser.SectionProxy) :
    if preference is None : 
        raise Exception("need a preference to be configured")
    try : 
            preference.maxStreams =  int(confFile.get("numberOfPortPanels"))
    except : 
        pass
    for connectid in range(preference.maxStreams):
        try : 
            preference.Connect[connectid] = ( True if confFile.get(f"connect{connectid}").lower() == "true" else False )
        except : 
            pass
    try : 
        preference.lineTermination  = confFile.get("lineTermination").replace("\\n","\n").replace("\\r","\r")
    except : 
        pass
    try: 
        if len(confFile.get("configName")) != 0 : 
            preference.configName = str(confFile.get("configName"))
    except : 
        pass
            
def ConfFileConfig(stream : Stream ,confFile : configparser.SectionProxy) :
        """
        Init a stream and it's settings with a configuration file 
        
        Args:
            confFile (configparser.SectionProxy): section of a stream in a configuration file
        """
        if stream is None :
            raise Exception('need a stream to be configured')
        
        stream.serialSettings = ConfFileSerial(confFile, stream.debugLogging)
        stream.tcpSettings= ConfFileTCP(confFile , stream.debugLogging)
        
        stream.udpSettings = ConfFileUDP(confFile ,  stream.debugLogging )
        stream.ntripClient = ConfFileNTRIPClient(confFile ,  stream.debugLogging )
        try :
            
            stream.StreamType = StreamType(int(confFile.get("connectionType")))
        except :
            stream.StreamType = StreamType.NONE
        links = confFile.get("linksChecked").replace("[","").replace(" ","").replace("]","").split(",")
        for link in links:
            if link != '':
                stream.linkedPort.append(int(link))
        stream.startupScript = confFile.get("startupscriptfile")        
        try : 
            stream.sendStartupScript = True if confFile.get("startupscript").lower() == "true" else False
        except : 
            stream.sendStartupScript = False
        stream.closeScript = confFile.get("closescriptfile")        
        try : 
            stream.sendCloseScript = True if confFile.get("closescript").lower() == "true" else False
        except : 
            stream.sendCloseScript = False
        stream.loggingFile = confFile.get("logfile")
        if stream.loggingFile != "":
            stream.logging = True
    
def ConfFileSerial(confFile :configparser.SectionProxy, debugLogging :bool):
    """
    Init Serial settings of the current stream with value from a configuration file.
    If no value in configuration file , default value will be use

    Args:
        confFile (configparser.SectionProxy): configuration file 

    Returns:
        SerialSetting: return a new SerialSettings
    """
    port : str = confFile.get('Serial.Port')
    try :
        baudrate : BaudRate = BaudRate(confFile.get('Serial.BaudRate'))
    except : 
        baudrate : BaudRate = BaudRate.eBAUD115200
    try :    
        parity : Parity = Parity(confFile.get('Serial.Parity'))
    except : 
        parity : Parity = Parity.PARITY_NONE
    try : 
        stopbits : StopBits = StopBits(confFile.get('Serial.StopBits') ) 
    except :
        stopbits : StopBits = StopBits.STOPBITS_ONE
    try :
        bytesize : ByteSize= ByteSize(confFile.get('Serial.ByteSize')) 
    except : 
        bytesize : ByteSize = ByteSize.EIGHTBITS 
    try : 
        rtscts : bool = True if confFile.get('Serial.RtcCts').lower() == "true" else False
    except :
        rtscts = False
    return SerialSettings(Port= port , baudrate=baudrate , parity=parity , stopbits=stopbits,bytesize=bytesize , Rtscts=rtscts,debugLogging=debugLogging)

def ConfFileTCP(confFile : configparser.SectionProxy, debugLogging : bool):
    """
    Init TCP settings of the current stream with value from a configuration file.
    If no value in configuration file , default value will be use

    Args:
        confFile (configparser.SectionProxy): configuration file 

    Returns:
        TcpSettings: return a new TcpSettings
    """        
    host : str = confFile.get('hostName')
    try : 
        port : int = int(confFile.get('portNumber'))
    except :
        port = 28784
        
    if bool(True if str(confFile.get('TCPserver')).lower() == "true" else False ) is True :
        host = ''
        streamMode = StreamMode.SERVER
    else:
        streamMode = StreamMode.CLIENT
            
    return TcpSettings(host= host , port= port ,streamMode = streamMode , debugLogging=debugLogging)
   
def ConfFileUDP(confFile : configparser.SectionProxy, debugLogging : bool):
    """
    Init UDP settings of the current stream with value from a configuration file.
    If no value in configuration file , default value will be use

    Args:
        confFile (configparser.SectionProxy): configuration file 

    Returns:
        UdpSettings: return a new udpsettings
    """
    host : str = confFile.get('hostNameUDP')
    try : 
        port : int = int(confFile.get('portNumberUDP'))
    except : 
        port = 28784
    try: 
        dataFlow : DataFlow = DataFlow(confFile.get('dataDirUDP'))
    except :
        dataFlow : DataFlow = DataFlow.Both
    try  :
        specificHost : bool  = True if confFile.get('specificIpUDP').lower() == "true" else False
    except : 
        specificHost = False
    
    return UdpSettings(host=host,port=port , dataflow=dataFlow,specificHost=specificHost , debugLogging = debugLogging )
    
def ConfFileNTRIPClient(confFile : configparser.SectionProxy , debugLogging : bool):
    """
    Init a Ntrip client with value from a configuration file.
    If no value in configuration file , default value will be use

    Args:
        confFile (configparser.SectionProxy): configuration file 

    Returns:
        NtripClient: return a new ntrip
    """
    host : str = confFile.get('NTRIP.hostname')
    try :
        port : int = int(confFile.get('NTRIP.portnumber'))
    except:
        port = 2101
    mountpoint : str = confFile.get('NTRIP.mountPoint')
    try : 
        auth : bool = True if confFile.get('NTRIP.authenticationenabled').lower() == "true" else False
    except : 
        auth = False
    username : str = confFile.get('NTRIP.user')
    try : 
        password : str = base64.b64decode((confFile.get('NTRIP.password')).encode()).decode()
    except : 
        password : str = ""
    try : 
        tls : bool = True if confFile.get('NTRIP.TLS').lower() == "true" else False
    except : 
        tls = False
    try : 
        fixedPos : bool = True if confFile.get('NTRIP.fixedpositionset').lower() == "true" else False
    except : 
        fixedPos = False
                
    try :
        latitude : float = float(confFile.get('NTRIP.fixedlatitude'))
    except :
        latitude = 00.000000000
    try :
        longitude : float = float(confFile.get('NTRIP.fixedlongitude'))
    except :
        longitude = 000.000000000
    try : 
        height : int = int(confFile.get('NTRIP.fixedheight'))
    except :
        height = 0
    
        
    return NtripClient(host=host , port=port , auth=auth , username=username , password= password , mountpoint=mountpoint 
                        , tls= tls ,fixedPos=fixedPos , latitude = latitude , longitude = longitude , height = height , debugLogging= debugLogging )
