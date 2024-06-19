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
try : 
    from simple_term_menu import TerminalMenu 
except: 
    print("WARNING : You are running pyDataLink on a system that doesn't support TUI interface !")
from ..StreamConfig import DataFlow , StreamMode , App , StreamType , Stream , BaudRate , Parity , StopBits , ByteSize , SerialSettings




class TerminalUserInterface :
    
    # Menu Items 
    mainMenuItems = ["[1] - Configure Stream" , "[2] - Connect / Disconnect","[3] - ShowData" ,"[4] - Link","[5] - Preferences","[q] - Exit"]
    connectDisconectItems=["[1] - Connect","[2] - Disconnect" ,"[q] - Back to stream selection"]
    showDataMenuItems=["[1] - show all data","[2] - Show Input data" , "[3] - Show Output data","[q] - Back to stream selection"]

    
    PortListMenuItems = ["[q] - Back to main menu"]

    configureMenuSubmenuItems = ["[1] - Stream Config","[2] - Connect Script", "[3] - Close Script" ,"[4] - Logging" , "[q] - Back to stream selection"]
    
    configureStreamTypeMenuItems=[]
    
    SerialSettingsBaudRateItems =[]
    SerialSettingsParityItems =[]
    SerialSettingsStopBitsItems =[]
    SerialSettingsBytesizeItems = []

    TCPSettingsStreamModeItems = []

    UDPSettingsDataFlowItems = []


    def __init__(self ,app : App ) -> None:
        self.App : App = app
        for port , i in zip(app.StreamList , range(len(app.StreamList))):
           self.PortListMenuItems.insert(i,"[%d] - Stream %d - %s %s" %(i ,i ,( "Connected" if port.connected else "Disonnected") ,  ("" if port.StreamType is None else str(port.StreamType).replace("StreamType.","- "))))
        self._CreateMenus()
        
        self.showDataThread : threading.Thread = None
        self.stopShowDataEvent = threading.Event()
        
    def _showDataTask(self, selectedPort : Stream):
        while self.stopShowDataEvent.is_set() is False:
            if selectedPort.DataToShow.empty() is False :
                print(selectedPort.DataToShow.get())
        return 0
                

    def _refreshMenuItems(self) :

        for port , i in zip(self.App.StreamList , range(len(self.App.StreamList))):
           self.PortListMenuItems[i] = "[%d] - Stream %d - %s %s" %(i ,i ,( "Connected" if port.connected else "Disonnected") , ("" if port.StreamType is None else str(port.StreamType).replace("StreamType.","- ")))
       

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
        for type in StreamType :
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
                self.App.CloseAll()
                sys.exit()
      
    def ConfigureMenu(self):
        terminalMenu = TerminalMenu(self.PortListMenuItems ,clear_screen=False, title="Configuration Menu : \n Change Streams configs \n")
        ConfigureMenuEntryIndex = terminalMenu.show()
        if ConfigureMenuEntryIndex is None : return self.MainMenu()
        if ConfigureMenuEntryIndex >= self.App.preferences.maxStreams :
             return self.MainMenu()
        else:
            selectedPort : Stream = self.App.StreamList[ConfigureMenuEntryIndex]
            if selectedPort.connected :
                print("This port is currently connected , Disonnect before configuration ! \n")
                return self.ConfigureMenu()
            else:
                return self.ConfigureMenu_SubMenu(selectedPort)
             
            


    def Preferences_menu(self):
        
        
        
        preference_menu_Items : list = ["[q] - Back"]

        preference_menu_Items.insert(0,"[1] - Configuration File Name - %s" %(self.App.preferences.configName))
        preference_menu_Items.insert(1,"[2] - Line Termination - %s" %(str(self.App.preferences.getLineTermination())))
        preference_menu_Items.insert(2,"[3] - Max streams- %s" %(self.App.preferences.maxStreams))
        preference_menu_Items.insert(3,"[4] - Startup Connect")        
        
        def preferences_configurationFileName():
            print(f"Current file name : {self.App.preferences.configName}")
            print("Enter a new name for the file")
            newname = input()
            self.App.preferences.configName= newname
            return self.Preferences_menu()
        
        def preferences_lineTermination():
            print(f"Current line termination {self.App.preferences.getLineTermination()}")
            terminalMenu = TerminalMenu(["[1] - \\n" , "[2] - \\r" , "[3] - \\r\\n" , "[q] - Back"],clear_screen=False, title="Preferences Menu : Line Termination\n")
            lineTerminationMenuEntryIndex = terminalMenu.show()
            match lineTerminationMenuEntryIndex :
                case 0 :  self.App.preferences.lineTermination = "\n"
                case 1 :  self.App.preferences.lineTermination = "\r"
                case 2 :  self.App.preferences.lineTermination = "\r\n"
                case _ : return self.Preferences_menu()
            return self.Preferences_menu()
        def preferences_maxStreams():
            print(f"Current max number of stream : {self.App.preferences.maxStreams}")
            maxStreamList = ["[1] - 1","[2] - 2","[3] - 3","[4] - 4","[5] - 5","[6] - 6","[q] - Back"]
            terminalMenu = TerminalMenu(maxStreamList,clear_screen=False, title="Preferences Menu : Max number of stream\n")
            maxStreamMenuEntryIndex = terminalMenu.show()
            if maxStreamMenuEntryIndex < len(maxStreamList) - 1:
                self.App.preferences.maxStreams = maxStreamMenuEntryIndex + 1
            return self.Preferences_menu()
        
        def preferences_StartupConnect():
            iterator = 0
            PreferencesStartupconnectMenuItems = []
            for startupConnect in self.App.preferences.Connect : 
                PreferencesStartupconnectMenuItems.append("[%d] - Stream %d - %s" %(iterator,iterator,("True" if startupConnect else "False")))
                iterator +=1
            PreferencesStartupconnectMenuItems.append("[q] - Back") 
            terminalMenu = TerminalMenu(PreferencesStartupconnectMenuItems ,clear_screen=False, title="Preferences Menu : Startup Connect\n")
            startupConnectMenuEntryIndex = terminalMenu.show()
            if startupConnectMenuEntryIndex <= len(self.App.preferences.Connect) - 1:
                self.App.preferences.Connect[startupConnectMenuEntryIndex] = not self.App.preferences.Connect[startupConnectMenuEntryIndex]
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
            terminalMenu = TerminalMenu(self.connectDisconectItems ,clear_screen=False, title=" Connect Menu : Stream %i %s %s\n to change the stream type , the stream need to be disconnected\n" %(selectedPort.id,"Connected" if selectedPort.connected else "Disconnected",self.getSettingsTitle(selectedPort) if selectedPort.connected else "") )
            ConfigureMenuEntryIndex = terminalMenu.show()
            match ConfigureMenuEntryIndex :
                case 0 : 
                        if selectedPort.connected : 
                            print(f"Stream {selectedPort.id} is already connected !")
                            return self.Connect_menu() 
                        else :
                            return Connect(selectedPort)
                case 1 : return Disconnect(selectedPort)
                case _ : return self.Connect_menu()                

        def Disconnect(selectedPort : Stream):
            if selectedPort.connected : 
                selectedPort.Disconnect()
            return self.Connect_menu()

        def Connect(selectedPort : Stream):
            terminalMenu = TerminalMenu(self.configureStreamTypeMenuItems ,clear_screen=False, title=" Connect Menu : Stream %i %s \n Choose wich type of stream you want\n" %(selectedPort.id,"Connected" if selectedPort.connected else "Disconnected" ))
            ConfigureMenuEntryIndex = terminalMenu.show()
            
            if ConfigureMenuEntryIndex is None : return self.MainMenu()
            if ConfigureMenuEntryIndex < len(self.configureStreamTypeMenuItems) - 1 :
                try : 
                    selectedPort.Connect(StreamType(ConfigureMenuEntryIndex)) 
                except Exception as e:
                    print(f"Connection failed ! : {e}")  
            return self.Connect_menu()

        self._refreshMenuItems()
        terminalMenu = TerminalMenu(self.PortListMenuItems , title="Connect Menu : \n Choose which stream you want to enable or disable\n" )
        ConfigureMenuEntryIndex =terminalMenu.show()
        if ConfigureMenuEntryIndex is None : return self.MainMenu()
        if ConfigureMenuEntryIndex < self.App.preferences.maxStreams :
            selectedPort : Stream = self.App.StreamList[ConfigureMenuEntryIndex]
            return connect_menu_select_StreamType(selectedPort)
        return self.MainMenu()
    
    def ShowData_menu(self):
        terminalMenu = TerminalMenu(self.PortListMenuItems ,clear_screen=False, title="Show Data Menu : \n Select a stream \n" ,)
        showdataMenuEntryIndex = terminalMenu.show()
        if showdataMenuEntryIndex is None : return self.MainMenu()
        if showdataMenuEntryIndex < self.App.preferences.maxStreams :
            selectedPort : Stream = self.App.StreamList[showdataMenuEntryIndex]
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
                            selectedPort.ToggleInputDataVisibility()
                            selectedPort.ToggleOutputDataVisibility()
                        case 1 :
                            selectedPort.ToggleInputDataVisibility()
                        case 2 :
                            selectedPort.ToggleOutputDataVisibility()
                    self.stopShowDataEvent.clear()
                    self.showDataThread = threading.Thread(target=self._showDataTask , args=(selectedPort,))
                    self.showDataThread.start()
                    input()
                    print("Stop showing data")
                    self.stopShowDataEvent.set()
                    self.showDataThread.join()
            
                    match showdataMenuEntryIndex : 
                        case 0 : 
                            selectedPort.ToggleInputDataVisibility()
                            selectedPort.ToggleOutputDataVisibility()
                        case 1 :
                            selectedPort.ToggleInputDataVisibility()
                        case 2 :
                            selectedPort.ToggleOutputDataVisibility()
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
        if LinkPortMenuEntryIndex < self.App.preferences.maxStreams :
            selectedPort = self.App.StreamList[LinkPortMenuEntryIndex]
            self.LinkPort_link_menu(selectedPort)
        return self.MainMenu()
    
    def LinkPort_link_menu(self , selectedPort : Stream):

        def GetAvailableLinkList(selectedPort : Stream):
            availableLink = []
            for port in self.App.StreamList :
                if port is not selectedPort:
                    availableLink.append("[%d] - Stream %d %s" %(port.id,port.id,(" Linked " if port.id in selectedPort.linkedPort else "")))
                else : 
                    availableLink.append("[%d] - Stream %d ( Port can't link itself )" %(port.id,port.id))
            availableLink.append("[q] - Back")
            return availableLink
        
        availableStream = GetAvailableLinkList(selectedPort)
        terminalMenu = TerminalMenu( availableStream,clear_screen=False, title="chose Stream for output data\n" ,)
        LinkPortMenuEntryIndex = terminalMenu.show()
        if LinkPortMenuEntryIndex < len(availableStream)-1 : 
                if LinkPortMenuEntryIndex is not  selectedPort.id :
                    selectedPort.UpdatelinkedPort(LinkPortMenuEntryIndex)
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

            TCPSettings_menu_Items.insert(0,"[1] - Host - %s" %(selectedPort.tcpSettings.host))
            TCPSettings_menu_Items.insert(1,"[2] - Port - %s" %(selectedPort.tcpSettings.port))
            TCPSettings_menu_Items.insert(2,"[3] - Stream Mode - %s" %(selectedPort.tcpSettings.StreamMode.value))   

            TCP_title = f"Configuration Menu : Stream {selectedPort.id} \n Current Configuration : \n Host : {selectedPort.tcpSettings.host} \n Port : {selectedPort.tcpSettings.port}\n StreamMode : {selectedPort.tcpSettings.StreamMode.value}\n "

            def Configure_TCP_Host_menu():
                print(TCP_title)
                print("Enter a valid hostname or IP address")
                print("note : if in server mode , host will be 127.0.0.1")
                newhost = input()
                try : 
                    if len(newhost) !=0 : 
                        socket.gethostbyname(newhost)
                        selectedPort.tcpSettings.setHost(newhost)
                except Exception as e :
                    print("Invalid host !")
                return Configure_Stream_TCP_menu()
            
            def Configure_TCP_Port_menu():
                print(TCP_title)
                print("Enter a valid port ")
                try : 
                    newport = int(input())
                    selectedPort.tcpSettings.setPort( newport)
                except Exception as e :
                    print("Invalid port !")
                return Configure_Stream_TCP_menu()
            

            def Configure_TCP_StreamMode_menu():
                terminalMenu= TerminalMenu( self.TCPSettingsStreamModeItems,clear_screen=False, title=TCP_title +"Stream mode Configuration\n" )
                menuEntryIndex = terminalMenu.show()
                if menuEntryIndex < len(self.TCPSettingsStreamModeItems) - 1:
                        selectedPort.tcpSettings.set_StreamMode(StreamMode[self.TCPSettingsStreamModeItems[menuEntryIndex]])
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

            SerialSettings_menu_Items.insert(0,"[1] - Port - %s" %("None" if selectedPort.serialSettings.port is None else selectedPort.serialSettings.port))
            SerialSettings_menu_Items.insert(1,"[2] - BaudRate - %s" %(selectedPort.serialSettings.baudrate.value))
            SerialSettings_menu_Items.insert(2,"[3] - stopBits - %s" %(selectedPort.serialSettings.stopbits.value))   
            SerialSettings_menu_Items.insert(3,"[4] - Parity - %s" %(selectedPort.serialSettings.parity.value))     
            SerialSettings_menu_Items.insert(4,"[5] - Bytesize - %s" %(selectedPort.serialSettings.bytesize.value))        
            SerialSettings_menu_Items.insert(5,"[6] - Rtc-cts - %s" %(selectedPort.serialSettings.rtscts))
            
            Serial_title = f"Configuration Menu : Stream {selectedPort.id} \n Current Configuration : \n Port : {selectedPort.serialSettings.port} \n BaudRate : {selectedPort.serialSettings.baudrate.value}\n StopBits : {selectedPort.serialSettings.stopbits.value}\n Parity : {selectedPort.serialSettings.parity.value}\n Bytesize : {selectedPort.serialSettings.bytesize.value}\n Rtc-cts : {selectedPort.serialSettings.rtscts}\n"


            def Configure_Serial_Port_menu():
                AvailableStreams = SerialSettings.GetAvailablePort()
                AvailableStreams_temps =[]
                found = False
                for AvailablePort in AvailableStreams :
                    
                    for port in self.App.StreamList:
                        if port.serialSettings is not None:
                            if port.serialSettings.port is not None:
                                if AvailablePort[0] in port.serialSettings.port :
                                    found = True
                    if found  == False:
                        AvailableStreams_temps.append(AvailablePort) 
                    found = False   

                iterator = 0 
                ConfigureMenu_port_items = ["[d] - Disconnect","[q] - Back"]
                if AvailableStreams_temps is not None:
                    for AvailablePort in AvailableStreams_temps :
                        ConfigureMenu_port_items.insert(iterator,"[%d] %s - %s" %(iterator + 1,AvailablePort[0],AvailablePort[1]))
                        iterator +=1

                terminalMenu= TerminalMenu(ConfigureMenu_port_items ,clear_screen=False, title=Serial_title + "Configure Stream's port \n")
                menuEntryIndex = terminalMenu.show()

                if menuEntryIndex >= iterator :
                    if menuEntryIndex == iterator:
                        selectedPort.serialSettings.setPort("")
                    return Configure_Stream_Serial_menu()
                else:
                    selectedPort.serialSettings.setPort(AvailableStreams_temps[menuEntryIndex][0])
                    return Configure_Stream_Serial_menu()
            

            def Configure_Serial_BaudRate_menu():
                terminalMenu= TerminalMenu( self.SerialSettingsBaudRateItems,clear_screen=False, title=Serial_title +"Configure Stream's Baudrate \n")
                menuEntryIndex = terminalMenu.show()
                if menuEntryIndex < len(self.SerialSettingsBaudRateItems) - 1:
                    selectedPort.serialSettings.set_baudrate(BaudRate( self.SerialSettingsBaudRateItems[menuEntryIndex]))
                return Configure_Stream_Serial_menu()

            def Configure_Serial_Parity_menu():
                terminalMenu= TerminalMenu( self.SerialSettingsParityItems,clear_screen=False, title=Serial_title +"Configure Stream's Parity \n")
                menuEntryIndex = terminalMenu.show()
                if menuEntryIndex < len(self.SerialSettingsParityItems) - 1:
                        selectedPort.serialSettings.set_parity(Parity["PARITY_"+self.SerialSettingsParityItems[menuEntryIndex]])
                return Configure_Stream_Serial_menu()
            
            def Configure_Serial_StopBits_menu():
                terminalMenu= TerminalMenu( self.SerialSettingsStopBitsItems,clear_screen=False, title=Serial_title+"Configure Stream's StopBits \n")
                menuEntryIndex = terminalMenu.show()
                if menuEntryIndex < len(self.SerialSettingsStopBitsItems) - 1:
                        selectedPort.serialSettings.set_stopbits(StopBits["STOPBITS_" + self.SerialSettingsStopBitsItems[menuEntryIndex]])
                return Configure_Stream_Serial_menu()
            
            def Configure_Serial_Bytesize_menu():
                terminalMenu= TerminalMenu( self.SerialSettingsBytesizeItems,clear_screen=False, title=Serial_title+"Configure Stream's StopBits \n")
                menuEntryIndex = terminalMenu.show()
                if menuEntryIndex < len(self.SerialSettingsBytesizeItems) - 1:
                        selectedPort.serialSettings.set_bytesize(ByteSize[self.SerialSettingsBytesizeItems[menuEntryIndex]])
                return Configure_Stream_Serial_menu()

            def Configure_Serial_RTSCTS_menu():
                if selectedPort.serialSettings.rtscts is True :
                    selectedPort.serialSettings.set_rtscts(False)
                else:
                    selectedPort.serialSettings.set_rtscts(True)
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
            if selectedPort.udpSettings.specificHost:
                UDPSettings_menu_Items.insert(0,"[1] - Specific Host - %s" %(selectedPort.udpSettings.host))

            UDPSettings_menu_Items.insert(1,"[2] - Port - %s" %(selectedPort.udpSettings.port))
            UDPSettings_menu_Items.insert(2,"[3] - Stream to specific Host - %s" %(  selectedPort.udpSettings.specificHost ))
            UDPSettings_menu_Items.insert(3,"[4] - Data Flow Mode - %s"%(str(selectedPort.udpSettings.DataFlow).replace("DataFlow.","")) )
            UDPSettings_menu_Items.append("[q] - Back")
            UDP_title = f"Configuration Menu : Stream {selectedPort.id} \n Current Configuration : \n Host : {selectedPort.udpSettings.host}\n Port : {selectedPort.udpSettings.port}\n Specific Host : {selectedPort.udpSettings.specificHost}\n Data Flow Mode : {str(selectedPort.udpSettings.DataFlow).replace('DataFlow.','')}\n"

            def Configure_UDP_Host_menu():
                print(UDP_title)
                print("Enter a valid hostname or Ip address")
                newhost = input()
                try : 
                    if len(newhost) !=0:
                        socket.gethostbyname(newhost)
                        selectedPort.tcpSettings.setHost(newhost)
                except Exception as e :
                    print("Invalid hostname or IP address !")
                return Configure_Stream_UDP_menu()
            
            def Configure_UDP_Port_menu():
                print(UDP_title)
                print("Enter a valid port ")
                try : 
                    newport = int(input())
                    if newport is not None:
                        selectedPort.tcpSettings.setPort( newport)
                except Exception as e :
                    print("Invalid port !")
                return Configure_Stream_UDP_menu()
            
            def Configure_UDP_SpecificHost_menu():
                selectedPort.udpSettings.specificHost = False if selectedPort.udpSettings.specificHost else True 
                return Configure_Stream_UDP_menu()
            
            def Configure_UDP_DataFlow_menu():
                terminalMenu= TerminalMenu( self.UDPSettingsDataFlowItems,clear_screen=False, title=UDP_title + "Configure Stream's Dataflow\n")
                menuEntryIndex = terminalMenu.show()
                if menuEntryIndex < len(self.UDPSettingsDataFlowItems) - 1:
                        selectedPort.udpSettings.DataFlow = DataFlow[self.UDPSettingsDataFlowItems[menuEntryIndex]]
                return Configure_Stream_UDP_menu()

            terminalMenu= TerminalMenu(UDPSettings_menu_Items ,clear_screen=False, title="Configuration Menu : Stream %d \n UDP Configuration Menu" %(selectedPort.id) )
            configure_Stream_UDPMenuEntryIndex = terminalMenu.show()
            if selectedPort.udpSettings.specificHost is False : configure_Stream_UDPMenuEntryIndex += 1

            match configure_Stream_UDPMenuEntryIndex:
                case 0 : return Configure_UDP_Host_menu() if selectedPort.udpSettings.specificHost else Configure_Stream_UDP_menu()
                case 1 : return Configure_UDP_Port_menu()
                case 2 : return Configure_UDP_SpecificHost_menu()
                case 3 : return Configure_UDP_DataFlow_menu()
                case _ : return self.Configure_Stream_StreamType_menu(selectedPort)

        def Configure_Stream_NTRIP_menu():
            NTRIPSettings_menu_Items : list =[]
            NTRIPSettings_menu_Items.insert(0,"[1] - Host - %s" %(selectedPort.ntripClient.ntripSettings.host))
            NTRIPSettings_menu_Items.insert(1,"[2] - Port - %s" %(selectedPort.ntripClient.ntripSettings.port))
            NTRIPSettings_menu_Items.insert(2,"[3] - Mountpoint - %s" %(selectedPort.ntripClient.ntripSettings.mountpoint))
            NTRIPSettings_menu_Items.insert(3,"[4] - Authentification - %s" %("Enabled" if selectedPort.ntripClient.ntripSettings.auth else "Disabled"))
            NTRIPSettings_menu_Items.insert(4,"[5] - Username - %s" %(selectedPort.ntripClient.ntripSettings.username))
            NTRIPSettings_menu_Items.insert(5,"[6] - Password - %s" %(selectedPort.ntripClient.ntripSettings.password))
            NTRIPSettings_menu_Items.append("[q] - Back")
            NTRIP_title = f"Configuration Menu : Stream {selectedPort.id} \n Current Configuration : \n Host : {selectedPort.ntripClient.ntripSettings.host}\n Port : {selectedPort.ntripClient.ntripSettings.port}\n Username : {selectedPort.ntripClient.ntripSettings.username}\n Password : {selectedPort.ntripClient.ntripSettings.password}\n Mountpoint : {selectedPort.ntripClient.ntripSettings.mountpoint}\n"

            def Configure_NTRIP_Host_menu():
                print(NTRIP_title)
                print("Enter a valid hostname or Ip address")
                newhost = input()
                try : 
                    if len(newhost) !=0:
                        socket.gethostbyname(newhost)
                        selectedPort.ntripClient.set_Settings_Host(newhost)
                except Exception as e :
                    print("Invalid hostname or IP address !")
                return Configure_Stream_NTRIP_menu()
            
            def Configure_NTRIP_Port_menu():
                print(NTRIP_title)
                print("Enter a valid port ")
                try : 
                    newport = int(input())
                    if newport is not None:
                        selectedPort.ntripClient.ntripSettings.setPort( newport)
                except Exception as e :
                    print("Invalid port !")
                return Configure_Stream_NTRIP_menu()
            
            def Configure_NTRIP_Mountpoint_menu():
                print(NTRIP_title)
                if selectedPort.ntripClient.ntripSettings.host is not None and selectedPort.ntripClient.ntripSettings.sourceTable is not None: 
                    listofMountPoint = []
                    for sourceTable in selectedPort.ntripClient.ntripSettings.sourceTable:
                        listofMountPoint.append(sourceTable.mountpoint)
                    listofMountPoint.append("[q] - Back")
                    terminalMenu = TerminalMenu(listofMountPoint ,clear_screen=False, title="Configuration Menu : Stream %d \n NTRIP Configuration Menu \n Choose a mountpoint \n" %(selectedPort.id) )
                    mountPointIndex = terminalMenu.show()
                    if mountPointIndex < len(listofMountPoint) - 1 :
                        selectedPort.ntripClient.ntripSettings.setMountpoint(listofMountPoint[mountPointIndex])
                return Configure_Stream_NTRIP_menu()
            
            def Configure_NTRIP_Username_menu():
                print(NTRIP_title)
                print("Enter a valid username ")
                newusername = input()
                if len(newusername) !=0:
                    selectedPort.ntripClient.ntripSettings.setUsername(newusername)
                return Configure_Stream_NTRIP_menu()
            
            def Configure_NTRIP_Password_menu():
                print(NTRIP_title)
                print("Enter a valid password ")
                newpassword = input()
                if len(newpassword) !=0:
                    selectedPort.ntripClient.ntripSettings.setPassword(newpassword)
                return Configure_Stream_NTRIP_menu()
            
            def Configure_NTRIP_Auth_menu():
                selectedPort.ntripClient.ntripSettings.auth = False if selectedPort.ntripClient.ntripSettings.auth else True
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
            configureScriptMenuItems=[f"[1] - Startup Script - {selectedPort.sendStartupScript}",f"[2] - Script file - {selectedPort.startupScript}","[q] - Back"]
        else :
            configureScriptMenuItems=[f"[1] - Closeup Script - {selectedPort.sendCloseScript}",f"[2] - Script file - {selectedPort.closeScript}","[q] - Back"]
        def Configure_Script():
            if startup : 
                selectedPort.setStartupScript()
            else : 
                selectedPort.setCloseScript()
            return self.Configure_Stream_Script_menu(selectedPort , startup)
            
        def Configure_ScriptFile_menu():
                print("Enter the path to the Script file")
                newpath = input()
                try : 
                    if len(newpath) !=0 : 
                        if startup : 
                            selectedPort.setStartupScriptPath(newpath)
                        else :
                            selectedPort.setCloseScriptPath(newpath)
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
        
        configureLoggingMenuItems=[f"[1] - Logging - {str(selectedPort.logging)}",f"[2] - Logging Filename - {selectedPort.loggingFile}","[q] - Back"]
        
        def Configure_logging():
            selectedPort.setLogging()
            return self.Configure_Stream_Logging_menu(selectedPort)
        def Configure_Logging_FileName_menu():
                print("Enter the path to the Script file")
                newpath = input()
                try : 
                    if len(newpath) !=0 : 
                            selectedPort.setLoggingFileName(newpath)
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
        currentSettings = selectedPort.toString()
        if currentSettings is None :
            return "\n No settings"
        else : 
            return f"\n Current Settings : \n {currentSettings} \n"