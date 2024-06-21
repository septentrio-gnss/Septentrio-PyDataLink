#!/usr/bin/env python
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

import sys
import os
import argparse
from src.constants import  DATAPATH , CONFIGPATH , LOGFILESPATH , DEFAULTCONFIGFILE
from src.StreamConfig.App import App , ConfigurationType
try :
    from PySide6.QtWidgets import QApplication
    from src.UserInterfaces.GraphicalUserInterface import GraphicalUserInterface 
    GUI = True
except Exception as e:
    GUI = False
    raise e

try :
    from src.UserInterfaces.TerminalUserInterface import TerminalUserInterface
    TUI = True
except NotImplementedError :
    TUI = False

from src.UserInterfaces.CommandLineInterface import CommandLineInterface

def clean_log_folder():
    files = [os.path.join(LOGFILESPATH, f) for f in os.listdir(LOGFILESPATH) if os.path.isfile(os.path.join(LOGFILESPATH, f))]
    if len(files) > 40:
        oldest_file = min(files, key=os.path.getctime)
        os.remove(oldest_file)



def check_data_folder():
    if os.path.exists(DATAPATH) is not True :
        os.mkdir(DATAPATH)
    if os.path.exists( CONFIGPATH ) is not True:
        os.mkdir(CONFIGPATH )
    if os.path.exists( LOGFILESPATH ) is not True:
        os.mkdir(LOGFILESPATH )
    else : 
        clean_log_folder()

class DatalinkApp:
    """Main class for Datalink application
    """

    def __init__(self , config_args) -> None:
        self.config_args = config_args
        self.app : App = None
        self.user_interface = None
        self.show_data_port = None
        if self.config_args.Mode == "CMD" :
            if self.config_args.Streams is None :
                print("Error : you need to specify the streams to configure\n")
                return
            else :
                if self.config_args.ShowData is not None:
                    try :
                        show = int(self.config_args.ShowData)
                    except ValueError  as exc:
                        print(f"Error : streams stream_id \"{self.config_args.ShowData}\" is not correct , please enter a valid ID !")
                        raise exc

                self.app = App(max_stream=len(self.config_args.Streams),stream_settings_list=self.config_args.Streams , configuration_type= ConfigurationType.CMDLINE)
                if self.config_args.ShowData is not None :
                    if show <= len(self.app.stream_list):
                        self.show_data_port=self.app.stream_list[show - 1]
                        self.show_data_port.toggle_all_data_visibility()

        else :
            if os.path.exists(self.config_args.ConfigPath):
                self.app = App(configuration_type= ConfigurationType.FILE,config_file=self.config_args.ConfigPath, debug_logging=True)
            elif os.path.exists(DEFAULTCONFIGFILE) :
                self.app = App(configuration_type= ConfigurationType.FILE , config_file=DEFAULTCONFIGFILE , debug_logging=True)
            else :
                self.app = App(debug_logging=True)

    def start(self) -> None :
        if self.config_args.Mode == "TUI":
            self.datalink__terminal_start()
        elif self.config_args.Mode == "GUI":
            self.datalink_graphical_start()
        elif self.config_args.Mode == "CMD":
            self.datalink_cmdline_start()

    def datalink__terminal_start(self):
        """Start Datalink as a Graphical User interface
        """
        if os.name == "posix" and TUI:
            self.user_interface = TerminalUserInterface(self.app)
            sys.exit(self.user_interface.MainMenu())
        elif not TUI:
            print("simple-Term-menu is required to run in TUI mode \nInstall Simple-Term-Menu : pip install simple-term-menu\nOr run the App in a Different mode (-m GUI or -m CMD)")
        else :
            print("Sorry the terminal version of Data link is only available on Unix distro")

    def datalink_graphical_start(self):
        """Start Datalink as a Graphical User interface
        """
        if(GUI):
            self.user_interface = QApplication()
            gallery = GraphicalUserInterface(self.app)
            gallery.show()
            sys.exit(self.user_interface.exec())
        else :
            print("PySide6 is required to run in GUI mode \nInstall pyside : pip install PySide6 \nOr run the App in a Different mode (-m CMD or -m TUI)")

    def datalink_cmdline_start(self):
        """Start Datalink as a command line interface
        """
        self.user_interface = CommandLineInterface(self.app , show_data_id= self.show_data_port)
        sys.exit(self.user_interface.run())

if __name__ == "__main__":
    check_data_folder()

    parser = argparse.ArgumentParser(prog="PyDatalink" ,description='')
    parser.add_argument('--Mode','-m', choices=['TUI', 'GUI', 'CMD'], default='GUI',
                        help="Start %(prog)s with a specific interface (DEFAULT : GUI)")
    parser.add_argument('--ConfigPath','-c', action='store', default= DEFAULTCONFIGFILE ,
                            help='Path to the config file ( This Option won\'t be use when in CMD mode )  ')

    parser.add_argument('--Streams' ,'-s', nargs='*' , action='store' ,
                        help="List of streams to configure , the size of this list is configure by --nbPorts\n ,this parameter is only used when in CMD mode \n ")
    parser.add_argument('--ShowData', "-d" ,nargs="?", action="store",
                        help="Lisf of streams stream_id, will print every input and output data from the streams\n ,this parameter is only used when in CMD mode ")

    DatalinkApp(config_args=parser.parse_args()).start()

