
import base64
import os
import configparser
from src import constants
from ..StreamConfig.Preferences import Preferences
from ..StreamConfig.Stream import Stream


def create_conf_file(app):
    """
    Create the default configuration file with the current values 
    """
    conf_file_name = constants.CONFIGPATH + "/temp"
    conf_file = open(conf_file_name, "w",encoding='utf-8')

    # Add content to the file
    config = configparser.ConfigParser()
    for stream  in app.stream_list :
        section_name = "Port"+str(stream.id)
        config.add_section(section_name)
        config.set(section_name,"linksChecked" , str(stream.linked_ports))
        config.set(section_name,"startup_script" ,str(stream.send_startup_script ))
        config.set(section_name,"startupScriptFile" , stream.startup_script)
        config.set(section_name,"close_script",str(stream.send_close_script))
        config.set(section_name,"closeScriptFile",stream.close_script)
        config.set(section_name,"logfile",str(stream.logging_file))
        save_tcp_config(stream ,section_name , config)
        save_udp_config(stream ,section_name,config)
        config.set(section_name,"connectionType",str(stream.stream_type.value))
        save_serial_config(stream ,section_name , config)
        save_ntrip_config(stream , section_name , config)

    config.add_section("Preferences")
    save_preferences_config(app.preferences, "Preferences" , config)
    config.write(conf_file)
    conf_file.close()
    if os.path.exists(constants.DEFAULTCONFIGFILE) :
        os.remove(constants.DEFAULTCONFIGFILE)
    os.rename(conf_file_name , constants.DEFAULTCONFIGFILE)

# Saving config File
def save_udp_config(stream : Stream,section_name : str,save_config_file:configparser.ConfigParser):
    """
        Add current class values in the config_file
    Args:
        section_name (str): name of the current section
        save_config_file (configparser.ConfigParser): configparser of the configuration file
    """
    save_config_file.set(section_name,"hostNameUDP", stream.udp_settings.host )
    save_config_file.set(section_name,"portNumberUDP",str(stream.udp_settings.port))
    save_config_file.set(section_name,"specificIpUDP",str(stream.udp_settings.specific_host))
    save_config_file.set(section_name,"dataDirUDP",str(stream.udp_settings.DataFlow.value))

def save_tcp_config(stream : Stream,section_name : str,save_config_file:configparser.ConfigParser):
    """
        Add current class values in the config_file
    Args:
        section_name (str): name of the current section
        save_config_file (configparser.ConfigParser): configparser of the configuration file
    """
    save_config_file.set(section_name,"hostName",stream.tcp_settings.host)
    save_config_file.set(section_name,"portNumber",str(stream.tcp_settings.port))
    save_config_file.set(section_name,"TCPserver",str(stream.tcp_settings.is_server()))

def save_serial_config(stream:Stream,section_name : str,save_config_file:configparser.ConfigParser):
    """
        Add current class values in the config_file
    Args:
        section_name (str): name of the current section
        save_config_file (configparser.ConfigParser): configparser of the configuration file
    """

    save_config_file.set(section_name,"Serial.Port", str(stream.serial_settings.port))
    save_config_file.set(section_name,"Serial.BaudRate",str(stream.serial_settings.baudrate.value))
    save_config_file.set(section_name,"Serial.Parity",str(stream.serial_settings.parity.value))
    save_config_file.set(section_name,"Serial.StopBits",str(stream.serial_settings.stopbits.value))
    save_config_file.set(section_name,"Serial.ByteSize",str(stream.serial_settings.bytesize.value))
    save_config_file.set(section_name,"Serial.RtcCts",str(stream.serial_settings.rtscts))
    
def save_ntrip_config(stream : Stream,section_name:str,save_config_file:configparser.ConfigParser):
    save_config_file.set(section_name,"NTRIP.hostname",str(stream.ntrip_client.ntrip_settings.host))
    save_config_file.set(section_name,"NTRIP.portnumber",str(stream.ntrip_client.ntrip_settings.port))
    save_config_file.set(section_name,"NTRIP.mountPoint",str(stream.ntrip_client.ntrip_settings.mountpoint))
    save_config_file.set(section_name,"NTRIP.authenticationenabled", str(stream.ntrip_client.ntrip_settings.auth))
    save_config_file.set(section_name,"NTRIP.user",str(stream.ntrip_client.ntrip_settings.username))
    save_config_file.set(section_name,"NTRIP.password",str(base64.b64encode((stream.ntrip_client.ntrip_settings.password).encode()).decode()))
    save_config_file.set(section_name,"NTRIP.fixedpositionset",str(stream.ntrip_client.ntrip_settings.fixed_pos))
    save_config_file.set(section_name,"NTRIP.fixedLatitude",str(stream.ntrip_client.ntrip_settings.latitude))
    save_config_file.set(section_name,"NTRIP.fixedLongitude",str(stream.ntrip_client.ntrip_settings.longitude))
    save_config_file.set(section_name,"NTRIP.fixedHeight",str(stream.ntrip_client.ntrip_settings.height))
    save_config_file.set(section_name,"NTRIP.TLS", str(stream.ntrip_client.ntrip_settings.tls))
    
    

def save_preferences_config(preferences : Preferences , section_name : str,save_config_file  : configparser.ConfigParser): 
    """
        Add current class values in the config_file
    Args:
        section_name (str): name of the current section
        save_config_file (configparser.ConfigParser): configparser of the configuration file
    """
    save_config_file.set(section_name , "config_name" ,str(preferences.config_name))
    save_config_file.set(section_name,"numberOfPortPanels",str(preferences.max_streams))
    save_config_file.set(section_name,"line_termination",preferences.line_termination.replace("\n","\\n").replace("\r","\\r"))
    for connect , index in zip(preferences.connect,range(len(preferences.connect))):
        connect_string = "connect" + str(index)
        save_config_file.set(section_name,connect_string,str(connect))
