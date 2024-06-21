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

import configparser
from enum import Enum
import queue

from ..NTRIP.NtripClient import NtripClientError
from .Preferences import Preferences
from .Stream import Stream
from ..Configuration import SaveConfiguration , CommandLineConfiguration , FileConfiguration


class AppException(Exception):
    """
        Exception class for App 
    """
    def __init__(self, message, error_code = None):
        super().__init__(message)
        self.error_code = error_code
        
class ConfigurationFileEmpty(AppException):
    """Raised when the configuration file is empty
    """
    
class InvalidStreamTypeException(AppException):
    """Raised when the given stream type is not supported
    """
class ConfigurationType(Enum):
    """Type of configuration that need to be executed 
    """
    FILE = 0
    CMDLINE = 1
    DEFAULT = None


class App :
    """
    Class which initialise every Streams.
    Depending on the input it can be configure via a configuration file or via a configuration list
    
    """

    def __init__(self,max_stream : int = 6, config_file :str = "" ,
                 stream_settings_list : list[str] = None ,
                 configuration_type : ConfigurationType = ConfigurationType.DEFAULT ,
                 debug_logging : bool = False):

        self.preferences : Preferences = Preferences()
        self.max_stream :int  = max_stream
        self.stream_settings_list : list[str] = stream_settings_list
        self.config_file :str = config_file
        self.stream_list : list[Stream] = []
        self.linked_data : list[queue.Queue] = []
        self.debug_logging : bool = debug_logging 
        self.configuration_type : ConfigurationType = configuration_type

        for i in range (self.max_stream) :
            self.linked_data.append(queue.Queue())

        for i in range(self.max_stream):
            new_port = Stream(i ,self.linked_data , debug_logging=debug_logging )
            self.stream_list.append(new_port)

        self.preferences = Preferences(self.max_stream)

        if configuration_type != ConfigurationType.DEFAULT:
            self.configure_app( configuration_type)

    def configure_app(self , config_type : ConfigurationType ):
        """ Configure app according to the configuration type selected
        """
        if config_type.value == ConfigurationType.FILE.value :
            config = configparser.ConfigParser()
            read_value = config.read(self.config_file)
            if len(config.sections()) == 0 :
                raise ConfigurationFileEmpty("Configuration file is empty")
            else :
                try :
                    new_max_stream = int(config.get("Preferences","numberOfPortPanels"))
                    if self.max_stream > new_max_stream and new_max_stream > 0 :
                        diff = self.max_stream - new_max_stream
                        for i in range(diff) :
                            self.stream_list.pop(self.max_stream - i - 1)
                        self.max_stream = new_max_stream
                finally :
                    next_stream_id = 0
                    for key in config.sections():
                        if "Preferences" in key:
                            FileConfiguration.conf_file_preference(self.preferences, config[key] )
                        if "Port" in key :
                            if next_stream_id < self.max_stream :
                                FileConfiguration.conf_file_config(self.stream_list[next_stream_id],config[key])
                                next_stream_id +=1
                    for port_id, value  in enumerate(self.preferences.connect):
                        if port_id < self.max_stream:
                            self.stream_list[port_id].set_line_termination(self.preferences.line_termination)
                            if value :
                                try :
                                    self.stream_list[port_id].connect(self.stream_list[port_id].stream_type)
                                except (NtripClientError) as e :
                                    self.stream_list[port_id].startup_error =f"Ntrip stream couldn't start properly : \n {e}"
                                except Exception as e:
                                    self.stream_list[port_id].startup_error =f"Stream couldn't start properly : \n {e}"
            
        else :
            iterator = 0
            for stream in self.stream_settings_list :
                stream_type = stream.split("://")[0]
                if stream_type.lower() in ["udp","udpspe","tcpcli","tcpsrv","serial","ntrip"]:
                    try :
                        CommandLineConfiguration.command_line_config(self.stream_list[iterator],stream)
                        iterator += 1
                    except CommandLineConfiguration.CommandLineConfigurationException as e :
                        print(f"Could not open {stream_type} : {e}")
                        self.close_all()
                        break
                else :
                    raise InvalidStreamTypeException(f" {stream_type} is not a valid stream type")


    def close_all(self):
        """
        Close every Stream that are still connected
        """
        if ((self.configuration_type.value == ConfigurationType.FILE.value) or
        (self.configuration_type.value == ConfigurationType.DEFAULT.value)) :

            SaveConfiguration.create_conf_file(self)
        for port in self.stream_list:
            port.disconnect()
        self.linked_data.clear()
        self.stream_list.clear()
