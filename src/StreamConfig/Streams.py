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
import queue
import configparser
import os
import serial
from .Preferences import Preferences
from .PortConfig import PortConfig
from src import constants

"""
    Class which initialise every Port/Stream.
    Depending on the input it can be configure via a configuration file or via a configuration list
    
"""
class Streams :

    def __init__(self,maxStream : int = 6, configFile :str = None , streamSettingsList : list[str] = None):
        
        self.preferences : Preferences = Preferences()
        self.maxStream = maxStream
        self.configFile = configFile
        self.streamSettingsList = streamSettingsList
        self.StreamList : list[PortConfig] = []
        self.linkedData : list[queue.Queue] = []
            #Init Communication Queues
        for i in range (self.maxStream) : 
            self.linkedData.append(queue.Queue())

        if self.streamSettingsList is None:
            
            #Init Communication Ports with default Value 
            if configFile is None :
                for i in range(maxStream):
                    if configFile is None :
                        newPort = PortConfig(i ,self.linkedData )
                        self.StreamList.append(newPort)
                self.preferences = Preferences(maxStream)
                
            #init Communication Ports with a ConfigFile
            else : 
                config = configparser.ConfigParser()
                readValue = config.read(configFile)
                if len(readValue) != 0 :
                    try :
                        self.maxStream = int(config.get("Preferences","numberOfPortPanels"))
                    except : 
                        self.maxStream = maxStream
                    nbPreConfig = 0
                    for key in config.sections():
                        if "Preferences" in key:
                            preferenceKey = config[key]
                            self.preferences = Preferences(self.maxStream , ConfigFile= preferenceKey)
                            
                        if "Port" in key and nbPreConfig < self.maxStream :
                            portKey = config[key]
                            newPort = PortConfig(nbPreConfig ,self.linkedData,portKey)
                            self.StreamList.append(newPort)
                            nbPreConfig += 1
                    if nbPreConfig < self.maxStream :
                        for i in range(self.maxStream - nbPreConfig):
                            newPort = PortConfig(i + nbPreConfig ,self.linkedData )
                            self.StreamList.append(newPort)
                    for portId in range(len(self.preferences.Connect)):
                        self.StreamList[portId].setLineTermination(self.preferences.lineTermination)
                        if self.preferences.Connect[portId] :
                            try :
                                self.StreamList[portId].Connect(self.StreamList[portId].StreamType)
                            except: 
                                print(f"Stream {portId} couldn't start properly")
                else :
                    raise Exception("Init Error","The given file is empty")
        else : 
            
            iterator = 0
            for stream in self.streamSettingsList :           
                StreamType = stream.split("://")[0]
                if StreamType.lower() in ["udp","udpspe","tcpcli","tcpsrv","serial","ntrip"]:
                    try : 
                        newPort = PortConfig(iterator,self.linkedData,commandLineConfig=stream)
                        self.StreamList.append(newPort)
                        iterator += 1
                    except Exception as e : 
                        print(f"Could not open {StreamType} : {e}")
                        self.CloseAll()
                        break
                else :
                    raise ValueError(f" {StreamType} is not a valid stream type")
                

    def CloseAll(self):
        """
        Close every Stream that are still connected
        """
        if self.streamSettingsList is None :
            self.createConfFile()
        for port in self.StreamList:
            port.Disconnect()
        self.linkedData.clear()
        self.StreamList.clear()
        
    def createConfFile(self):
        """
        Create the default configuration file with the current values 
        """
        confFileName = constants.CONFIGPATH + "/temp"
        confFile = open(confFileName, "w")

        # Add content to the file
        Config = configparser.ConfigParser()
        for stream in self.StreamList : 
            sectionName = "Port"+str(stream.id)
            Config.add_section(sectionName)
            Config.set(sectionName,"linksChecked" , str(stream.linkedPort))
            Config.set(sectionName,"startupScript" ,str(stream.sendStartupScript ))
            Config.set(sectionName,"startupScriptFile" , stream.startupScript)
            Config.set(sectionName,"closeScript",str(stream.sendCloseScript))
            Config.set(sectionName,"closeScriptFile",stream.closeScript)
            Config.set(sectionName,"logFile",stream.loggingFile)
            stream.tcpSettings.SaveConfig(sectionName , Config)
            stream.udpSettings.SaveConfig(sectionName,Config)
            Config.set(sectionName,"connectionType",str(stream.StreamType.value))
            stream.serialSettings.SaveConfig(sectionName , Config)
            stream.ntripClient.ntripSettings.SaveConfig(sectionName , Config)
        
        Config.add_section("Preferences")
        self.preferences.SaveConfig("Preferences",Config)
        Config.write(confFile)
        confFile.close()
        if os.path.exists(constants.DEFAULTCONFIGFILE) : 
            os.remove(constants.DEFAULTCONFIGFILE)
        os.rename(confFileName , constants.DEFAULTCONFIGFILE)    


