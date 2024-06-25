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

from src.StreamSettings.SerialSettings import BaudRate , Parity ,ByteSize , StopBits
from src.StreamSettings.TcpSettings import StreamMode
from src.StreamSettings.UdpSettings import DataFlow
from ..StreamConfig.Stream import  LogFileException, ScriptFileException, Stream, StreamException, StreamType
from ..StreamConfig.App import App
try :
    from simple_term_menu import TerminalMenu
except NotImplementedError as e :
    print("WARNING : You are running pyDataLink on a system that doesn't support TUI interface !")



class TerminalUserInterface :

    # Menu Items
    main_menu_items = ["[1] - Configure Stream" , "[2] - connect / disconnect",
                       "[3] - ShowData" ,"[4] - Link","[5] - Preferences","[q] - Exit"]

    connect_disconect_items=["[1] - connect","[2] - disconnect" ,"[q] - Back to stream selection"]
    show_data_menu_items=["[1] - show all data","[2] - Show Input data" ,
                          "[3] - Show Output data","[q] - Back to stream selection"]

    port_list_menu_items = ["[q] - Back to main menu"]

    configure_menu_submenu_items = ["[1] - Stream Config","[2] - connect Script",
                                    "[3] - Close Script" ,"[4] - Logging" , "[q] - Back to stream selection"]

    configure_stream_type_menu_items=[]

    serialsettings_baudrate_items =[]
    serialsettings_parity_items =[]
    serialsettings_stopbits_items =[]
    serialsettings_bytesize_items = []

    tcpsettings_stream_mode_items = []

    udpsettings_dataflow_items = []


    def __init__(self ,app : App ) -> None:
        self.app : App = app
        for port , i in zip(app.stream_list , range(len(app.stream_list))):
           self.port_list_menu_items.insert(i,f"[{i}] - Stream {i} - {"Connected" if port.connected else "Disonnected"} {"" if port.stream_type is None else str(port.stream_type).replace("StreamType.","- ")}")
        self._create_menus()

        self.show_data_thread : threading.Thread = None
        self.stop_show_data_event = threading.Event()

    def _show_data_task(self, selected_port : Stream):
        while self.stop_show_data_event.is_set() is False:
            if selected_port.data_to_show.empty() is False :
                print(selected_port.data_to_show.get())
        return 0


    def _refresh_menu_items(self) :

        for port , i in zip(self.app.stream_list , range(len(self.app.stream_list))):
           self.port_list_menu_items[i] = f"[{i}] - Stream {i} - {"Connected" if port.connected else "Disonnected"} {"" if port.stream_type is None else str(port.stream_type).replace("StreamType.","- ")}"


    def _create_menus(self):

        #BaudRate Menu
        for baudrate in BaudRate :
            self.serialsettings_baudrate_items.append(baudrate.value)
        self.serialsettings_baudrate_items.append("[q] - Back")

        #Parity Menu
        for parity in Parity :
            self.serialsettings_parity_items.append(str(parity).replace("Parity.PARITY_",""))
        self.serialsettings_parity_items.append("[q] - Back")

        #StopBits Menu
        for stopbits in StopBits :
            self.serialsettings_stopbits_items.append(str(stopbits).replace("StopBits.STOPBITS_",""))
        self.serialsettings_stopbits_items.append("[q] - Back")

         #Bytesize Menu
        for bytesize in ByteSize :
            self.serialsettings_bytesize_items.append(str(bytesize).replace("ByteSize.",""))
        self.serialsettings_bytesize_items.append("[q] - Back")

        #StreamMode Menu
        for mode in StreamMode :
            self.tcpsettings_stream_mode_items.append(str(mode).replace("StreamMode.",""))
        self.tcpsettings_stream_mode_items.append("[q] - Back")

        #StreamType
        iterator = 1
        for stream_type in StreamType :
            if stream_type.value is not None:
                self.configure_stream_type_menu_items.append(f"[{iterator}] - {str(stream_type).replace("StreamType.","")}" )
                iterator+=1
        self.configure_stream_type_menu_items.append("[q] - Back")

        # DataFlow
        for flow in DataFlow :
            self.udpsettings_dataflow_items.append(str(flow).replace("DataFlow.",""))
        self.udpsettings_dataflow_items.append("[q] - Back")

