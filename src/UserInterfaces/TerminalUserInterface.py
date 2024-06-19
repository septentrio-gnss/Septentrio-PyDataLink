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


import threading
import socket
import sys
import time

from src.StreamSettings.SerialSettings import *
from src.StreamSettings.TcpSettings import *
from src.StreamSettings.UdpSettings import *
try : 
    from simple_term_menu import TerminalMenu 
except: 
    print("WARNING : You are running pyDataLink on a system that doesn't support TUI interface !")
from ..StreamConfig import  App ,  Stream 
from ..StreamSettings import *



class TerminalUserInterface :
    
    # Menu Items 
    mainMenuItems = ["[1] - Configure Stream" , "[2] - connect / disconnect","[3] - ShowData" ,"[4] - Link","[5] - Preferences","[q] - Exit"]
    connectDisconectItems=["[1] - connect","[2] - disconnect" ,"[q] - Back to stream selection"]
    showDataMenuItems=["[1] - show all data","[2] - Show Input data" , "[3] - Show Output data","[q] - Back to stream selection"]

    
    PortListMenuItems = ["[q] - Back to main menu"]

    configureMenuSubmenuItems = ["[1] - Stream Config","[2] - connect Script", "[3] - Close Script" ,"[4] - Logging" , "[q] - Back to stream selection"]
    
    configureStreamTypeMenuItems=[]
    
    SerialSettingsBaudRateItems =[]
    SerialSettingsParityItems =[]
    SerialSettingsStopBitsItems =[]
    SerialSettingsBytesizeItems = []

    TCPSettingsStreamModeItems = []

    UDPSettingsDataFlowItems = []


    def __init__(self ,app : App ) -> None:
        self.App : App = app
        for port , i in zip(app.stream_list , range(len(app.stream_list))):
           self.PortListMenuItems.insert(i,"[%d] - Stream %d - %s %s" %(i ,i ,( "Connected" if port.connected else "Disonnected") ,  ("" if port.stream_type is None else str(port.stream_type).replace("StreamType.","- "))))
        self._CreateMenus()
        
        self.showDataThread : threading.Thread = None
        self.stopShowDataEvent = threading.Event()
        
    def _showDataTask(self, selectedPort : Stream):
        while self.stopShowDataEvent.is_set() is False:
            if selectedPort.data_to_show.empty() is False :
                print(selectedPort.data_to_show.get())
        return 0
                

    def _refreshMenuItems(self) :

        for port , i in zip(self.App.stream_list , range(len(self.App.stream_list))):
           self.PortListMenuItems[i] = "[%d] - Stream %d - %s %s" %(i ,i ,( "Connected" if port.connected else "Disonnected") , ("" if port.stream_type is None else str(port.stream_type).replace("StreamType.","- ")))
       

    def _CreateMenus(self):

        #BaudRate Menu
        for baudrate in BaudRate :
            self.SerialSettingsBaudRateItems.append(baudrate.value)
        self.SerialSettingsBaudRateItems.append("[q] - Back") 

        #Parity Menu
        for parity in Parity :
            self.SerialSettingsParityItems.append(str(parity).replace("Parity.PARITY_",""))
        self.SerialSettingsParityItems.append("[q] - Back") 

        #StopBits Menu
        for stopbits in StopBits :
            self.SerialSettingsStopBitsItems.append(str(stopbits).replace("StopBits.STOPBITS_",""))
        self.SerialSettingsStopBitsItems.append("[q] - Back") 

         #Bytesize Menu
        for bytesize in ByteSize :
            self.SerialSettingsBytesizeItems.append(str(bytesize).replace("ByteSize.",""))
        self.SerialSettingsBytesizeItems.append("[q] - Back") 

        #StreamMode Menu
        for mode in StreamMode :
            self.TCPSettingsStreamModeItems.append(str(mode).replace("StreamMode.",""))
        self.TCPSettingsStreamModeItems.append("[q] - Back") 

        #StreamType
        iterator = 1 
        for type in Stream.stream_type :
            if type.value is not None:
                self.configureStreamTypeMenuItems.append("[%d] - %s" %(iterator, str(type).replace("StreamType.","")))
                iterator+=1
        self.configureStreamTypeMenuItems.append("[q] - Back") 

        # DataFlow
        for flow in DataFlow :
            self.UDPSettingsDataFlowItems.append("%s" %(str(flow).replace("DataFlow.","")))
        self.UDPSettingsDataFlowItems.append("[q] - Back") 
        
        

          
