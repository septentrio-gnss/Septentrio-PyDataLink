import base64
import configparser
from ..StreamConfig.Preferences import Preferences
from ..StreamConfig.Stream import Stream
from src import constants
import os

def createConfFile(app):
    """
    Create the default configuration file with the current values 
    """
    confFileName = constants.CONFIGPATH + "/temp"
    confFile = open(confFileName, "w")

    # Add content to the file
    Config = configparser.ConfigParser()
    for stream  in app.StreamList : 
        sectionName = "Port"+str(stream.id)
        Config.add_section(sectionName)
        Config.set(sectionName,"linksChecked" , str(stream.linkedPort))
        Config.set(sectionName,"startupScript" ,str(stream.sendStartupScript ))
        Config.set(sectionName,"startupScriptFile" , stream.startupScript)
        Config.set(sectionName,"closeScript",str(stream.sendCloseScript))
        Config.set(sectionName,"closeScriptFile",stream.closeScript)
        Config.set(sectionName,"logFile",stream.loggingFile)
        SaveTCPConfig(stream ,sectionName , Config)
        SaveUDPConfig(stream ,sectionName,Config)
        Config.set(sectionName,"connectionType",str(stream.StreamType.value))
        SaveSerialConfig(stream ,sectionName , Config)
        SaveNTRIPConfig(stream , sectionName , Config)
    
    Config.add_section("Preferences")
    SavePreferencesConfig(app.preferences, "Preferences" , Config)
    Config.write(confFile)
    confFile.close()
    if os.path.exists(constants.DEFAULTCONFIGFILE) : 
        os.remove(constants.DEFAULTCONFIGFILE)
    os.rename(confFileName , constants.DEFAULTCONFIGFILE)    
    
    
# Saving Config File
def SaveUDPConfig(stream : Stream , sectionName : str,SaveConfigFile  : configparser.ConfigParser):
    """
        Add current class values in the configFile
    Args:
        sectionName (str): name of the current section
        SaveConfigFile (configparser.ConfigParser): configparser of the configuration file
    """
    SaveConfigFile.set(sectionName,"hostNameUDP", stream.udpSettings.host )
    SaveConfigFile.set(sectionName,"portNumberUDP",str(stream.udpSettings.port))
    SaveConfigFile.set(sectionName,"specificIpUDP",str(stream.udpSettings.specificHost))
    SaveConfigFile.set(sectionName,"dataDirUDP",str(stream.udpSettings.DataFlow.value))

def SaveTCPConfig(stream : Stream , sectionName : str,SaveConfigFile  : configparser.ConfigParser):
    """
        Add current class values in the configFile
    Args:
        sectionName (str): name of the current section
        SaveConfigFile (configparser.ConfigParser): configparser of the configuration file
    """
    SaveConfigFile.set(sectionName,"hostName",stream.tcpSettings.host)
    SaveConfigFile.set(sectionName,"portNumber",str(stream.tcpSettings.port))
    SaveConfigFile.set(sectionName,"TCPserver",str(stream.tcpSettings.isServer()))

def SaveSerialConfig(stream : Stream , sectionName : str,SaveConfigFile  : configparser.ConfigParser):
    """
        Add current class values in the configFile
    Args:
        sectionName (str): name of the current section
        SaveConfigFile (configparser.ConfigParser): configparser of the configuration file
    """
    
    SaveConfigFile.set(sectionName,"Serial.Port", str(stream.serialSettings.port))
    SaveConfigFile.set(sectionName,"Serial.BaudRate",str(stream.serialSettings.baudrate.value))
    SaveConfigFile.set(sectionName,"Serial.Parity",str(stream.serialSettings.parity.value))
    SaveConfigFile.set(sectionName,"Serial.StopBits",str(stream.serialSettings.stopbits.value))
    SaveConfigFile.set(sectionName,"Serial.ByteSize",str(stream.serialSettings.bytesize.value))
    SaveConfigFile.set(sectionName,"Serial.RtcCts",str(stream.serialSettings.rtscts))
    
def SaveNTRIPConfig(stream : Stream , sectionName : str,SaveConfigFile  : configparser.ConfigParser):
    SaveConfigFile.set(sectionName,"NTRIP.hostname",str(stream.ntripClient.ntripSettings.host))
    SaveConfigFile.set(sectionName,"NTRIP.portnumber",str(stream.ntripClient.ntripSettings.port))
    SaveConfigFile.set(sectionName,"NTRIP.mountPoint",str(stream.ntripClient.ntripSettings.mountpoint))
    SaveConfigFile.set(sectionName,"NTRIP.authenticationenabled", str(stream.ntripClient.ntripSettings.auth))
    SaveConfigFile.set(sectionName,"NTRIP.user",str(stream.ntripClient.ntripSettings.username))
    SaveConfigFile.set(sectionName,"NTRIP.password",str(base64.b64encode((stream.ntripClient.ntripSettings.password).encode()).decode()))
    SaveConfigFile.set(sectionName,"NTRIP.fixedpositionset",str(stream.ntripClient.ntripSettings.fixedPos))
    SaveConfigFile.set(sectionName,"NTRIP.fixedLatitude",str(stream.ntripClient.ntripSettings.latitude))
    SaveConfigFile.set(sectionName,"NTRIP.fixedLongitude",str(stream.ntripClient.ntripSettings.longitude))
    SaveConfigFile.set(sectionName,"NTRIP.fixedHeight",str(stream.ntripClient.ntripSettings.height))
    SaveConfigFile.set(sectionName,"NTRIP.TLS", str(stream.ntripClient.ntripSettings.tls))
    
    

def SavePreferencesConfig(preferences : Preferences , sectionName : str,SaveConfigFile  : configparser.ConfigParser): 
    """
        Add current class values in the configFile
    Args:
        sectionName (str): name of the current section
        SaveConfigFile (configparser.ConfigParser): configparser of the configuration file
    """
    SaveConfigFile.set(sectionName , "configName" ,str(preferences.configName))       
    SaveConfigFile.set(sectionName,"numberOfPortPanels",str(preferences.maxStreams))
    SaveConfigFile.set(sectionName,"lineTermination",preferences.lineTermination.replace("\n","\\n").replace("\r","\\r"))
    for connect , index in zip(preferences.Connect,range(len(preferences.Connect))):
        connectString = "connect" + str(index)
        SaveConfigFile.set(sectionName,connectString,str(connect))
