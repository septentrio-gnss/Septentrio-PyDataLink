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

import math
import copy
from ..StreamConfig.Stream import *
from ..StreamConfig.App import *
from ..StreamSettings import SerialSettings ,TcpSettings , UdpSettings
from ..constants import *

from PySide6.QtCore import QObject, Qt , QRegularExpression , QUrl, QThread , Signal 
from PySide6.QtGui import  QRegularExpressionValidator,QTextCursor,QAction,QIcon,QDesktopServices , QPixmap
from PySide6.QtWidgets import (QMainWindow, QApplication, QCheckBox, QComboBox, QFrame,
                               QDialog, QDialogButtonBox,QGridLayout, QGroupBox, QHBoxLayout, QLabel,
                               QLineEdit, QPushButton, QRadioButton, QMessageBox,
                               QSpinBox,QTabWidget, QTextEdit,QVBoxLayout, QWidget,QFileDialog)


def pair_h_widgets( *widgets : QWidget ) -> QHBoxLayout:
    """Add every widgets to a horizontal layout
    Returns:
        QHBoxLayout: _description_
    """
    result = QHBoxLayout()
    for widget in widgets :
        result.addWidget(widget)
    result.setAlignment(Qt.AlignmentFlag.AlignTop)
    return result
def pair_v_widgets(*widgets : QWidget) ->QVBoxLayout:
    """Add every widgets to a horizontal layout

    Returns:
        QHBoxLayout: _description_
    """
    result = QHBoxLayout()
    for widget in widgets :
        result.addWidget(widget)
    result.setAlignment(Qt.AlignmentFlag.AlignTop)
    return result

class GraphicalUserInterface(QMainWindow):
    """Graphical interface for datalink
    """

    def __init__(self, app : App) -> None:
        super().__init__()
        
        self.setWindowIcon(QIcon(os.path.join(DATAFILESPATH , 'pyDatalink_icon.png')))
        self.app : App = app
        self.streams_widget : list[ConnectionCard] = []
        self.setWindowTitle(APPNAME)

        # Menu bar
        menu_bar = self.menuBar()

        # Create a menu
        file_menu = menu_bar.addMenu('File')

        # Preferences action
        preference_action = QAction("Preferences",self)
        preference_action.setShortcut('Ctrl+P')
        preference_action.triggered.connect(lambda p : self.open_preference_interface())

        # exit action
        exit_Action = QAction('Exit', self)
        exit_Action.setShortcut('Ctrl+Q')
        exit_Action.triggered.connect(lambda : self.close())

        file_menu.addAction(preference_action)
        file_menu.addSeparator()
        file_menu.addAction(exit_Action)

        # IDEA -  TO DO
        #confMenu = menu_bar.addMenu('Config')
        #Save current Config
        #Load config
        #Change config

        # github page
        github_page_action = QAction(QIcon(os.path.join(DATAFILESPATH ,"Github_icon.png")),"GitHub Repository", self)
        github_page_action.triggered.connect(lambda : self.open_link())

        # About action
        about_action = QAction(QIcon(os.path.join(DATAFILESPATH , 'pyDatalink_icon.png')),"About",self)
        about_action.triggered.connect(lambda p : self.open_about_dialog())

        #Help Menu
        help_menu = menu_bar.addMenu("Help")
        help_menu.addAction(github_page_action)
        help_menu.addSeparator()
        help_menu.addAction(about_action)

        #Main Window layout
        main_layout = QGridLayout()
        connection_card_layout = QVBoxLayout()
        connection_card_line_layout = QHBoxLayout()
        number_card_per_line = math.ceil(self.app.max_stream / 2)
        number_line = math.ceil(self.app.max_stream /number_card_per_line)
        for i in range(self.app.max_stream):
            new_card = ConnectionCard(i,self.app.stream_list[i],self.app.max_stream)
            self.streams_widget.append(new_card)
            connection_card_line_layout.addWidget(new_card.get_card_widget())
            if connection_card_line_layout.count() == number_card_per_line :
                connection_card_layout.addLayout(connection_card_line_layout)
                connection_card_line_layout = QHBoxLayout()
                connection_card_line_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        if connection_card_line_layout.count() < number_card_per_line :
            connection_card_layout.addLayout(connection_card_line_layout)

        window_height = (350 * number_line) + 50
        window_width = (300 * number_card_per_line) + 20
        self.setFixedSize(window_width,window_height)

        main_layout.addLayout(connection_card_layout,0,0)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        widget = QWidget()
        widget.setLayout(main_layout)
        self.setCentralWidget(widget)

        self.timer_id = self.startTimer(30)

    def timerEvent(self, event):
        for widget in self.streams_widget:
            widget.refresh_cards()

    def open_preference_interface(self):
        """open the setting page to configure preferences
        """
        configure_dialog = PreferencesInterface(self.app.preferences)
        configure_dialog.exec_()

    def open_about_dialog(self):
        """Open the about dialog
        """
        about_dialog = AboutDialog()
        about_dialog.exec_()

    def open_link(self):
        """open github repository in a web browser
        """
        url = QUrl("https://github.com/septentrio-gnss/Septentrio-PyDataLink")
        if not QDesktopServices.openUrl(url):
            QMessageBox.warning(self, "Error", "Couldn't open the web page")

    def closeEvent(self,event):
        self.app.close_all()
        QApplication.quit()