# Main menu
    def MainMenu(self) :

        terminalMenu = TerminalMenu(self.mainMenuItems ,clear_screen=True,  title="PyDatalink\n you are using pyDatalink App in Terminal UI mode \n")
        menuEntryIndex = terminalMenu.show()
        match menuEntryIndex: 
            case 0 : self.ConfigureMenu() 
            case 1 : self.Connect_menu()
            case 2 : self.ShowData_menu()
            case 3 : self.LinkPort_menu()
            case 4 : self.Preferences_menu()
            case _ : 
                self.App.close_all()
                sys.exit()
      
    def ConfigureMenu(self):
        terminalMenu = TerminalMenu(self.PortListMenuItems ,clear_screen=False, title="Configuration Menu : \n Change Streams configs \n")
        ConfigureMenuEntryIndex = terminalMenu.show()
        if ConfigureMenuEntryIndex is None : return self.MainMenu()
        if ConfigureMenuEntryIndex >= self.App.preferences.max_streams :
             return self.MainMenu()
        else:
            selectedPort : Stream = self.App.stream_list[ConfigureMenuEntryIndex]
            if selectedPort.connected :
                print("This port is currently connected , Disonnect before configuration ! \n")
                return self.ConfigureMenu()
            else:
                return self.ConfigureMenu_SubMenu(selectedPort)
             
            


    def Preferences_menu(self):
        
        
        
        preference_menu_Items : list = ["[q] - Back"]

        preference_menu_Items.insert(0,"[1] - Configuration File Name - %s" %(self.App.preferences.config_name))
        preference_menu_Items.insert(1,"[2] - Line Termination - %s" %(str(self.App.preferences.get_line_termination())))
        preference_menu_Items.insert(2,"[3] - Max streams- %s" %(self.App.preferences.max_streams))
        preference_menu_Items.insert(3,"[4] - Startup connect")        
        
        def preferences_configurationFileName():
            print(f"Current file name : {self.App.preferences.config_name}")
            print("Enter a new name for the file")
            newname = input()
            self.App.preferences.config_name= newname
            return self.Preferences_menu()
        
        def preferences_lineTermination():
            print(f"Current line termination {self.App.preferences.get_line_termination()}")
            terminalMenu = TerminalMenu(["[1] - \\n" , "[2] - \\r" , "[3] - \\r\\n" , "[q] - Back"],clear_screen=False, title="Preferences Menu : Line Termination\n")
            lineTerminationMenuEntryIndex = terminalMenu.show()
            match lineTerminationMenuEntryIndex :
                case 0 :  self.App.preferences.line_termination = "\n"
                case 1 :  self.App.preferences.line_termination = "\r"
                case 2 :  self.App.preferences.line_termination = "\r\n"
                case _ : return self.Preferences_menu()
            return self.Preferences_menu()
        def preferences_maxStreams():
            print(f"Current max number of stream : {self.App.preferences.max_streams}")
            maxStreamList = ["[1] - 1","[2] - 2","[3] - 3","[4] - 4","[5] - 5","[6] - 6","[q] - Back"]
            terminalMenu = TerminalMenu(maxStreamList,clear_screen=False, title="Preferences Menu : Max number of stream\n")
            maxStreamMenuEntryIndex = terminalMenu.show()
            if maxStreamMenuEntryIndex < len(maxStreamList) - 1:
                self.App.preferences.max_streams = maxStreamMenuEntryIndex + 1
            return self.Preferences_menu()
        
        def preferences_StartupConnect():
            iterator = 0
            PreferencesStartupconnectMenuItems = []
            for startupConnect in self.App.preferences.connect : 
                PreferencesStartupconnectMenuItems.append("[%d] - Stream %d - %s" %(iterator,iterator,("True" if startupConnect else "False")))
                iterator +=1
            PreferencesStartupconnectMenuItems.append("[q] - Back") 
            terminalMenu = TerminalMenu(PreferencesStartupconnectMenuItems ,clear_screen=False, title="Preferences Menu : Startup connect\n")
            startupConnectMenuEntryIndex = terminalMenu.show()
            if startupConnectMenuEntryIndex <= len(self.App.preferences.connect) - 1:
                self.App.preferences.connect[startupConnectMenuEntryIndex] = not self.App.preferences.connect[startupConnectMenuEntryIndex]
                return preferences_StartupConnect()
            return self.Preferences_menu()
        
        terminalMenu = TerminalMenu(preference_menu_Items, clear_screen=False , title =" Preferences Menu")
        preferenceMenuEntryIndex = terminalMenu.show()
        match preferenceMenuEntryIndex : 
            case 0 : return preferences_configurationFileName()
            case 1 : return  preferences_lineTermination()
            case 2 : return preferences_maxStreams()
            case 3 : return preferences_StartupConnect()
            case _ : return self.MainMenu()



    def Connect_menu(self) :

        def connect_menu_select_StreamType (selectedPort : Stream):
            terminalMenu = TerminalMenu(self.connectDisconectItems ,clear_screen=False, title=" connect Menu : Stream %i %s %s\n to change the stream type , the stream need to be disconnected\n" %(selectedPort.id,"Connected" if selectedPort.connected else "Disconnected",self.getSettingsTitle(selectedPort) if selectedPort.connected else "") )
            ConfigureMenuEntryIndex = terminalMenu.show()
            match ConfigureMenuEntryIndex :
                case 0 : 
                        if selectedPort.connected : 
                            print(f"Stream {selectedPort.id} is already connected !")
                            return self.Connect_menu() 
                        else :
                            return connect(selectedPort)
                case 1 : return disconnect(selectedPort)
                case _ : return self.Connect_menu()                

        def disconnect(selectedPort : Stream):
            if selectedPort.connected : 
                selectedPort.disconnect()
            return self.Connect_menu()

        def connect(selectedPort : Stream):
            terminalMenu = TerminalMenu(self.configureStreamTypeMenuItems ,clear_screen=False, title=" connect Menu : Stream %i %s \n Choose wich type of stream you want\n" %(selectedPort.id,"Connected" if selectedPort.connected else "Disconnected" ))
            ConfigureMenuEntryIndex = terminalMenu.show()
            
            if ConfigureMenuEntryIndex is None : return self.MainMenu()
            if ConfigureMenuEntryIndex < len(self.configureStreamTypeMenuItems) - 1 :
                try : 
                    selectedPort.connect(Stream.stream_type(ConfigureMenuEntryIndex)) 
                except Exception as e:
                    print(f"Connection failed ! : {e}")  
            return self.Connect_menu()

        self._refreshMenuItems()
        terminalMenu = TerminalMenu(self.PortListMenuItems , title="connect Menu : \n Choose which stream you want to enable or disable\n" )
        ConfigureMenuEntryIndex =terminalMenu.show()
        if ConfigureMenuEntryIndex is None : return self.MainMenu()
        if ConfigureMenuEntryIndex < self.App.preferences.max_streams :
            selectedPort : Stream = self.App.stream_list[ConfigureMenuEntryIndex]
            return connect_menu_select_StreamType(selectedPort)
        return self.MainMenu()
    
    def ShowData_menu(self):
        terminalMenu = TerminalMenu(self.PortListMenuItems ,clear_screen=False, title="Show Data Menu : \n Select a stream \n" ,)
        showdataMenuEntryIndex = terminalMenu.show()
        if showdataMenuEntryIndex is None : return self.MainMenu()
        if showdataMenuEntryIndex < self.App.preferences.max_streams :
            selectedPort : Stream = self.App.stream_list[showdataMenuEntryIndex]
            settings_title = self.getSettingsTitle(selectedPort)
            terminalMenu = TerminalMenu(self.showDataMenuItems ,title =f"Show Data Menu : Stream {selectedPort.id}" +settings_title  )
            showdataMenuEntryIndex = terminalMenu.show()
            
            if showdataMenuEntryIndex is None : 
                return self.MainMenu()
            if showdataMenuEntryIndex >= len(self.showDataMenuItems) - 1 :
                return self.ShowData_menu()
            else :
                if selectedPort.connected is True : 
                    match showdataMenuEntryIndex : 
                        case 0 : 
                            selectedPort.toggle_incomming_data_visibility()
                            selectedPort.toggle_outgoing_data_visibility()
                        case 1 :
                            selectedPort.toggle_incomming_data_visibility()
                        case 2 :
                            selectedPort.toggle_outgoing_data_visibility()
                    self.stopShowDataEvent.clear()
                    self.showDataThread = threading.Thread(target=self._showDataTask , args=(selectedPort,))
                    self.showDataThread.start()
                    input()
                    print("Stop showing data")
                    self.stopShowDataEvent.set()
                    self.showDataThread.join()
            
                    match showdataMenuEntryIndex : 
                        case 0 : 
                            selectedPort.toggle_incomming_data_visibility()
                            selectedPort.toggle_outgoing_data_visibility()
                        case 1 :
                            selectedPort.toggle_incomming_data_visibility()
                        case 2 :
                            selectedPort.toggle_outgoing_data_visibility()
                    return self.ShowData_menu()
                else : 
                    print("Error : Selected Stream is not connected\n ")
                    return self.ShowData_menu()
        else : 
            return self.MainMenu()

    def LinkPort_menu(self): 
        terminalMenu = TerminalMenu(self.PortListMenuItems ,clear_screen=False, title="Link Menu : \n Link output data to a Stream\n" ,)
        LinkPortMenuEntryIndex = terminalMenu.show()
        if LinkPortMenuEntryIndex is None : return self.MainMenu()
        if LinkPortMenuEntryIndex < self.App.preferences.max_streams :
            selectedPort = self.App.stream_list[LinkPortMenuEntryIndex]
            self.LinkPort_link_menu(selectedPort)
        return self.MainMenu()
    
    def LinkPort_link_menu(self , selectedPort : Stream):

        def GetAvailableLinkList(selectedPort : Stream):
            availableLink = []
            for port in self.App.stream_list :
                if port is not selectedPort:
                    availableLink.append("[%d] - Stream %d %s" %(port.id,port.id,(" Linked " if port.id in selectedPort.linked_ports else "")))
                else : 
                    availableLink.append("[%d] - Stream %d ( Port can't link itself )" %(port.id,port.id))
            availableLink.append("[q] - Back")
            return availableLink
        
        availableStream = GetAvailableLinkList(selectedPort)
        terminalMenu = TerminalMenu( availableStream,clear_screen=False, title="chose Stream for output data\n" ,)
        LinkPortMenuEntryIndex = terminalMenu.show()
        if LinkPortMenuEntryIndex < len(availableStream)-1 : 
                if LinkPortMenuEntryIndex is not  selectedPort.id :
                    selectedPort.update_linked_ports(LinkPortMenuEntryIndex)
                else :
                    print("not possible !")
                return self.LinkPort_link_menu(selectedPort)
        return self.LinkPort_menu()

    def ConfigureMenu_SubMenu(self , selectedPort : Stream):
            terminalMenu = TerminalMenu(self.configureMenuSubmenuItems , clear_screen= False , title=f"Configuration Menu : \n Change Streams {selectedPort.id} configs \n")
            ConfigureMenuEntryIndex = terminalMenu.show()
            match ConfigureMenuEntryIndex :
                case 0 : self.Configure_Stream_StreamType_menu(selectedPort)
                case 1 : self.Configure_Stream_Script_menu(selectedPort,True)
                case 2 : self.Configure_Stream_Script_menu(selectedPort,False)
                case 3 : self.Configure_Stream_Logging_menu(selectedPort)
                case _ : return self.ConfigureMenu()
                
    def Configure_Stream_StreamType_menu(self,selectedPort : Stream):
        def Configure_Stream_TCP_menu():
            TCPSettings_menu_Items : list = ["[q] - Back"]

            TCPSettings_menu_Items.insert(0,"[1] - Host - %s" %(selectedPort.tcp_settings.host))
            TCPSettings_menu_Items.insert(1,"[2] - Port - %s" %(selectedPort.tcp_settings.port))
            TCPSettings_menu_Items.insert(2,"[3] - Stream Mode - %s" %(selectedPort.tcp_settings.StreamMode.value))   

            TCP_title = f"Configuration Menu : Stream {selectedPort.id} \n Current Configuration : \n Host : {selectedPort.tcp_settings.host} \n Port : {selectedPort.tcp_settings.port}\n StreamMode : {selectedPort.tcp_settings.StreamMode.value}\n "

            def Configure_TCP_Host_menu():
                print(TCP_title)
                print("Enter a valid hostname or IP address")
                print("note : if in server mode , host will be 127.0.0.1")
                newhost = input()
                try : 
                    if len(newhost) !=0 : 
                        socket.gethostbyname(newhost)
                        selectedPort.tcp_settings.set_host(newhost)
                except Exception as e :
                    print("Invalid host !")
                return Configure_Stream_TCP_menu()
            
            def Configure_TCP_Port_menu():
                print(TCP_title)
                print("Enter a valid port ")
                try : 
                    newport = int(input())
                    selectedPort.tcp_settings.set_port( newport)
                except Exception as e :
                    print("Invalid port !")
                return Configure_Stream_TCP_menu()
            

            def Configure_TCP_StreamMode_menu():
                terminalMenu= TerminalMenu( self.TCPSettingsStreamModeItems,clear_screen=False, title=TCP_title +"Stream mode Configuration\n" )
                menuEntryIndex = terminalMenu.show()
                if menuEntryIndex < len(self.TCPSettingsStreamModeItems) - 1:
                        selectedPort.tcp_settings.set_stream_mode(StreamMode[self.TCPSettingsStreamModeItems[menuEntryIndex]])
                return Configure_Stream_TCP_menu()

            terminalMenu= TerminalMenu(TCPSettings_menu_Items ,clear_screen=False, title="Configuration Menu : Stream %d \n TCP Configuration Menu" %(selectedPort.id) )
            configure_Stream_TCPMenuEntryIndex = terminalMenu.show()
            match configure_Stream_TCPMenuEntryIndex:
                case 0 : return Configure_TCP_Host_menu()
                case 1 : return Configure_TCP_Port_menu()
                case 2 : return Configure_TCP_StreamMode_menu()
                case _ : return self.Configure_Stream_StreamType_menu(selectedPort)

        def Configure_Stream_Serial_menu():
                
            SerialSettings_menu_Items : list = ["[q] - Back"]

            SerialSettings_menu_Items.insert(0,"[1] - Port - %s" %("None" if selectedPort.serial_settings.port is None else selectedPort.serial_settings.port))
            SerialSettings_menu_Items.insert(1,"[2] - BaudRate - %s" %(selectedPort.serial_settings.baudrate.value))
            SerialSettings_menu_Items.insert(2,"[3] - stopBits - %s" %(selectedPort.serial_settings.stopbits.value))   
            SerialSettings_menu_Items.insert(3,"[4] - Parity - %s" %(selectedPort.serial_settings.parity.value))     
            SerialSettings_menu_Items.insert(4,"[5] - Bytesize - %s" %(selectedPort.serial_settings.bytesize.value))        
            SerialSettings_menu_Items.insert(5,"[6] - Rtc-cts - %s" %(selectedPort.serial_settings.rtscts))
            
            Serial_title = f"Configuration Menu : Stream {selectedPort.id} \n Current Configuration : \n Port : {selectedPort.serial_settings.port} \n BaudRate : {selectedPort.serial_settings.baudrate.value}\n StopBits : {selectedPort.serial_settings.stopbits.value}\n Parity : {selectedPort.serial_settings.parity.value}\n Bytesize : {selectedPort.serial_settings.bytesize.value}\n Rtc-cts : {selectedPort.serial_settings.rtscts}\n"


            def Configure_Serial_Port_menu():
                AvailableStreams = SerialSettings.get_available_port()
                AvailableStreams_temps =[]
                found = False
                for AvailablePort in AvailableStreams :
                    
                    for port in self.App.stream_list:
                        if port.serial_settings is not None:
                            if port.serial_settings.port is not None:
                                if AvailablePort[0] in port.serial_settings.port :
                                    found = True
                    if found  == False:
                        AvailableStreams_temps.append(AvailablePort) 
                    found = False   

                iterator = 0 
                ConfigureMenu_port_items = ["[d] - disconnect","[q] - Back"]
                if AvailableStreams_temps is not None:
                    for AvailablePort in AvailableStreams_temps :
                        ConfigureMenu_port_items.insert(iterator,"[%d] %s - %s" %(iterator + 1,AvailablePort[0],AvailablePort[1]))
                        iterator +=1

                terminalMenu= TerminalMenu(ConfigureMenu_port_items ,clear_screen=False, title=Serial_title + "Configure Stream's port \n")
                menuEntryIndex = terminalMenu.show()

                if menuEntryIndex >= iterator :
                    if menuEntryIndex == iterator:
                        selectedPort.serial_settings.set_port("")
                    return Configure_Stream_Serial_menu()
                else:
                    selectedPort.serial_settings.set_port(AvailableStreams_temps[menuEntryIndex][0])
                    return Configure_Stream_Serial_menu()
            

            def Configure_Serial_BaudRate_menu():
                terminalMenu= TerminalMenu( self.SerialSettingsBaudRateItems,clear_screen=False, title=Serial_title +"Configure Stream's Baudrate \n")
                menuEntryIndex = terminalMenu.show()
                if menuEntryIndex < len(self.SerialSettingsBaudRateItems) - 1:
                    selectedPort.serial_settings.set_baudrate(BaudRate( self.SerialSettingsBaudRateItems[menuEntryIndex]))
                return Configure_Stream_Serial_menu()

            def Configure_Serial_Parity_menu():
                terminalMenu= TerminalMenu( self.SerialSettingsParityItems,clear_screen=False, title=Serial_title +"Configure Stream's Parity \n")
                menuEntryIndex = terminalMenu.show()
                if menuEntryIndex < len(self.SerialSettingsParityItems) - 1:
                        selectedPort.serial_settings.set_parity(Parity["PARITY_"+self.SerialSettingsParityItems[menuEntryIndex]])
                return Configure_Stream_Serial_menu()
            
            def Configure_Serial_StopBits_menu():
                terminalMenu= TerminalMenu( self.SerialSettingsStopBitsItems,clear_screen=False, title=Serial_title+"Configure Stream's StopBits \n")
                menuEntryIndex = terminalMenu.show()
                if menuEntryIndex < len(self.SerialSettingsStopBitsItems) - 1:
                        selectedPort.serial_settings.set_stopbits(StopBits["STOPBITS_" + self.SerialSettingsStopBitsItems[menuEntryIndex]])
                return Configure_Stream_Serial_menu()
            
            def Configure_Serial_Bytesize_menu():
                terminalMenu= TerminalMenu( self.SerialSettingsBytesizeItems,clear_screen=False, title=Serial_title+"Configure Stream's StopBits \n")
                menuEntryIndex = terminalMenu.show()
                if menuEntryIndex < len(self.SerialSettingsBytesizeItems) - 1:
                        selectedPort.serial_settings.set_bytesize(ByteSize[self.SerialSettingsBytesizeItems[menuEntryIndex]])
                return Configure_Stream_Serial_menu()

            def Configure_Serial_RTSCTS_menu():
                if selectedPort.serial_settings.rtscts is True :
                    selectedPort.serial_settings.set_rtscts(False)
                else:
                    selectedPort.serial_settings.set_rtscts(True)
                return Configure_Stream_Serial_menu()
            
            terminalMenu= TerminalMenu(SerialSettings_menu_Items ,clear_screen=False, title="Configuration Menu : Stream %d \n Serial Configuration Menu" %(selectedPort.id) )
            configure_Stream_SerialMenuEntryIndex = terminalMenu.show()
            match configure_Stream_SerialMenuEntryIndex:
                case 0 : return Configure_Serial_Port_menu()
                case 1 : return Configure_Serial_BaudRate_menu()
                case 2 : return Configure_Serial_StopBits_menu()
                case 3 : return Configure_Serial_Parity_menu()
                case 4 : return Configure_Serial_Bytesize_menu()
                case 5 : return Configure_Serial_RTSCTS_menu()
                case _ : return self.Configure_Stream_StreamType_menu(selectedPort)

        def Configure_Stream_UDP_menu():
            UDPSettings_menu_Items : list =[]
            if selectedPort.udp_settings.specific_host:
                UDPSettings_menu_Items.insert(0,"[1] - Specific Host - %s" %(selectedPort.udp_settings.host))

            UDPSettings_menu_Items.insert(1,"[2] - Port - %s" %(selectedPort.udp_settings.port))
            UDPSettings_menu_Items.insert(2,"[3] - Stream to specific Host - %s" %(  selectedPort.udp_settings.specific_host ))
            UDPSettings_menu_Items.insert(3,"[4] - Data Flow Mode - %s"%(str(selectedPort.udp_settings.DataFlow).replace("DataFlow.","")) )
            UDPSettings_menu_Items.append("[q] - Back")
            UDP_title = f"Configuration Menu : Stream {selectedPort.id} \n Current Configuration : \n Host : {selectedPort.udp_settings.host}\n Port : {selectedPort.udp_settings.port}\n Specific Host : {selectedPort.udp_settings.specific_host}\n Data Flow Mode : {str(selectedPort.udp_settings.DataFlow).replace('DataFlow.','')}\n"

            def Configure_UDP_Host_menu():
                print(UDP_title)
                print("Enter a valid hostname or Ip address")
                newhost = input()
                try : 
                    if len(newhost) !=0:
                        socket.gethostbyname(newhost)
                        selectedPort.tcp_settings.set_host(newhost)
                except Exception as e :
                    print("Invalid hostname or IP address !")
                return Configure_Stream_UDP_menu()
            
            def Configure_UDP_Port_menu():
                print(UDP_title)
                print("Enter a valid port ")
                try : 
                    newport = int(input())
                    if newport is not None:
                        selectedPort.tcp_settings.set_port( newport)
                except Exception as e :
                    print("Invalid port !")
                return Configure_Stream_UDP_menu()
            
            def Configure_UDP_SpecificHost_menu():
                selectedPort.udp_settings.specific_host = False if selectedPort.udp_settings.specific_host else True 
                return Configure_Stream_UDP_menu()
            
            def Configure_UDP_DataFlow_menu():
                terminalMenu= TerminalMenu( self.UDPSettingsDataFlowItems,clear_screen=False, title=UDP_title + "Configure Stream's Dataflow\n")
                menuEntryIndex = terminalMenu.show()
                if menuEntryIndex < len(self.UDPSettingsDataFlowItems) - 1:
                        selectedPort.udp_settings.DataFlow = DataFlow[self.UDPSettingsDataFlowItems[menuEntryIndex]]
                return Configure_Stream_UDP_menu()

            terminalMenu= TerminalMenu(UDPSettings_menu_Items ,clear_screen=False, title="Configuration Menu : Stream %d \n UDP Configuration Menu" %(selectedPort.id) )
            configure_Stream_UDPMenuEntryIndex = terminalMenu.show()
            if selectedPort.udp_settings.specific_host is False : configure_Stream_UDPMenuEntryIndex += 1

            match configure_Stream_UDPMenuEntryIndex:
                case 0 : return Configure_UDP_Host_menu() if selectedPort.udp_settings.specific_host else Configure_Stream_UDP_menu()
                case 1 : return Configure_UDP_Port_menu()
                case 2 : return Configure_UDP_SpecificHost_menu()
                case 3 : return Configure_UDP_DataFlow_menu()
                case _ : return self.Configure_Stream_StreamType_menu(selectedPort)

        def Configure_Stream_NTRIP_menu():
            NTRIPSettings_menu_Items : list =[]
            NTRIPSettings_menu_Items.insert(0,"[1] - Host - %s" %(selectedPort.ntrip_client.ntrip_settings.host))
            NTRIPSettings_menu_Items.insert(1,"[2] - Port - %s" %(selectedPort.ntrip_client.ntrip_settings.port))
            NTRIPSettings_menu_Items.insert(2,"[3] - Mountpoint - %s" %(selectedPort.ntrip_client.ntrip_settings.mountpoint))
            NTRIPSettings_menu_Items.insert(3,"[4] - Authentification - %s" %("Enabled" if selectedPort.ntrip_client.ntrip_settings.auth else "Disabled"))
            NTRIPSettings_menu_Items.insert(4,"[5] - Username - %s" %(selectedPort.ntrip_client.ntrip_settings.username))
            NTRIPSettings_menu_Items.insert(5,"[6] - Password - %s" %(selectedPort.ntrip_client.ntrip_settings.password))
            NTRIPSettings_menu_Items.append("[q] - Back")
            NTRIP_title = f"Configuration Menu : Stream {selectedPort.id} \n Current Configuration : \n Host : {selectedPort.ntrip_client.ntrip_settings.host}\n Port : {selectedPort.ntrip_client.ntrip_settings.port}\n Username : {selectedPort.ntrip_client.ntrip_settings.username}\n Password : {selectedPort.ntrip_client.ntrip_settings.password}\n Mountpoint : {selectedPort.ntrip_client.ntrip_settings.mountpoint}\n"

            def Configure_NTRIP_Host_menu():
                print(NTRIP_title)
                print("Enter a valid hostname or Ip address")
                newhost = input()
                try : 
                    if len(newhost) !=0:
                        socket.gethostbyname(newhost)
                        selectedPort.ntrip_client.set_settings_host(newhost)
                except Exception as e :
                    print("Invalid hostname or IP address !")
                return Configure_Stream_NTRIP_menu()
            
            def Configure_NTRIP_Port_menu():
                print(NTRIP_title)
                print("Enter a valid port ")
                try : 
                    newport = int(input())
                    if newport is not None:
                        selectedPort.ntrip_client.ntrip_settings.set_port( newport)
                except Exception as e :
                    print("Invalid port !")
                return Configure_Stream_NTRIP_menu()
            
            def Configure_NTRIP_Mountpoint_menu():
                print(NTRIP_title)
                if selectedPort.ntrip_client.ntrip_settings.host is not None and selectedPort.ntrip_client.ntrip_settings.sourceTable is not None: 
                    listofMountPoint = []
                    for sourceTable in selectedPort.ntrip_client.ntrip_settings.sourceTable:
                        listofMountPoint.append(sourceTable.mountpoint)
                    listofMountPoint.append("[q] - Back")
                    terminalMenu = TerminalMenu(listofMountPoint ,clear_screen=False, title="Configuration Menu : Stream %d \n NTRIP Configuration Menu \n Choose a mountpoint \n" %(selectedPort.id) )
                    mountPointIndex = terminalMenu.show()
                    if mountPointIndex < len(listofMountPoint) - 1 :
                        selectedPort.ntrip_client.ntrip_settings.setMountpoint(listofMountPoint[mountPointIndex])
                return Configure_Stream_NTRIP_menu()
            
            def Configure_NTRIP_Username_menu():
                print(NTRIP_title)
                print("Enter a valid username ")
                newusername = input()
                if len(newusername) !=0:
                    selectedPort.ntrip_client.ntrip_settings.setUsername(newusername)
                return Configure_Stream_NTRIP_menu()
            
            def Configure_NTRIP_Password_menu():
                print(NTRIP_title)
                print("Enter a valid password ")
                newpassword = input()
                if len(newpassword) !=0:
                    selectedPort.ntrip_client.ntrip_settings.setPassword(newpassword)
                return Configure_Stream_NTRIP_menu()
            
            def Configure_NTRIP_Auth_menu():
                selectedPort.ntrip_client.ntrip_settings.auth = False if selectedPort.ntrip_client.ntrip_settings.auth else True
                return Configure_Stream_NTRIP_menu()

            terminalMenu= TerminalMenu(NTRIPSettings_menu_Items ,clear_screen=False, title="Configuration Menu : Stream %d \n NTRIP Configuration Menu" %(selectedPort.id) )
            configure_Stream_UDPMenuEntryIndex = terminalMenu.show()
            match configure_Stream_UDPMenuEntryIndex:
                case 0 : return Configure_NTRIP_Host_menu()
                case 1 : return Configure_NTRIP_Port_menu()
                case 2 : return Configure_NTRIP_Mountpoint_menu()
                case 3 : return Configure_NTRIP_Auth_menu()
                case 4 : return Configure_NTRIP_Username_menu()
                case 5 : return Configure_NTRIP_Password_menu()
                case _ : return self.Configure_Stream_StreamType_menu(selectedPort)


        terminalMenu= TerminalMenu(self.configureStreamTypeMenuItems,clear_screen=False , title="Configuration Menu : Stream %d \n  select which type of stream you want to configure \n" %(selectedPort.id) )
        configure_StreamMenuEntryIndex = terminalMenu.show()
        match configure_StreamMenuEntryIndex:
                case 0 : return Configure_Stream_Serial_menu()
                case 1 : return Configure_Stream_TCP_menu()   
                case 2 : return Configure_Stream_UDP_menu()   
                case 3 : return Configure_Stream_NTRIP_menu()      
                case _ : return self.ConfigureMenu_SubMenu(selectedPort)
    
    def Configure_Stream_Script_menu(self, selectedPort : Stream , startup : bool):
        if startup : 
            configureScriptMenuItems=[f"[1] - Startup Script - {selectedPort.send_startup_script}",f"[2] - Script file - {selectedPort.startup_script}","[q] - Back"]
        else :
            configureScriptMenuItems=[f"[1] - Closeup Script - {selectedPort.send_close_script}",f"[2] - Script file - {selectedPort.close_script}","[q] - Back"]
        def Configure_Script():
            if startup : 
                selectedPort.set_startup_script()
            else : 
                selectedPort.set_close_script()
            return self.Configure_Stream_Script_menu(selectedPort , startup)
            
        def Configure_ScriptFile_menu():
                print("Enter the path to the Script file")
                new_path = input()
                try : 
                    if len(new_path) !=0 : 
                        if startup : 
                            selectedPort.set_startup_script_path(new_path)
                        else :
                            selectedPort.set_close_script_path(new_path)
                except Exception as e :
                    print(f"Invalid path ! , {e}")
                return self.Configure_Stream_Script_menu(selectedPort , startup)
            
        terminalMenu = TerminalMenu(configureScriptMenuItems,clear_screen=False, title="")
        choice_index = terminalMenu.show()
        match choice_index : 
            case 0 : return Configure_Script()
            case 1 : return Configure_ScriptFile_menu()
            case _ : return self.ConfigureMenu()
    
    def Configure_Stream_Logging_menu(self,selectedPort : Stream ):
        
        configureLoggingMenuItems=[f"[1] - Logging - {str(selectedPort.logging)}",f"[2] - Logging Filename - {selectedPort.logging_file}","[q] - Back"]
        
        def Configure_logging():
            selectedPort.set_logging()
            return self.Configure_Stream_Logging_menu(selectedPort)
        def Configure_Logging_FileName_menu():
                print("Enter the path to the Script file")
                new_path = input()
                try : 
                    if len(new_path) !=0 : 
                            selectedPort.set_logging_file_name(new_path)
                except Exception as e :
                    print(f"Invalid path ! , {e}")
                return self.Configure_Stream_Logging_menu(selectedPort)
            
        terminalMenu = TerminalMenu(configureLoggingMenuItems, title="")
        choice_index = terminalMenu.show()
        match choice_index : 
            case 0 : return Configure_logging()
            case 1 : return Configure_Logging_FileName_menu()
            case _ : return self.ConfigureMenu()
      
          
    
    
    def getSettingsTitle(self, selectedPort : Stream):
        currentSettings = selectedPort.to_string()
        if currentSettings is None :
            return "\n No settings"
        else : 
            return f"\n Current Settings : \n {currentSettings} \n"