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
from src.constants import  * 
from src.StreamConfig.App import App , ConfigurationType
try : 
    from PySide6.QtWidgets import QApplication
    from src.UserInterfaces import GraphicalUserInterface 
    GUI = True
except Exception as e:
    print(e)
    GUI = False
import os
import shutil
import argparse
try : 
    from src.UserInterfaces import TerminalUserInterface
    TUI = True
except : 
    TUI = False
from src.UserInterfaces import CommandLineInterface


    
def checkDataFolder():
    if os.path.exists(DATAPATH) is not True :
        os.mkdir(DATAPATH)
    if os.path.exists( CONFIGPATH ) is not True:
        os.mkdir(CONFIGPATH )
    if os.path.exists( LOGFILESPATH ) is not True:
        os.mkdir(LOGFILESPATH )

class DatalinkApp:
    

    def __init__(self) -> None:
        self.app : App = None
        self.userInterface = None
        self.showDataPort = None
        if args.Mode == "CMD" :
                if args.Streams is None :
                    print("Error : you need to specify the streams to configure\n")
                    return
                else :
                    if args.ShowData is not None:
                        try :
                            show = int(args.ShowData)
                        except Exception as e :
                                print(f"Error : streams id \"{args.ShowData}\" is not correct , please enter a valid ID !")
                                return 
                    
                    self.app = App(max_stream=len(args.Streams),stream_settings_list=args.Streams , configuration_type= ConfigurationType.CMDLINE)
                    if args.ShowData is not None :
                        if show <= len(self.app.stream_list):
                            self.showDataPort=self.app.stream_list[show - 1]
                            self.showDataPort.toggle_all_data_visibility()
                    
        else : 
                if os.path.exists(args.ConfigPath): 
                    self.app = App(configuration_type= ConfigurationType.FILE,config_file=args.ConfigPath, debug_logging=True)
                elif os.path.exists(DEFAULTCONFIGFILE) : 
                    self.app = App(configuration_type= ConfigurationType.FILE , config_file=DEFAULTCONFIGFILE , debug_logging=True)
                else :
                    self.app = App(debug_logging=True)
        self.Start()
                
    def Start(self) -> None : 
        if args.Mode == "TUI":
            self.DatalinkInTerminalStart()
        elif args.Mode == "GUI":
            self.DatalinkInGuiStart()
        elif args.Mode == "CMD":
            self.DatalinkInCmdStart()
                        

    def DatalinkInTerminalStart(self):
        if os.name == "posix" and TUI:
                self.userInterface = TerminalUserInterface(self.app)
                sys.exit(self.userInterface.MainMenu())
            
        elif not TUI:
            print(f"simple-Term-menu is required to run in TUI mode \nInstall Simple-Term-Menu : pip install simple-term-menu\nOr run the App in a Different mode (-m GUI or -m CMD)")
        else :
                print(f"Sorry the terminal version of Data link is only available on Unix distro")
    
    def DatalinkInGuiStart(self):
        if(GUI):
            self.userInterface = QApplication()
            gallery = GraphicalUserInterface.GraphicalUserInterface(self.app)
            gallery.show()
            sys.exit(self.userInterface.exec())
        else :
            print(f"PySide6 is required to run in GUI mode \nInstall pyside : pip install PySide6 \nOr run the App in a Different mode (-m CMD or -m TUI)")
        
    def DatalinkInCmdStart(self):
        self.userInterface = CommandLineInterface.CommandLineInterface(self.app , showdataId = self.showDataPort)
        sys.exit(self.userInterface.run())
    
        

if __name__ == "__main__":
    checkDataFolder()
    MinPorts = 1
    MaxPorts = 6

    parser = argparse.ArgumentParser(prog="PyDatalink" ,description='')
    parser.add_argument('--Mode','-m', choices=['TUI', 'GUI', 'CMD'], default='GUI',
                        help="Start %(prog)s with a specific interface (DEFAULT : GUI)")
    parser.add_argument('--ConfigPath','-c', action='store', default= DEFAULTCONFIGFILE ,
                            help='Path to the config file ( This Option won\'t be use when in CMD mode )  ')

    parser.add_argument('--Streams' ,'-s', nargs='*' , action='store' , 
                        help="List of streams to configure , the size of this list is configure by --nbPorts\n ,this parameter is only used when in CMD mode \n ")
    parser.add_argument('--ShowData', "-d" ,nargs="?", action="store",
                        help="Lisf of streams id, will print every input and output data from the streams\n ,this parameter is only used when in CMD mode ")
    

    args = parser.parse_args()
    DatalinkApp()
        


   