class ConnectionCard :
    """Widget of a stream in the main page
    """   
    def __init__(self,stream_id : int ,stream : Stream , max_streams : int ) -> None:
        self.stream = stream
        self.stream_id = stream_id
        self.max_streams = max_streams
        self.connection_card_widget = self.connection_card()
        self.connect_thread = None
        self.worker = None
        self.show_data_dialog = None
        self.previous_tab = 0

    def connection_card(self):
        """create the card widget
        """
        result = QGroupBox(f"Connection {self.stream_id}")

        result.setFixedSize(300,350)
        #Top button
        self.connect_button = QPushButton("Connect")

        #Add slot : connect the selected stream
        self.configure_button = QPushButton("Configure")

       # overviewText
        self.current_config_overview = QLabel()
        self.current_config_overview.setText(f"Current configuration :\n {self.stream.to_string()}")
        self.current_config_overview.setAlignment(Qt.AlignmentFlag.AlignJustify)
        self.current_config_overview.setFixedHeight(150)

        # Status
        self.status= QLabel()
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status.setFixedSize(280,30)

        #Data Transfert
        self.current_data_transfert = QLabel()
        self.current_data_transfert.setText(f"In: {self.stream.data_transfer_input} kBps | Out: {self.stream.data_transfer_output} kBps")
        self.current_data_transfert.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.current_data_transfert.setStyleSheet("QWidget { border: 2px solid grey; }")
        self.current_data_transfert.setFixedSize(160,24)

        #showdata
        
        self.show_data_button = QPushButton("Show Data")
        data_layout = pair_h_widgets(self.show_data_button , self.current_data_transfert)
        button_layout = pair_h_widgets(self.connect_button , self.configure_button)
        top_layout = QVBoxLayout()
        top_layout.addLayout(button_layout)
        top_layout.addLayout(data_layout)
        top_layout.addWidget(self.status)
        
        #Separator
        separator : list[QFrame] = []
        for _ in range(2) :
            new_separator = QFrame()
            new_separator.setFrameShape(QFrame.HLine)
            new_separator.setFrameShadow(QFrame.Sunken)
            new_separator.setLineWidth(1)
            separator.append(new_separator)
        
        # Final Layout
        card_layout = QVBoxLayout(result)
        card_layout.addLayout(top_layout)
        card_layout.addWidget(separator[0])
        card_layout.addWidget(self.current_config_overview)
        card_layout.addWidget(separator[1])
        card_layout.addWidget(self.link_layout())

        #Init in case of Startup connect
        if self.stream.is_connected():
            self.connect_button.setText("Disonnect")
            self.configure_button.setDisabled(True)
            self.status.setText("CONNECTED")
            self.status.setStyleSheet("QLabel {color : #32a852; font-weight: bold;}")
        else :
            self.current_data_transfert.setStyleSheet("QWidget { border: 2px solid grey; }")
            if self.stream.startup_error != "":
                self.status.setText("ERROR ON STARTUP CONNECT !")
                self.status.setStyleSheet("QLabel { color: #c42323;} QToolTip {font-weight: bold;}")
                self.status.setToolTip(self.stream.startup_error)
        # SIGNALS

        self.configure_button.pressed.connect(lambda : self.open_configure_interface(self.stream))
        self.connect_button.pressed.connect(self.connect_stream)
        self.show_data_button.pressed.connect(self.show_data)
        return result

    def link_layout(self):
        """create the link check box for a connection card
        """
        link_widget = QWidget()
        
        link_layout = QHBoxLayout(link_widget)
        link_layout.addWidget(QLabel("Links : "))
        for a in range(self.max_streams):
            new_check_box = QCheckBox(str(a))
            if self.stream_id == a :
                new_check_box.setDisabled(True)
            if a in self.stream.linked_ports :
                new_check_box.setChecked(True)
            new_check_box.stateChanged.connect(lambda state,x=a : self.toggle_linked_port(x))

            link_layout.addWidget(new_check_box)
        return link_widget

    def toggle_linked_port(self , linkindex):
        """update linked ports of stream when checkbox is check or uncheck
        """
        self.stream.update_linked_ports(linkindex)

    def open_configure_interface(self,stream : Stream):
        """Open configuration dialog to configure current stream
        """
        configure_dialog = ConfigureInterface(stream , self.previous_tab)
        configure_dialog.accepted.connect(self.refresh_cards)
        configure_dialog.save_previous_tab.connect(self.save_previous_tab)
        configure_dialog.save_config.connect(self.save_config)
        configure_dialog.exec_()
        
    def save_previous_tab(self, tab):
        self.previous_tab = tab
    def save_config(self,stream):
        self.stream = stream

    def refresh_cards(self):
        """Refresh sumarry value when a setting has changed
        """
        self.current_config_overview.setText(f"Current configuration :  {self.stream.stream_type.name}\n{self.stream.to_string()}")
        self.current_data_transfert.setText(f"In: {self.stream.data_transfer_input} kBps | Out: {self.stream.data_transfer_output} kBps")
        if not self.stream.connected and self.connect_button.text() =="Disconnect" :
            self.connect_button.setText("Connect")
            self.configure_button.setDisabled(False)
            self.status.setText("")

    def connect_stream(self):
        """Connect or disconnect the stream 
        """
        self.connect_button.setDisabled(True)
        self.connect_thread = QThread()
        self.worker = StreamConnectWorker(self)
        self.worker.moveToThread(self.connect_thread)
        self.connect_thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.connect_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.connect_thread.finished.connect(self.connect_thread.deleteLater)
        self.connect_thread.finished.connect(self.cleanup)
        self.worker.finished.connect(lambda : self.connect_button.setDisabled(False) )

        self.connect_thread.start()

    def cleanup(self):
        """Reset thread and worker values
        """
        self.connect_thread = None
        self.worker = None

    def show_data(self):
        """open the dialog to visualize the incoming or outgoing data
        """
        if self.stream.show_incoming_data.is_set() or self.stream.show_outgoing_data.is_set():
            self.show_data_button.setText("Show Data")
            self.show_data_dialog.close_dialog()
            self.show_data_dialog = None
        else:
            self.show_data_dialog = ShowDataInterface(self.stream)
            self.show_data_dialog.finished.connect(lambda : self.show_data_button.setText("Show Data"))
            self.show_data_button.setText("Hide Data")
            self.show_data_dialog.show()

    def get_card_widget(self):
        """return a new connection card widget
        """
        return self.connection_card_widget

