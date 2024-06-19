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

from enum import Enum
import queue
from .Preferences import Preferences
from .Stream import Stream
from ..Configuration import SaveConfiguration , CommandLineConfiguration , FileConfiguration 
import configparser

"""
    Class which initialise every Streams.
    Depending on the input it can be configure via a configuration file or via a configuration list
    
"""
class ConfigurationType(Enum):
    FILE = 0
    CMDLINE = 1
    DEFAULT = None


class App :

    def __init__(self,maxStream : int = 6, configFile :str = "" , streamSettingsList : list[str] = [] , configurationType : ConfigurationType = ConfigurationType.DEFAULT , debugLogging : bool = False):
        
        self.preferences : Preferences = Preferences()
        self.maxStream :int  = maxStream
        self.streamSettingsList : list[str] = streamSettingsList
        self.configFile :str = configFile
        self.StreamList : list[Stream] = []
        self.linkedData : list[queue.Queue] = []
        self.debugLogging : bool = debugLogging 
        self.configurationType : ConfigurationType = configurationType

        for i in range (self.maxStream) : 
            self.linkedData.append(queue.Queue())
            
        for i in range(self.maxStream):
            newPort = Stream(i ,self.linkedData , debugLogging=debugLogging )
            self.StreamList.append(newPort)
            
        self.preferences = Preferences(self.maxStream)
        
        if configurationType != ConfigurationType.DEFAULT:
            self.ConfigureApp( configurationType)
        

        

    def ConfigureApp(self , type : ConfigurationType ): 
        
        if type.value == ConfigurationType.FILE.value :
            
            config = configparser.ConfigParser()
            readValue = config.read(self.configFile)
            if len(readValue) != 0 :
                try :
                    newMaxStream = int(config.get("Preferences","numberOfPortPanels"))
                    if self.maxStream > newMaxStream and newMaxStream > 0 : 
                        diff = self.maxStream - newMaxStream
                        for i in range(diff) : 
                            self.StreamList.pop(self.maxStream - i - 1)
                        self.maxStream = newMaxStream
                except : 
                    pass
                finally :
                    nextStreamid = 0
                    for key in config.sections():
                        if "Preferences" in key:
                            FileConfiguration.ConfFilePreference(self.preferences, config[key] )
                        if "Port" in key :
                            FileConfiguration.ConfFileConfig(self.StreamList[nextStreamid],config[key])
                            nextStreamid +=1 
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
                        CommandLineConfiguration.CommandLineConfig(self.StreamList[iterator] , stream)
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
        if self.configurationType.value == ConfigurationType.FILE.value or  self.configurationType.value == ConfigurationType.DEFAULT.value :
            SaveConfiguration.createConfFile(self)
        for port in self.StreamList:
            port.Disconnect()
        self.linkedData.clear()
        self.StreamList.clear()
        
    