# Main menu
    def main_menu(self) :
        """Main menu of TUI
        """
        terminal_menu = TerminalMenu(self.main_menu_items ,clear_screen=True,
                                     title="PyDatalink\n you are using pyDatalink App in Terminal UI mode \n")
        menu_entry_index = terminal_menu.show()
        match menu_entry_index:
            case 0 : self.configure_menu()
            case 1 : self.connect_menu()
            case 2 : self.showdata_menu()
            case 3 : self.link_port_menu()
            case 4 : self.preferences_menu()
            case _ :
                self.app.close_all()
                sys.exit()

    def configure_menu(self):
        """Configuration menu 
        """
        terminal_menu = TerminalMenu(self.port_list_menu_items ,clear_screen=False,
                                     title="Configuration Menu : \n Change Streams configs \n")

        configure_menu_entry_index = terminal_menu.show()
        if configure_menu_entry_index is None or configure_menu_entry_index >= self.app.preferences.max_streams :
            return self.main_menu()
        else:
            selected_port : Stream = self.app.stream_list[configure_menu_entry_index]
            if selected_port.is_connected :
                print("This port is currently connected , Disonnect before configuration ! \n")
                return self.configure_menu()
            else:
                return self.configure_menu_submenu(selected_port)

    def preferences_menu(self):
        """Preferences menu
        """
        preference_menu_items : list = ["[q] - Back"]
        preference_menu_items.insert(0,f"[1] - Configuration File Name - {self.app.preferences.config_name}")
        preference_menu_items.insert(1,f"[2] - Line Termination - {str(self.app.preferences.get_line_termination())}")
        preference_menu_items.insert(2,f"[3] - Max streams- {self.app.preferences.max_streams}")
        preference_menu_items.insert(3,"[4] - Startup connect")

        def preferences_configuration_filename():
            print(f"Current file name : {self.app.preferences.config_name}")
            print("Enter a new name for the file")
            newname = input()
            self.app.preferences.config_name= newname
            return self.preferences_menu()

        def preferences_line_termination():
            print(f"Current line termination {self.app.preferences.get_line_termination()}")
            terminal_menu = TerminalMenu(["[1] - \\n" , "[2] - \\r" , "[3] - \\r\\n" , "[q] - Back"],
                                         clear_screen=False, title="Preferences Menu : Line Termination\n")
            line_termination_menu_entry_index = terminal_menu.show()
            match line_termination_menu_entry_index :
                case 0 :  self.app.preferences.line_termination = "\n"
                case 1 :  self.app.preferences.line_termination = "\r"
                case 2 :  self.app.preferences.line_termination = "\r\n"
                case _ : return self.preferences_menu()
            return self.preferences_menu()
        def preferences_max_streams():
            print(f"Current max number of stream : {self.app.preferences.max_streams}")
            max_stream_list = ["[1] - 1","[2] - 2","[3] - 3",
                               "[4] - 4","[5] - 5","[6] - 6","[q] - Back"]
            terminal_menu = TerminalMenu(max_stream_list,clear_screen=False,
                                         title="Preferences Menu : Max number of stream\n")
            max_stream_menu_entry_index = terminal_menu.show()
            if max_stream_menu_entry_index < len(max_stream_list) - 1:
                self.app.preferences.max_streams = max_stream_menu_entry_index + 1
            return self.preferences_menu()

        def preferences_startup_connect():
            iterator = 0
            preferences_startup_connect_menu_items = []
            for startup_connect in self.app.preferences.connect :
                preferences_startup_connect_menu_items.append(f"[{iterator}] - Stream {iterator} - {"True" if startup_connect else "False"}" )
                iterator +=1
            preferences_startup_connect_menu_items.append("[q] - Back")
            terminal_menu = TerminalMenu(preferences_startup_connect_menu_items ,clear_screen=False,
                                         title="Preferences Menu : Startup connect\n")
            startup_connect_menu_entry_index = terminal_menu.show()
            if startup_connect_menu_entry_index <= len(self.app.preferences.connect) - 1:
                self.app.preferences.connect[startup_connect_menu_entry_index] = not self.app.preferences.connect[startup_connect_menu_entry_index]
                return preferences_startup_connect()
            return self.preferences_menu()

        terminal_menu = TerminalMenu(preference_menu_items, clear_screen=False ,
                                     title =" Preferences Menu")
        preference_menu_entry_index = terminal_menu.show()
        match preference_menu_entry_index :
            case 0 : return preferences_configuration_filename()
            case 1 : return  preferences_line_termination()
            case 2 : return preferences_max_streams()
            case 3 : return preferences_startup_connect()
            case _ : return self.main_menu()



    def connect_menu(self) :
        """Connect menu , allow you to connect 
        """

        def connect_menu_select_stream_type (selected_port : Stream):
            terminal_menu = TerminalMenu(self.connect_disconect_items ,clear_screen=False,
                                         title=f" connect Menu : Stream {selected_port.stream_id} {"Connected" if selected_port.connected else "Disconnected"} {self.get_settings_title(selected_port) if selected_port.connected else ""}\n to change the stream type , the stream need to be disconnected\n")
            configure_menu_entry_index = terminal_menu.show()
            match configure_menu_entry_index :
                case 0 :
                    if selected_port.connected :
                        print(f"Stream {selected_port.stream_id} is already connected !")
                        return self.connect_menu()
                    else :
                        return connect(selected_port)
                case 1 : return disconnect(selected_port)
                case _ : return self.connect_menu()

        def disconnect(selected_port : Stream):
            if selected_port.connected :
                selected_port.disconnect()
            return self.connect_menu()

        def connect(selected_port : Stream):
            terminal_menu = TerminalMenu(self.configure_stream_type_menu_items ,clear_screen=False,
                                         title=f"connect Menu : Stream {selected_port.stream_id} {"Connected" if selected_port.connected else "Disconnected"} \n Choose wich type of stream you want\n" )
            configure_menu_entry_index = terminal_menu.show()

            if configure_menu_entry_index is None :
                return self.main_menu()
            if configure_menu_entry_index < len(self.configure_stream_type_menu_items) - 1 :
                try :
                    selected_port.connect(StreamType(configure_menu_entry_index))
                except StreamException as exc:
                    print(f"Connection failed ! : {exc}")
            return self.connect_menu()

        self._refresh_menu_items()
        terminal_menu = TerminalMenu(self.port_list_menu_items ,
                                     title="connect Menu : \n Choose which stream you want to enable or disable\n" )
        configure_menu_entry_index =terminal_menu.show()
        if configure_menu_entry_index is None :
            return self.main_menu()
        if configure_menu_entry_index < self.app.preferences.max_streams :
            selected_port : Stream = self.app.stream_list[configure_menu_entry_index]
            return connect_menu_select_stream_type(selected_port)
        return self.main_menu()

    def showdata_menu(self):
        """Show data menu
        """
        terminal_menu = TerminalMenu(self.port_list_menu_items ,clear_screen=False,
                                     title="Show Data Menu : \n Select a stream \n" ,)
        showdata_menu_entry_index = terminal_menu.show()
        if showdata_menu_entry_index is None :
            return self.main_menu()
        if showdata_menu_entry_index < self.app.preferences.max_streams :
            selected_port : Stream = self.app.stream_list[showdata_menu_entry_index]
            terminal_menu = TerminalMenu(self.show_data_menu_items ,
                                         title =f"Show Data Menu : Stream {selected_port.stream_id} {self.get_settings_title(selected_port)}")
            showdata_menu_entry_index = terminal_menu.show()

            if showdata_menu_entry_index is None :
                return self.main_menu()
            if showdata_menu_entry_index >= len(self.show_data_menu_items) - 1 :
                return self.showdata_menu()
            else :
                if selected_port.connected is True :
                    match showdata_menu_entry_index :
                        case 0 :
                            selected_port.toggle_incomming_data_visibility()
                            selected_port.toggle_outgoing_data_visibility()
                        case 1 :
                            selected_port.toggle_incomming_data_visibility()
                        case 2 :
                            selected_port.toggle_outgoing_data_visibility()
                    self.stop_show_data_event.clear()
                    self.show_data_thread = threading.Thread(target=self._show_data_task , args=(selected_port,))
                    self.show_data_thread.start()
                    input()
                    print("Stop showing data")
                    self.stop_show_data_event.set()
                    self.show_data_thread.join()

                    match showdata_menu_entry_index :
                        case 0 :
                            selected_port.toggle_incomming_data_visibility()
                            selected_port.toggle_outgoing_data_visibility()
                        case 1 :
                            selected_port.toggle_incomming_data_visibility()
                        case 2 :
                            selected_port.toggle_outgoing_data_visibility()
                    return self.showdata_menu()
                else :
                    print("Error : Selected Stream is not connected\n ")
                    return self.showdata_menu()
        else :
            return self.main_menu()

    def link_port_menu(self):
        """Link port menu 
        """
        terminal_menu = TerminalMenu(self.port_list_menu_items ,clear_screen=False,
                                     title="Link Menu : \n Link output data to a Stream\n" ,)
        link_port_menu_entry_index = terminal_menu.show()
        if link_port_menu_entry_index is None :
            return self.main_menu()
        if link_port_menu_entry_index < self.app.preferences.max_streams :
            selected_port = self.app.stream_list[link_port_menu_entry_index]
            self.link_port_link_menu(selected_port)
        return self.main_menu()

    def link_port_link_menu(self , selected_port : Stream):
        """List of availabel stream to link
        """

        def get_available_link_list(selected_port : Stream):
            available_link = []
            for port in self.app.stream_list :
                if port is not selected_port:
                    available_link.append(f"[{port.stream_id}] - Stream {port.stream_id} {" Linked " if port.stream_id in selected_port.linked_ports else ""}")
                else :
                    available_link.append(f"[{port.stream_id}] - Stream {port.stream_id} ( Port can't link itself )")
            available_link.append("[q] - Back")
            return available_link

        available_stream = get_available_link_list(selected_port)
        terminal_menu = TerminalMenu( available_stream,clear_screen=False,
                                     title="chose Stream for output data\n" ,)
        link_port_menu_entry_index = terminal_menu.show()
        if link_port_menu_entry_index < len(available_stream)-1 :
            if link_port_menu_entry_index is not  selected_port.stream_id :
                selected_port.update_linked_ports(link_port_menu_entry_index)
            else :
                print("not possible !")
            return self.link_port_link_menu(selected_port)
        return self.link_port_menu()

    def configure_menu_submenu(self , selected_port : Stream):
        """Menu to configure a specific stream
        """
        terminal_menu = TerminalMenu(self.configure_menu_submenu_items , clear_screen= False ,
                                     title=f"Configuration Menu : \n Change Streams {selected_port.stream_id} configs \n")
        configure_menu_entry_index = terminal_menu.show()
        match configure_menu_entry_index :
            case 0 : self.configure_stream_stream_type_menu(selected_port)
            case 1 : self.configure_stream_script_menu(selected_port,True)
            case 2 : self.configure_stream_script_menu(selected_port,False)
            case 3 : self.configure_stream_logging_menu(selected_port)
            case _ : return self.configure_menu()

    def configure_stream_stream_type_menu(self,selected_port : Stream):
        """Menu to configure a Stream
        """
        def configure_stream_tcp_menu():
            tcp_settings_menu_items : list = ["[q] - Back"]

            tcp_settings_menu_items.insert(0,f"[1] - Host - {selected_port.tcp_settings.host}")
            tcp_settings_menu_items.insert(1,f"[2] - Port - {selected_port.tcp_settings.port}")
            tcp_settings_menu_items.insert(2,f"[3] - Stream Mode - {selected_port.tcp_settings.stream_mode.value}")

            tcp_title = f"Configuration Menu : Stream {selected_port.stream_id} \n Current Configuration : \n Host : {selected_port.tcp_settings.host} \n Port : {selected_port.tcp_settings.port}\n StreamMode : {selected_port.tcp_settings.stream_mode.value}\n "

            def configure_tcp_host_menu():
                print(tcp_title)
                print("Enter a valid hostname or IP address")
                print("note : if in server mode , host will be 127.0.0.1")
                newhost = input()
                try :
                    if len(newhost) !=0 :
                        socket.gethostbyname(newhost)
                        selected_port.tcp_settings.set_host(newhost)
                except socket.gaierror:
                    print("Invalid host !")
                return configure_stream_tcp_menu()

            def configure_tcp_port_menu():
                print(tcp_title)
                print("Enter a valid port ")
                try :
                    newport = int(input())
                    selected_port.tcp_settings.set_port( newport)
                except ValueError:
                    print("Invalid port !")
                return configure_stream_tcp_menu()

            def configure_tcp_stream_mode_menu():
                terminal_menu= TerminalMenu( self.tcpsettings_stream_mode_items,clear_screen=False,
                                            title=tcp_title +"Stream mode Configuration\n" )
                menu_entry_index = terminal_menu.show()
                if menu_entry_index < len(self.tcpsettings_stream_mode_items) - 1:
                    selected_port.tcp_settings.set_stream_mode(StreamMode[self.tcpsettings_stream_mode_items[menu_entry_index]])
                return configure_stream_tcp_menu()

            terminal_menu= TerminalMenu(tcp_settings_menu_items ,clear_screen=False,
                                        title=f"Configuration Menu : Stream {selected_port.stream_id} \n TCP Configuration Menu")
            configure_stream_tpc_menu_entry_index = terminal_menu.show()
            match configure_stream_tpc_menu_entry_index:
                case 0 : return configure_tcp_host_menu()
                case 1 : return configure_tcp_port_menu()
                case 2 : return configure_tcp_stream_mode_menu()
                case _ : return self.configure_stream_stream_type_menu(selected_port)

        def configure_stream_serial_menu():

            serial_settings_menu_items : list = ["[q] - Back"]

            serial_settings_menu_items.insert(0,f"[1] - Port - {"None" if selected_port.serial_settings.port is None else selected_port.serial_settings.port}")
            serial_settings_menu_items.insert(1,f"[2] - BaudRate - {selected_port.serial_settings.baudrate.value}")
            serial_settings_menu_items.insert(2,f"[3] - stopBits - {selected_port.serial_settings.stopbits.value}")
            serial_settings_menu_items.insert(3,f"[4] - Parity - {selected_port.serial_settings.parity.value}")
            serial_settings_menu_items.insert(4,f"[5] - Bytesize - {selected_port.serial_settings.bytesize.value}")
            serial_settings_menu_items.insert(5,f"[6] - Rtc-cts - {selected_port.serial_settings.rtscts}")
            
            serial_title = f"Configuration Menu : Stream {selected_port.stream_id} \n Current Configuration : \n Port : {selected_port.serial_settings.port} \n BaudRate : {selected_port.serial_settings.baudrate.value}\n StopBits : {selected_port.serial_settings.stopbits.value}\n Parity : {selected_port.serial_settings.parity.value}\n Bytesize : {selected_port.serial_settings.bytesize.value}\n Rtc-cts : {selected_port.serial_settings.rtscts}\n"


            def configure_serial_port_menu():
                available_streams = selected_port.serial_settings.get_available_port()
                available_streams_temps =[]
                found = False
                for available_port in available_streams :

                    for port in self.app.stream_list:
                        if port.serial_settings is not None:
                            if port.serial_settings.port is not None:
                                if available_port[0] in port.serial_settings.port :
                                    found = True
                    if found is False:
                        available_streams_temps.append(available_port)
                    found = False

                iterator = 0
                configure_menu_port_items = ["[d] - disconnect","[q] - Back"]
                if available_streams_temps is not None:
                    for available_port in available_streams_temps :
                        configure_menu_port_items.insert(iterator,f"[{iterator + 1}] {available_port[0]} - {available_port[1]}")
                        iterator +=1

                terminal_menu= TerminalMenu(configure_menu_port_items ,clear_screen=False,
                                            title=serial_title + "Configure Stream's port \n")
                menu_entry_index = terminal_menu.show()

                if menu_entry_index >= iterator :
                    if menu_entry_index == iterator:
                        selected_port.serial_settings.set_port("")
                    return configure_stream_serial_menu()
                else:
                    selected_port.serial_settings.set_port(available_streams_temps[menu_entry_index][0])
                    return configure_stream_serial_menu()


            def configure_serial_baudrate_menu():
                terminal_menu= TerminalMenu( self.serialsettings_baudrate_items,clear_screen=False,
                                            title=f"{serial_title} Configure Stream's Baudrate \n")
                menu_entry_index = terminal_menu.show()
                if menu_entry_index < len(self.serialsettings_baudrate_items) - 1:
                    selected_port.serial_settings.set_baudrate(BaudRate( self.serialsettings_baudrate_items[menu_entry_index]))
                return configure_stream_serial_menu()

            def configure_serial_parity_menu():
                terminal_menu= TerminalMenu( self.serialsettings_parity_items,clear_screen=False,
                                            title=f"{serial_title} Configure Stream's Parity \n")
                menu_entry_index = terminal_menu.show()
                if menu_entry_index < len(self.serialsettings_parity_items) - 1:
                    selected_port.serial_settings.set_parity(Parity["PARITY_"+self.serialsettings_parity_items[menu_entry_index]])
                return configure_stream_serial_menu()

            def configure_serial_stopbits_menu():
                terminal_menu= TerminalMenu( self.serialsettings_stopbits_items,clear_screen=False,
                                            title=f"{serial_title} Configure Stream's StopBits \n")
                menu_entry_index = terminal_menu.show()
                if menu_entry_index < len(self.serialsettings_stopbits_items) - 1:
                    selected_port.serial_settings.set_stopbits(StopBits["STOPBITS_" + self.serialsettings_stopbits_items[menu_entry_index]])
                return configure_stream_serial_menu()

            def configure_serial_bytesize_menu():
                terminal_menu= TerminalMenu( self.serialsettings_bytesize_items,clear_screen=False,
                                            title=f"{serial_title} Configure Stream's StopBits \n")
                menu_entry_index = terminal_menu.show()
                if menu_entry_index < len(self.serialsettings_bytesize_items) - 1:
                    selected_port.serial_settings.set_bytesize(ByteSize[self.serialsettings_bytesize_items[menu_entry_index]])
                return configure_stream_serial_menu()

            def configure_serial_rtscts_menu():
                if selected_port.serial_settings.rtscts is True :
                    selected_port.serial_settings.set_rtscts(False)
                else:
                    selected_port.serial_settings.set_rtscts(True)
                return configure_stream_serial_menu()

            terminal_menu= TerminalMenu(serial_settings_menu_items ,clear_screen=False,
                                        title=f"Configuration Menu : Stream {selected_port.stream_id} \n Serial Configuration Menu" )
            configure_stream_serial_menu_entry_index = terminal_menu.show()
            match configure_stream_serial_menu_entry_index:
                case 0 : return configure_serial_port_menu()
                case 1 : return configure_serial_baudrate_menu()
                case 2 : return configure_serial_stopbits_menu()
                case 3 : return configure_serial_parity_menu()
                case 4 : return configure_serial_bytesize_menu()
                case 5 : return configure_serial_rtscts_menu()
                case _ : return self.configure_stream_stream_type_menu(selected_port)

        def configure_stream_udp_menu():
            udp_settings_menu_items : list =[]
            if selected_port.udp_settings.specific_host:
                udp_settings_menu_items.insert(0,f"[1] - Specific Host - {selected_port.udp_settings.host}")

            udp_settings_menu_items.insert(1,f"[2] - Port - {selected_port.udp_settings.port}")
            udp_settings_menu_items.insert(2,f"[3] - Stream to specific Host - {selected_port.udp_settings.specific_host}")
            udp_settings_menu_items.insert(3,f"[4] - Data Flow Mode - {str(selected_port.udp_settings.dataflow).replace("DataFlow.","")}")
            udp_settings_menu_items.append("[q] - Back")
            udp_title = f"Configuration Menu : Stream {selected_port.stream_id} \n Current Configuration : \n Host : {selected_port.udp_settings.host}\n Port : {selected_port.udp_settings.port}\n Specific Host : {selected_port.udp_settings.specific_host}\n Data Flow Mode : {str(selected_port.udp_settings.DataFlow).replace('DataFlow.','')}\n"

            def configure_udp_host_menu():
                print(udp_title)
                print("Enter a valid hostname or Ip address")
                newhost = input()
                try : 
                    if len(newhost) !=0:
                        socket.gethostbyname(newhost)
                        selected_port.tcp_settings.set_host(newhost)
                except socket.gaierror:
                    print("Invalid hostname or IP address !")
                return configure_stream_udp_menu()

            def configure_udp_port_menu():
                print(udp_title)
                print("Enter a valid port ")
                try :
                    newport = int(input())
                    if newport is not None:
                        selected_port.tcp_settings.set_port( newport)
                except ValueError:
                    print("Invalid port !")
                return configure_stream_udp_menu()

            def configure_udp_specific_host_menu():
                selected_port.udp_settings.specific_host = False if selected_port.udp_settings.specific_host else True
                return configure_stream_udp_menu()

            def configure_udp_dataflow_menu():
                terminal_menu= TerminalMenu( self.udpsettings_dataflow_items,clear_screen=False, title=udp_title + "Configure Stream's Dataflow\n")
                menu_entry_index = terminal_menu.show()
                if menu_entry_index < len(self.udpsettings_dataflow_items) - 1:
                    selected_port.udp_settings.dataflow = DataFlow[self.udpsettings_dataflow_items[menu_entry_index]]
                return configure_stream_udp_menu()

            terminal_menu= TerminalMenu(udp_settings_menu_items ,clear_screen=False,
                                        title=f"Configuration Menu : Stream {selected_port.stream_id} \n UDP Configuration Menu")
            configure_stream_udp_menu_entry_index = terminal_menu.show()
            if selected_port.udp_settings.specific_host is False : 
                configure_stream_udp_menu_entry_index += 1

            match configure_stream_udp_menu_entry_index:
                case 0 : return configure_udp_host_menu() if selected_port.udp_settings.specific_host else configure_stream_udp_menu()
                case 1 : return configure_udp_port_menu()
                case 2 : return configure_udp_specific_host_menu()
                case 3 : return configure_udp_dataflow_menu()
                case _ : return self.configure_stream_stream_type_menu(selected_port)

        def configure_stream_ntrip_menu():
            ntrip_settings_menu_items : list =[]
            ntrip_settings_menu_items.insert(0,f"[1] - Host - {selected_port.ntrip_client.ntrip_settings.host}")
            ntrip_settings_menu_items.insert(1,f"[2] - Port - {selected_port.ntrip_client.ntrip_settings.port}")
            ntrip_settings_menu_items.insert(2,f"[3] - Mountpoint - {selected_port.ntrip_client.ntrip_settings.mountpoint}")
            ntrip_settings_menu_items.insert(3,f"[4] - Authentification - {"Enabled" if selected_port.ntrip_client.ntrip_settings.auth else "Disabled"}")
            ntrip_settings_menu_items.insert(4,f"[5] - Username - {selected_port.ntrip_client.ntrip_settings.username}")
            ntrip_settings_menu_items.insert(5,f"[6] - Password - {selected_port.ntrip_client.ntrip_settings.password}")
            ntrip_settings_menu_items.append("[q] - Back")
            ntrip_title = f"Configuration Menu : Stream {selected_port.stream_id} \n Current Configuration : \n Host : {selected_port.ntrip_client.ntrip_settings.host}\n Port : {selected_port.ntrip_client.ntrip_settings.port}\n Username : {selected_port.ntrip_client.ntrip_settings.username}\n Password : {selected_port.ntrip_client.ntrip_settings.password}\n Mountpoint : {selected_port.ntrip_client.ntrip_settings.mountpoint}\n"

            def configure_ntrip_host_menu():
                print(ntrip_title)
                print("Enter a valid hostname or Ip address")
                newhost = input()
                try :
                    if len(newhost) !=0:
                        socket.gethostbyname(newhost)
                        selected_port.ntrip_client.set_settings_host(newhost)
                except socket.gaierror:
                    print("Invalid hostname or IP address !")
                return configure_stream_ntrip_menu()

            def configure_ntrip_port_menu():
                print(ntrip_title)
                print("Enter a valid port ")
                try : 
                    newport = int(input())
                    if newport is not None:
                        selected_port.ntrip_client.ntrip_settings.set_port( newport)
                except ValueError:
                    print("Invalid port !")
                return configure_stream_ntrip_menu()

            def configure_ntrip_mountpoint_menu():
                print(ntrip_title)
                if selected_port.ntrip_client.ntrip_settings.host is not None and selected_port.ntrip_client.ntrip_settings.source_table is not None:
                    list_of_mountpoint = []
                    for source_table in selected_port.ntrip_client.ntrip_settings.source_table:
                        list_of_mountpoint.append(source_table.mountpoint)
                    list_of_mountpoint.append("[q] - Back")
                    terminal_menu = TerminalMenu(list_of_mountpoint ,clear_screen=False,
                                                 title=f"Configuration Menu : Stream {selected_port.stream_id} \n NTRIP Configuration Menu \n Choose a mountpoint \n"  )
                    mountpoint_index = terminal_menu.show()
                    if mountpoint_index < len(list_of_mountpoint) - 1 :
                        selected_port.ntrip_client.ntrip_settings.set_mountpoint(list_of_mountpoint[mountpoint_index])
                return configure_stream_ntrip_menu()
            
            def configure_ntrip_username_menu():
                print(ntrip_title)
                print("Enter a valid username ")
                new_username = input()
                if len(new_username) !=0:
                    selected_port.ntrip_client.ntrip_settings.set_username(new_username)
                return configure_stream_ntrip_menu()
            
            def configure_ntrip_password_menu():
                print(ntrip_title)
                print("Enter a valid password ")
                new_password = input()
                if len(new_password) !=0:
                    selected_port.ntrip_client.ntrip_settings.set_password(new_password)
                return configure_stream_ntrip_menu()
            
            def configure_ntrip_auth_menu():
                selected_port.ntrip_client.ntrip_settings.auth = False if selected_port.ntrip_client.ntrip_settings.auth else True
                return configure_stream_ntrip_menu()

            terminal_menu= TerminalMenu(ntrip_settings_menu_items ,clear_screen=False,
                                        title=f"Configuration Menu : Stream {selected_port.stream_id} \n NTRIP Configuration Menu")
            configure_stream_udp_menu_entry_index = terminal_menu.show()
            match configure_stream_udp_menu_entry_index:
                case 0 : return configure_ntrip_host_menu()
                case 1 : return configure_ntrip_port_menu()
                case 2 : return configure_ntrip_mountpoint_menu()
                case 3 : return configure_ntrip_auth_menu()
                case 4 : return configure_ntrip_username_menu()
                case 5 : return configure_ntrip_password_menu()
                case _ : return self.configure_stream_stream_type_menu(selected_port)


        terminal_menu= TerminalMenu(self.configure_stream_type_menu_items,clear_screen=False,
                                    title=f"Configuration Menu : Stream {selected_port.stream_id} \n  select which type of stream you want to configure \n")
        configure_stream_menu_entry_index = terminal_menu.show()
        match configure_stream_menu_entry_index:
            case 0 : return configure_stream_serial_menu()
            case 1 : return configure_stream_tcp_menu()
            case 2 : return configure_stream_udp_menu()
            case 3 : return configure_stream_ntrip_menu()
            case _ : return self.configure_menu_submenu(selected_port)

    def configure_stream_script_menu(self, selected_port : Stream , startup : bool):
        """add closeup or startup script menu
        """
        if startup :
            configure_script_menu_items=[f"[1] - Startup Script - {selected_port.send_startup_script}",
                                         f"[2] - Script file - {selected_port.startup_script}","[q] - Back"]
        else :
            configure_script_menu_items=[f"[1] - Closeup Script - {selected_port.send_close_script}",
                                         f"[2] - Script file - {selected_port.close_script}",
                                         "[q] - Back"]
        def configure_script():
            if startup :
                selected_port.set_startup_script()
            else :
                selected_port.set_close_script()
            return self.configure_stream_script_menu(selected_port , startup)

        def configure_script_file_menu():
            print("Enter the path to the Script file")
            new_path = input()
            try :
                if len(new_path) !=0 :
                    if startup :
                        selected_port.set_startup_script_path(new_path)
                    else :
                        selected_port.set_close_script_path(new_path)
            except ScriptFileException as exc :
                print(f"Invalid path ! , {exc}")
            return self.configure_stream_script_menu(selected_port , startup)

        terminal_menu = TerminalMenu(configure_script_menu_items,clear_screen=False, title="")
        choice_index = terminal_menu.show()
        match choice_index :
            case 0 : return configure_script()
            case 1 : return configure_script_file_menu()
            case _ : return self.configure_menu()

    def configure_stream_logging_menu(self,selected_port : Stream ):
        """Add logging file for logging
        """

        configure_logging_menu_items=[f"[1] - Logging - {str(selected_port.logging)}",
                                      f"[2] - Logging Filename - {selected_port.logging_file}",
                                      "[q] - Back"]

        def configure_logging():
            selected_port.set_logging()
            return self.configure_stream_logging_menu(selected_port)
        def configure_logging_file_name_menu():
            print("Enter the path to the Script file")
            new_path = input()
            try :
                if len(new_path) !=0 :
                    selected_port.set_logging_file_name(new_path)
            except LogFileException as exc :
                print(f"Invalid path ! , {exc}")
            return self.configure_stream_logging_menu(selected_port)

        terminal_menu = TerminalMenu(configure_logging_menu_items, title="")
        choice_index = terminal_menu.show()
        match choice_index :
            case 0 : return configure_logging()
            case 1 : return configure_logging_file_name_menu()
            case _ : return self.configure_menu()

    def get_settings_title(self, selected_port : Stream):
        """Return the current configuration of the stream
        """
        current_settings = selected_port.to_string()
        if current_settings is None :
            return "\n No settings"
        else :
            return f"\n Current Settings : \n {current_settings} \n"