class ConfigureInterface(QDialog) :
    """Configuration dialog
    """
    save_previous_tab = Signal(int)
    save_config = Signal(Stream)
    def __init__(self , stream : Stream , previous_tab : int = 0 ) -> None:
        super().__init__()
        self.setWindowTitle(f"Configure Connection {stream.stream_id}")
        self.setWindowIcon(QIcon(os.path.join(DATAFILESPATH , 'pyDatalink_icon.png')))
        self.stream = stream
        self.stream_save = copy.copy(stream)
        self.setModal(True)
        self.setFixedSize(350,580)
        configure_layout = QVBoxLayout(self)
        self.previous_tab = previous_tab
        self.update_thread = None
        self.worker = None
        
        serial_menu = self.serial_menu()
        tcp_menu = self.tcp_menu()
        udp_menu =  self.udp_menu()
        ntrip_menu = self.ntrip_menu()

        self.config_tabs = QTabWidget()
        self.config_tabs.addTab(self.general_menu(), "General")
        index = self.config_tabs.addTab(serial_menu , "Serial")
        self.config_tabs.addTab(tcp_menu, "TCP")
        self.config_tabs.addTab(udp_menu, "UDP")
        self.config_tabs.addTab(ntrip_menu, "NTRIP")

        if len(self.stream.serial_settings.get_available_port()) == 0 :
            self.config_tabs.setTabEnabled(index,False)
            if previous_tab == index :
                previous_tab = 0 
        
        self.config_tabs.setCurrentIndex(int(previous_tab))

        configure_layout.addWidget(self.config_tabs)
        configure_layout.addLayout(self.bottom_button_layout())

    def general_menu(self):
        """General menu tab
        """
        result = QGroupBox("General Settings")

        # Select Connection
        stream_type_box = QGroupBox("Select the connection type")
        stream_type_box_layout = QHBoxLayout(stream_type_box)
        stream_type_list = QComboBox()
        for type in StreamType :
            stream_type_list.addItem(type.name, type)
        if self.stream.serial_settings.baudrate is not None :
            index = stream_type_list.findData(self.stream.stream_type) 
        else :
            index = stream_type_list.findData(StreamType.NONE)
        stream_type_list.setCurrentIndex(index)
        stream_type_box_layout.addWidget(stream_type_list)
        stream_type_box_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        # connect/Close Script
        script_box = QGroupBox("Scripts")
        script_box_layout = QVBoxLayout(script_box)

        open_script_check_box = QCheckBox()
        open_script_check_box.setChecked(self.stream.send_startup_script)
        open_script_label = QLabel("connect Script : ")
        open_script_edit = QLineEdit()
        open_script_edit.setDisabled(not self.stream.send_startup_script)
        open_script_edit.setText(self.stream.startup_script)
        script_box_layout.addLayout(pair_h_widgets(open_script_check_box,open_script_label,open_script_edit))

        close_script_check_box = QCheckBox()
        close_script_check_box.setChecked(self.stream.send_close_script)
        close_script_label = QLabel("Close Script : ")
        close_script_edit = QLineEdit()
        close_script_edit.setDisabled(not self.stream.send_close_script)
        close_script_edit.setText(self.stream.close_script)
        script_box_layout.addLayout(pair_h_widgets(close_script_check_box,close_script_label,close_script_edit))

        # Logging file
        log_box = QGroupBox("Logging")
        log_box_layout = QVBoxLayout(log_box)

        log_check_box = QCheckBox()
        log_check_box.setChecked(self.stream.logging)
        log_label = QLabel("Log File : ")
        log_edit = QLineEdit()
        log_edit.setDisabled(not self.stream.logging)
        log_edit.setText(self.stream.logging_file)
        log_box_layout.addLayout(pair_h_widgets(log_check_box,log_label,log_edit))

        # Final Layout
        result_layout = QVBoxLayout(result)
        result_layout.addWidget(stream_type_box)
        result_layout.addWidget(script_box)
        result_layout.addWidget(log_box)
        result_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # SIGNALS
        stream_type_list.currentIndexChanged.connect(lambda : self.stream.set_stream_type(stream_type_list.currentData()))
        open_script_check_box.checkStateChanged.connect(lambda : self.open_script_file(open_script_edit,open_script_check_box , True))
        close_script_check_box.checkStateChanged.connect(lambda : self.open_script_file(close_script_edit,close_script_check_box , False))
        log_check_box.checkStateChanged.connect(lambda : self.select_log_file(log_edit ,log_check_box ))
        return result

    def serial_menu(self):
        """Serial tab
        """
        result = QGroupBox("Serial connection")
        #Available Port
        available_port_list = QComboBox()
        ports = self.stream.serial_settings.get_available_port()
        if len(ports) > 0 :
            for port in ports :
                available_port_list.addItem(port[0].replace("/dev/ttyACM","COM") + " - " + port[1].split("-")[0],port[0])
            available_port_list.setCurrentIndex(-1)
        else :
            available_port_list.addItem("no com port detected")
            available_port_list.setDisabled(True)
        if self.stream.serial_settings.port != "":
            index = available_port_list.findData(self.stream.serial_settings.port)
            available_port_list.setCurrentIndex(index)
        available_port_label = QLabel("Port COM:")
        available_port_label.setBuddy(available_port_list)

        #Baudrate
        baudrate_list = QComboBox()
        for baudrate in SerialSettings.BaudRate :
            baudrate_list.addItem(baudrate.value, baudrate)
        if self.stream.serial_settings.baudrate is not None :
            index = baudrate_list.findData(self.stream.serial_settings.baudrate)
            baudrate_list.setCurrentIndex(index)
        baudrate_list_label = QLabel("Baudrate :")
        baudrate_list_label.setBuddy(baudrate_list)

        #Parity
        parity_list = QComboBox()
        for parity in SerialSettings.Parity :
            parity_list.addItem( parity.value + " - " +  parity.name.replace("PARITY_","") , parity )
        if self.stream.serial_settings.parity is not None :
            index = parity_list.findData(self.stream.serial_settings.parity)
            parity_list.setCurrentIndex(index)
        parity_list_label = QLabel("Parity :")
        parity_list_label.setBuddy(parity_list)

        #Stop bits
        stop_bits_list = QComboBox()
        for stopbits in SerialSettings.StopBits :
            stop_bits_list.addItem(str(stopbits.value),stopbits)
        if self.stream.serial_settings.stopbits is not None :
            index = stop_bits_list.findData(self.stream.serial_settings.stopbits) 
            stop_bits_list.setCurrentIndex(index)
        stop_bits_list_label = QLabel("StopBits :")
        stop_bits_list_label.setBuddy(stop_bits_list)

         #ByteSize
        byte_size_list = QComboBox()
        for bytesize in SerialSettings.ByteSize :
            byte_size_list.addItem(str(bytesize.value) , bytesize)
        index = byte_size_list.findData(self.stream.serial_settings.bytesize) 
        byte_size_list.setCurrentIndex(index)
        byte_size_list_label = QLabel("Bytesize :")
        byte_size_list_label.setBuddy(byte_size_list)

        #RTscts
        rtscts_list = QComboBox()
        rtscts_list.addItem("True", True)
        rtscts_list.addItem("False", False)   
        index = rtscts_list.findData(self.stream.serial_settings.rtscts) 
        rtscts_list.setCurrentIndex(index)
        rtscts_list_label = QLabel("Rts-Cts :")
        rtscts_list_label.setBuddy(rtscts_list)
   
        # Final Layout
        widget_layout = QVBoxLayout(result)
        widget_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        widget_layout.addLayout(pair_h_widgets(available_port_label , available_port_list))
        widget_layout.addLayout(pair_h_widgets(baudrate_list_label,baudrate_list))
        widget_layout.addLayout(pair_h_widgets(parity_list_label,parity_list))
        widget_layout.addLayout(pair_h_widgets(stop_bits_list_label,stop_bits_list))
        widget_layout.addLayout(pair_h_widgets(byte_size_list_label ,byte_size_list ))
        widget_layout.addLayout(pair_h_widgets(rtscts_list_label,rtscts_list))

        # SIGNAL
        available_port_list.currentIndexChanged.connect(lambda : self.stream.serial_settings.set_port(available_port_list.currentData()))
        parity_list.currentIndexChanged.connect(lambda : self.stream.serial_settings.set_parity(parity_list.currentData()))
        baudrate_list.currentIndexChanged.connect(lambda : self.stream.serial_settings.set_baudrate(baudrate_list.currentData()))
        stop_bits_list.currentIndexChanged.connect(lambda : self.stream.serial_settings.set_stopbits(stop_bits_list.currentData()))
        byte_size_list.currentIndexChanged.connect(lambda : self.stream.serial_settings.set_bytesize(byte_size_list.currentData()))
        rtscts_list.currentIndexChanged.connect(lambda : self.stream.serial_settings.set_rtscts(rtscts_list.currentData()))
        return result

    def tcp_menu(self):
        """TCP config tab
        """
        result = QWidget()
        result_layout = QVBoxLayout(result)

        # Connection mode Box
        connection_mode_box = QGroupBox("Connection Mode")
        client_mode = QRadioButton("TCP/IP Client")
        server_mode = QRadioButton("TCP/IP Server")
        if self.stream.tcp_settings.stream_mode == StreamMode.CLIENT:
            client_mode.setChecked(True)
        else:
            server_mode.setChecked(True)

        connection_mode_layout = QHBoxLayout(connection_mode_box)
        connection_mode_layout.addWidget(client_mode)
        connection_mode_layout.addWidget(server_mode)
        connection_mode_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Host name Box
        host_name_box = QGroupBox("Host-Name or IP-Address")

        host_name = QLineEdit()
        host_name.setText(self.stream.tcp_settings.host)

        host_name_layout = QHBoxLayout(host_name_box)
        host_name_layout.addWidget(host_name)
        host_name_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        server_mode.toggled.connect(host_name.setDisabled)

        # Port Box
        port_box = QGroupBox("Port number")

        port = QSpinBox()
        port.setMaximumWidth(100)
        port.setMaximum(65535)
        port.setValue(self.stream.tcp_settings.port)

        port_layout = QHBoxLayout(port_box)
        port_layout.addWidget(port)
        port_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Final Layout

        result_layout.addWidget(connection_mode_box)
        result_layout.addWidget(host_name_box)
        result_layout.addWidget(port_box)
        result_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # SIGNALS
        client_mode.clicked.connect(lambda : self.stream.tcp_settings.set_stream_mode(StreamMode.CLIENT))
        server_mode.clicked.connect(lambda : self.stream.tcp_settings.set_stream_mode(StreamMode.SERVER))
        host_name.editingFinished.connect(lambda : self.stream.tcp_settings.set_host(host_name.text()))
        port.editingFinished.connect(lambda : self.stream.tcp_settings.set_port(port.value()))

        return result

    def udp_menu(self):
        """udp configure tab
        """
        result = QWidget() 
        result_layout = QVBoxLayout(result)

        #Host name box
        host_name_box = QGroupBox("Host-Name or IP-Address")

        specific_host = QCheckBox("Listen/Transmit to a specific Host Name or IP Address")
        host_name = QLineEdit()
        host_name.setText(self.stream.udp_settings.host)
        host_name.setDisabled(True)

        host_name_layout = QVBoxLayout(host_name_box)
        host_name_layout.addWidget(specific_host)
        host_name_layout.addWidget(host_name)
        host_name_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Port Box
        port_box = QGroupBox("Port number")

        port = QSpinBox()
        port.setMaximumWidth(100)
        port.setMaximum(65535)
        port.setValue(self.stream.udp_settings.port)

        port_layout = QHBoxLayout(port_box)
        port_layout.addWidget(port)
        port_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Data flow Box
        data_flow_box = QGroupBox("Data Flow")

        data_flow_box_layout = QHBoxLayout(data_flow_box)
        data_flow_list = QComboBox()
        for dataflow in UdpSettings.DataFlow :
            data_flow_list.addItem( dataflow.name , dataflow )
        if self.stream.udp_settings.dataflow is not None :
            index = data_flow_list.findData(self.stream.udp_settings.dataflow)
        data_flow_list.setCurrentIndex(index)
        data_flow_box_layout.addWidget(data_flow_list)

        # Final Layout
        result_layout.addWidget(host_name_box)
        result_layout.addWidget(port_box)
        result_layout.addWidget(data_flow_box)
        result_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # SIGNALS
        specific_host.toggled.connect(lambda : host_name.setDisabled( not specific_host.isChecked()))
        host_name.editingFinished.connect(lambda : self.stream.udp_settings.set_host(host_name.text()))
        port.editingFinished.connect(lambda : self.stream.udp_settings.set_port(int(port.text())))
        data_flow_list.currentIndexChanged.connect(lambda : self.stream.udp_settings.set_dataflow(data_flow_list.currentData()))

        return result

    def ntrip_menu(self):
        """ntrip config tab
        """
        result = QWidget()
        result_layout = QVBoxLayout(result)

        # Host name Box

        ntrip_caster_box = QGroupBox("Ntrip Caster")
        ntrip_caster_layout = QVBoxLayout(ntrip_caster_box)

        self.ntrip_host_name = QLineEdit()
        self.ntrip_host_name.setText(self.stream.ntrip_client.ntrip_settings.host)
        host_name_label= QLabel("Host : ")
        host_name_label.setBuddy(self.ntrip_host_name)

        host_name_layout = QHBoxLayout()
        host_name_layout.addWidget(host_name_label)
        host_name_layout.addWidget(self.ntrip_host_name)
        host_name_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        ntrip_caster_layout.addLayout(host_name_layout)

        # Port Box
        port = QSpinBox()
        port.setMaximumWidth(100)
        port.setMaximum(65535)
        port.setValue(self.stream.ntrip_client.ntrip_settings.port)

        port_label = QLabel("Port : ")
        port_label.setBuddy(port)

        port_layout = QHBoxLayout()
        port_layout.addWidget(port_label)
        port_layout.addWidget(port)
        port_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        port_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        ntrip_caster_layout.addLayout(port_layout)

        # Stream - MountPoint Box
        mount_point_box = QGroupBox("Stream")
        mount_point_box_layout = QVBoxLayout(mount_point_box)
        self.mountpoint_list = QComboBox()
        self.mountpoint_list.setPlaceholderText("List unavailable")
        self.task_get_new_source_table()
        mount_point_box_layout.addWidget(self.mountpoint_list)
        # TLS
        tls_box = QGroupBox("TLS")
        tls_box.setCheckable(True)
        tls_box.setChecked(self.stream.ntrip_client.ntrip_settings.tls)

        tls_box_layout = QVBoxLayout(tls_box)

        self.cert = QLineEdit()
        self.cert.setText(self.stream.ntrip_client.ntrip_settings.cert)
        cert_label= QLabel("Certificate : ")
        cert_label.setBuddy(self.cert)
        cert_select_file = QPushButton("...")
        cert_select_file.setToolTip("Only .cer, .crt, .pem or .key Files are allowed")
        tls_box_layout.addLayout(pair_h_widgets(cert_label,self.cert,cert_select_file))

        # Authentification Box
        auth_box = QGroupBox("Authentification")
        auth_box.setCheckable(True)
        auth_box.setChecked(self.stream.ntrip_client.ntrip_settings.auth)

        auth_box_layout = QVBoxLayout(auth_box)

        user = QLineEdit()
        user.setText(self.stream.ntrip_client.ntrip_settings.username)
        user_label= QLabel("User : ")
        user_label.setBuddy(user)
        auth_box_layout.addLayout(pair_h_widgets(user_label,user))

        password = QLineEdit()
        password.setText(self.stream.ntrip_client.ntrip_settings.password)
        password_label= QLabel("Password : ")
        password_label.setBuddy(password)
        auth_box_layout.addLayout(pair_h_widgets(password_label , password))

        # FIXED POSITION Box

        fixed_position_box = QGroupBox("Fixed position for GGA ")  
        fixed_position_box.setCheckable(True)
        fixed_position_box.setChecked(self.stream.ntrip_client.ntrip_settings.fixed_pos)

        fixed_position_box_layout = QVBoxLayout(fixed_position_box)

        latitude = QLineEdit()
        latitude.setInputMask("!N 99.999999999")
        input_validator = QRegularExpressionValidator(QRegularExpression("[NS] [0-9]{2}.[0-9]{9}"))
        latitude.setValidator(input_validator)
        latitude.setText(self.stream.ntrip_client.ntrip_settings.get_latitude())
        latitude_label= QLabel("Latitude : ")
        latitude_label.setBuddy(latitude)
        fixed_position_box_layout.addLayout(pair_h_widgets(latitude_label,latitude))

        longitude = QLineEdit()
        longitude.setInputMask("!E 999.999999999")
        input_validator = QRegularExpressionValidator(QRegularExpression("[EW] [0-9]{3}.[0-9]{9}"))
        longitude.setValidator(input_validator)
        longitude.setText(self.stream.ntrip_client.ntrip_settings.get_longitude())
        longitude_label= QLabel("Longitude : ")
        longitude_label.setBuddy(longitude)
        fixed_position_box_layout.addLayout(pair_h_widgets(longitude_label,longitude))

        height = QSpinBox()
        height.setMaximum(100000)
        height.setMaximumWidth(100)
        height.setValue(self.stream.ntrip_client.ntrip_settings.height)
        height_label = QLabel("Height")
        height_label.setBuddy(height)
        fixed_position_box_layout.addLayout(pair_h_widgets(height_label,height))

        # Final Layout
        result_layout.addWidget(ntrip_caster_box)
        result_layout.addWidget(mount_point_box)
        result_layout.addWidget(tls_box)
        result_layout.addWidget(auth_box)
        result_layout.addWidget(fixed_position_box)
        result_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        #   SIGNALS
        self.ntrip_host_name.editingFinished.connect(lambda: self.update_mountpoint_list())
        self.ntrip_host_name.editingFinished.emit()

        port.valueChanged.connect(lambda : self.stream.ntrip_client.ntrip_settings.set_port(port.value()))

        self.mountpoint_list.currentIndexChanged.connect(lambda : self.stream.ntrip_client.ntrip_settings.set_mountpoint(self.mountpoint_list.currentData()))

        auth_box.toggled.connect(lambda : self.stream.ntrip_client.ntrip_settings.set_auth(auth_box.isChecked()))
        user.editingFinished.connect(lambda : self.stream.ntrip_client.ntrip_settings.set_username(user.text()))
        password.editingFinished.connect(lambda : self.stream.ntrip_client.ntrip_settings.set_password(password.text()))
        fixed_position_box.toggled.connect(lambda : self.stream.ntrip_client.ntrip_settings.set_fixed_pos(fixed_position_box.isChecked()))
        latitude.editingFinished.connect(lambda : self.stream.ntrip_client.ntrip_settings.set_latitude(latitude.text()))
        longitude.editingFinished.connect(lambda : self.stream.ntrip_client.ntrip_settings.set_longitude(longitude.text()))
        height.valueChanged.connect(lambda x : self.stream.ntrip_client.ntrip_settings.set_height(height.value()))
        cert_select_file.pressed.connect(self.select_cert_file )
        self.cert.editingFinished.connect(lambda : self.stream.ntrip_client.ntrip_settings.set_cert(self.cert.text()))
        tls_box.toggled.connect(lambda : self.stream.ntrip_client.ntrip_settings.set_tls(tls_box.isChecked()))
        return result
        
    def update_mountpoint_list(self):
        """update the list of available mountpoint selectable.
        """
        self.mountpoint_list.clear()
        self.mountpoint_list.setPlaceholderText("Waiting for source table ...")
        self.update_thread = QThread()
        self.worker = SourceTableWorker(self)
        self.worker.moveToThread(self.update_thread)
        self.update_thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.update_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.update_thread.finished.connect(self.update_thread.deleteLater)
        self.update_thread.finished.connect(self.cleanup)
        self.worker.finished.connect(self.task_get_new_source_table)

        self.update_thread.start()

    def cleanup(self):
        self.update_thread = None
        self.worker = None

    def task_get_new_source_table(self):
        """ get new source table from the new ntrip caster
        """
        if len(self.ntrip_host_name.text()) < 1 :
            self.mountpoint_list.setPlaceholderText("List unavailable")
        else :
            try :
                if self.stream.ntrip_client.ntrip_settings.source_table is None :
                    self.mountpoint_list.setPlaceholderText("List unavailable")
                
                elif len(self.stream.ntrip_client.ntrip_settings.source_table) != 0:
                    currentindex : int = 3
                    for source, index in zip(self.stream.ntrip_client.ntrip_settings.source_table , range(len(self.stream.ntrip_client.ntrip_settings.source_table))):
                        self.mountpoint_list.addItem(source.mountpoint, source.mountpoint)
                        if self.stream.ntrip_client.ntrip_settings.mountpoint is not None and self.stream.ntrip_client.ntrip_settings.mountpoint == source.mountpoint:
                            currentindex = index
                            
                    self.mountpoint_list.setPlaceholderText("")
                    self.mountpoint_list.setCurrentIndex(currentindex)
                else :
                    self.mountpoint_list.setPlaceholderText("List unavailable")
            except NtripClientError :
                self.mountpoint_list.setPlaceholderText("List unavailable")

    def bottom_button_layout(self):
        """Create the ok and cancel button of the dialog
        """

        #Valid Button : confirm all modification
        valid_button = QPushButton("OK")
        valid_button.pressed.connect(self.confirm)

        #return : close the dialog with no modification

        return_button = QPushButton("Cancel")
        return_button.pressed.connect(self.cancel)

        bottom_button_layout = QHBoxLayout()
        bottom_button_layout.addWidget(valid_button)
        bottom_button_layout.addWidget(return_button)

        return bottom_button_layout

    def confirm(self):
        """function called when ok button is pressed
        """
        self.save_previous_tab.emit(self.config_tabs.currentIndex())
        if self.stream.ntrip_client.ntrip_settings.fixed_pos :
            self.stream.ntrip_client.create_gga_string()
        self.save_config.emit(self.stream)
        self.accept()

    def cancel(self):
        """function called when cancel button is pressed
        """
        self.save_config.emit(self.stream_save)
        self.reject()

    def open_script_file(self, input_widget : QLineEdit, checkbox: QCheckBox, connect_script : bool = None ):
        """open a dialog to get the path to the script file
        """
        if checkbox.isChecked():
            file_name = QFileDialog.getOpenFileName(self,"Select Script")
            if file_name[0] != '' and file_name[1] != '':
                try :
                    if connect_script:
                        self.stream.set_startup_script_path(file_name[0])
                        self.stream.set_startup_script()
                    else:
                        self.stream.set_close_script_path(file_name[0])
                        self.stream.set_close_script()
                    input_widget.setDisabled(False)
                    input_widget.setText(file_name[0])
                except StreamException :
                    checkbox.click()
                    input_widget.setDisabled(True)
            else:
                checkbox.click()
        else :
            input_widget.setDisabled(True)
            
    def select_log_file(self , logedit : QLineEdit  , checkbox : QCheckBox):
        """open the dialog to get the path to the log file
        """
        if checkbox.isChecked():
            file_name = QFileDialog.getSaveFileName(self,"Select log file ")
            if file_name[0] != '' and file_name[1] != '':
                try :
                    self.stream.set_logging_file_name(file_name[0])
                    self.stream.set_logging()
                    logedit.setDisabled(False)
                    logedit.setText(file_name[0])
                except StreamException : 
                    checkbox.click()
                    logedit.setDisabled(True)
            else:
                checkbox.click()
        else :
            logedit.setDisabled(True)

    def select_cert_file(self):
        """open a dialog to get the path to the certification file
        """
        file_name = QFileDialog.getOpenFileName(self,"Select certificat")
        if file_name[0] != '' and file_name[1] != '':
            if file_name[1] in [ ".cer", ".crt", ".pem"  ,".key"] :
                self.stream.ntrip_client.ntrip_settings.set_cert(file_name[0])
                self.cert.setText(file_name[0])
 
class ShowDataInterface(QDialog):

    def __init__(self,stream : Stream) -> None:
        super().__init__()
        self.stream = stream
        self.timer_id = self.startTimer(10)
        self.setMinimumSize(350,300)
        self.setBaseSize(350,300)
        self.setWindowIcon(QIcon(os.path.join(DATAFILESPATH , 'pyDatalink_icon.png')))
        self.setWindowTitle("Data Link Connection " + str(stream.stream_id))
        configure_layout = QVBoxLayout(self)
        self.show_data_output = QTextEdit()
        self.show_data_output.setLineWrapColumnOrWidth(1000)
        self.show_data_output.setLineWrapMode(QTextEdit.LineWrapMode.FixedPixelWidth)
        self.show_data_output.setReadOnly(True)
        self.freeze = False
        self.stream.show_incoming_data.set()
        self.stream.show_outgoing_data.set()

        self.send_command_edit = QLineEdit()
        self.send_command_edit.returnPressed.connect(lambda  : self.send_command(self.send_command_edit.text()))
        show_data = QComboBox()
        show_data.addItem("All Data")
        show_data.addItem("Only incomming Data")
        show_data.addItem("Only outgoing Data")
        show_data.setCurrentIndex(0)
        show_data.currentIndexChanged.connect(lambda e : self.change_data_visibility(e))

        configure_layout.addWidget(self.show_data_output)
        configure_layout.addWidget(self.send_command_edit)
        configure_layout.addWidget(show_data)
        configure_layout.addLayout(self.bottom_button())

    def timerEvent(self, event):
        if self.stream.data_to_show.empty() is False :
            value = self.stream.data_to_show.get()
            if not self.freeze :
                self.show_data_output.insertPlainText( value + "\n" )
                self.show_data_output.moveCursor(QTextCursor.End)
                self.show_data_output.horizontalScrollBar().setValue(self.show_data_output.horizontalScrollBar().minimum())

    def bottom_button(self):
        """ configuration of the bottom button of the show data dialog
        """

        #Valid Button : confirm all modification

        clear_button = QPushButton("Clear")
        clear_button.pressed.connect(self.show_data_output.clear)
        clear_button.setDefault(False)
        clear_button.setAutoDefault(False)
        self.freeze_button = QPushButton("Freeze")
        self.freeze_button.setDefault(False)
        self.freeze_button.setAutoDefault(False)
        self.freeze_button.pressed.connect(self.freeze_data_flow)
        valid_button = QPushButton("Close")
        valid_button.setDefault(False)
        valid_button.setAutoDefault(False)
        valid_button.pressed.connect(self.close_dialog)

        #return : close the dialog with no modification

        bottom_button_layout = QHBoxLayout()
        bottom_button_layout.addWidget(clear_button)
        bottom_button_layout.addWidget(self.freeze_button)
        bottom_button_layout.addWidget(valid_button)

        return bottom_button_layout
    def close_dialog(self):
        """function called when clossing the dialog
        """
        self.stream.show_incoming_data.clear()
        self.stream.show_outgoing_data.clear()
        self.killTimer(self.timer_id)
        self.reject()

    def closeEvent(self, event):
        """function called when clossing the dialog
        """
        self.stream.show_incoming_data.clear()
        self.stream.show_outgoing_data.clear()
        self.killTimer(self.timer_id)
        self.reject()

    def freeze_data_flow(self):
        """fonction that freeze the data flow 
        """
        self.freeze = not self.freeze

    def change_data_visibility(self,index):
        """modfy data visibility
        """
        if index == 0 :
            self.all_data_visibility()
        elif index == 1:
            self.incoming_data_visibility()
        elif index == 2 :
            self.outgoing_data_visibility()
        
    def all_data_visibility(self):
        """show all the data 
        """
        if not self.stream.show_incoming_data.is_set() :
            self.stream.show_incoming_data.set()
        if not self.stream.show_outgoing_data.is_set() :
            self.stream.show_outgoing_data.set()

    def incoming_data_visibility(self):
        """Show only the incoming data
        """
        if not self.stream.show_incoming_data.is_set() :
            self.stream.show_incoming_data.set()
        if  self.stream.show_outgoing_data.is_set() :
            self.stream.show_outgoing_data.clear()

    def outgoing_data_visibility(self):
        """Show only the outgoing data
        """
        if  self.stream.show_incoming_data.is_set() :
            self.stream.show_incoming_data.clear()
        if  not self.stream.show_outgoing_data.is_set() :
            self.stream.show_outgoing_data.set()
    def send_command(self,command):
        """send a command to the connected device
        """
        self.stream.send_command(command)
        self.send_command_edit.setText("")

class PreferencesInterface(QDialog):
    """class for the preference dialog
    """

    def __init__(self,preference : Preferences) -> None:
        super().__init__()

        self.preference = preference
        preference_layout = QVBoxLayout(self)
        self.setWindowIcon(QIcon(os.path.join(DATAFILESPATH , 'pyDatalink_icon.png')))
        self.setWindowTitle("Preferences")

        #Configuration File
        general_box = QGroupBox("General")
        general_layout = QVBoxLayout(general_box)
        config_name_label = QLabel("Current Config Name")
        config_name_input = QLineEdit()
        config_name_input.setText(preference.config_name)
        general_layout.addLayout(pair_h_widgets(config_name_label , config_name_input))

        # line Termination
        # List of 3 : \n \r \r\n
        line_termination_label = QLabel("Line Termination")
        line_termination_combobox = QComboBox()
        line_termination_combobox.addItem("<CR>","\n")
        line_termination_combobox.addItem("<LF>","\r")
        line_termination_combobox.addItem("<CR><LF>","\n\r")
        general_layout.addLayout(pair_h_widgets(line_termination_label,line_termination_combobox))

        #Number of streams
        max_stream_label = QLabel("Number of Port Panels")
        max_streams_input = QSpinBox()
        max_streams_input.setMaximumWidth(50)
        max_streams_input.setMaximum(6)
        max_streams_input.setMinimum(1)
        max_streams_input.setValue(preference.max_streams)
        general_layout.addLayout(pair_h_widgets(max_stream_label,max_streams_input))

        # connect list

        startup_connect_box = QGroupBox("connect at Startup")
        startup_connect_layout = QVBoxLayout(startup_connect_box)
        startup_connect_label = QLabel("Select the ports that should auto connect at startup")
        startup_connect_layout.addWidget(startup_connect_label)
        startup_connect_layout.addLayout(self.startup_connect_layout())
        

        # Final Layout

        preference_layout.addWidget(general_box)
        preference_layout.addWidget(startup_connect_box)
        preference_layout.addLayout(self.bottom_button_layout())

        #SIGNALS
        # self.preference.set_max_stream(newvalue)
        max_streams_input.valueChanged.connect(lambda  : self.preference.set_max_stream(max_streams_input.value()))
        line_termination_combobox.currentIndexChanged.connect(lambda : self.preference.set_line_termination(line_termination_combobox.currentData()))
        config_name_input.editingFinished.connect(lambda : self.preference.set_config_name(config_name_input.text()))
        
    def bottom_button_layout(self):
        """Create the ok and cancel button of the dialog
        """

        #Valid Button : confirm all modification
        valid_button = QPushButton("OK")
        valid_button.pressed.connect(self.accept)


        bottom_button_layout = QHBoxLayout()
        bottom_button_layout.addWidget(valid_button)

        return bottom_button_layout

    def startup_connect_layout(self):
        """
        Create connect on startup layout
        """
        startup_connect_final_layout = QVBoxLayout()
        for port_id in range(6):
            new_check_box = QCheckBox(f"connect {port_id}")
            if self.preference.connect[port_id] :
                new_check_box.setChecked(True)
            new_check_box.stateChanged.connect(lambda state,x=port_id : self.toggle_startup_connection(x))
            startup_connect_final_layout.addWidget(new_check_box)
        return startup_connect_final_layout

    def toggle_startup_connection(self, portid):
        """toggle the startup connect
        """
        self.preference.connect[portid] = not self.preference.connect[portid]

class AboutDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowIcon(QIcon(os.path.join(DATAFILESPATH , 'pyDatalink_icon.png')))
        self.setWindowTitle("About PyDatalink")
        button  = QDialogButtonBox.Ok

        self.button_box = QDialogButtonBox(button)
        self.button_box.accepted.connect(self.accept)
        # Add Version
        # add Link to github repo
        # add Description
        # Add Warning for still in testing
        self.dialoglayout = QVBoxLayout()

        about_logo_label = QLabel()
        logo = QPixmap(os.path.join(DATAFILESPATH ,"pyDatalink_Logo.png"))
        about_logo_label.setPixmap(logo)
        about_logo_label.setFixedSize(200,100)
        about_logo_label.setScaledContents(True)
        about_logo_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        about_label = QLabel()
        about_label.setText(" PyDatalink \n Version 1.0a\n 2024 , Septentrio")
        about_label.setStyleSheet(" font-weight: bold;")
        about_label.setScaledContents(True)

        self.dialoglayout.addLayout(pair_h_widgets(about_logo_label,about_label))
        self.dialoglayout.addWidget(self.button_box)
        self.dialoglayout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.setLayout(self.dialoglayout)

class SourceTableWorker(QObject):
    """worker for getting source table thread
    """
    finished = Signal()

    def __init__(self, configure_interface : ConfigureInterface):
        super().__init__()
        self.configure_interface = configure_interface

    def run(self):
        try :
            self.configure_interface.stream.ntrip_client.set_settings_host(self.configure_interface.ntrip_host_name.text())
        except NtripClientError:
            self.configure_interface.stream.ntrip_client.ntrip_settings.source_table = None
        self.finished.emit()

class StreamConnectWorker(QObject):
    """Worker for stream connect thread
    """
    finished = Signal()

    def __init__(self, connection_card : ConnectionCard):
        super().__init__()
        self.connection_card = connection_card

    def run(self):
        if not self.connection_card.stream.connected:
            try :
                self.connection_card.stream.connect()
                self.connection_card.configure_button.setDisabled(True)
                self.connection_card.status.setText("CONNECTED")
                self.connection_card.status.setStyleSheet("QLabel { color: #32a852;}")
                self.connection_card.connect_button.setText("Disconnect")
            except StreamException as e :
                self.connection_card.status.setText("ERROR DURING CONNECTION")
                self.connection_card.status.setToolTip(str(e))
                self.connection_card.status.setStyleSheet("QLabel { color: #c42323;}")
        else :
            try :
                self.connection_card.stream.disconnect()
                self.connection_card.configure_button.setDisabled(False)
                self.connection_card.status.setText("")
                self.connection_card.connect_button.setText("Connect")
            except StreamException as e :
                self.connection_card.status.setText("Couldn't disconnect")
                self.connection_card.status.setToolTip(str(e))
        self.finished.emit()
