from ..StreamConfig import *
import copy

import asyncio
import PySide6.QtAsyncio as QtAsyncio
from PySide6.QtCore import QSize, Qt , QRegularExpression
from PySide6.QtGui import QIntValidator , QRegularExpressionValidator,QTextCursor,QAction
from PySide6.QtWidgets import (QMainWindow, QApplication, QCheckBox, QComboBox,
                               QCommandLinkButton, QDateTimeEdit, QDial,
                               QDialog, QDialogButtonBox, QFileSystemModel,
                               QGridLayout, QGroupBox, QHBoxLayout, QLabel,
                               QLineEdit, QListView, QMenu, QPlainTextEdit,
                               QProgressBar, QPushButton, QRadioButton,
                               QScrollBar, QSizePolicy, QSlider, QSpinBox,
                               QStyleFactory, QTableWidget, QTabWidget,
                               QTextBrowser, QTextEdit, QToolBox, QToolButton,
                               QTreeView, QVBoxLayout, QWidget, QInputDialog,QFileDialog)


def PairWidgets(widget1, widget2 ) -> QHBoxLayout:
    result = QHBoxLayout()
    result.addWidget(widget1)
    result.addWidget(widget2)
    result.setAlignment(Qt.AlignmentFlag.AlignTop)
    return result

def TrioWidgets(widget1,widget2,widget3) -> QHBoxLayout:
    result = QHBoxLayout()
    result.addWidget(widget1)
    result.addWidget(widget2)
    result.addWidget(widget3)
    result.setAlignment(Qt.AlignmentFlag.AlignTop)
    return result


class GraphicalUserInterface(QMainWindow):
    
    def __init__(self, streams : Streams) -> None:
        super().__init__()
        self.setFixedSize(950,750)
        self.streams : Streams = streams
        self.streamsWidget : list[ConnectionCard] = []
        self.setWindowTitle("PyDataLink")
        
        # Menu bar 
        menuBar = self.menuBar()

        # Create a menu
        fileMenu = menuBar.addMenu('File')
        
        # IDEA -  TO DO 
        #confMenu = menuBar.addMenu('Config')
        #Save current Config
        #Load config
        #Change config
        
        # Create Preferences 
        preferenceAction = QAction("Preferences",self)
        preferenceAction.setShortcut('Ctrl+P')
        preferenceAction.triggered.connect(lambda p : self.openPreferenceInterface())
        
        # Create exit action
        exitAction = QAction('Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.triggered.connect(self.close)

        fileMenu.addAction(preferenceAction)
        fileMenu.addSeparator()
        fileMenu.addAction(exitAction)
        
        
        #Main Window layout
        mainLayout = QGridLayout()
        connectionCardLayout = QVBoxLayout()
        connectionCardLineLayout = QHBoxLayout()
        for i in range(self.streams.maxStream):
            newCard = ConnectionCard(i,self.streams.StreamList[i],self.streams.maxStream)
            self.streamsWidget.append(newCard)
            connectionCardLineLayout.addWidget(newCard.getWidget())
            if connectionCardLineLayout.count() == 3 :
                connectionCardLayout.addLayout(connectionCardLineLayout)
                connectionCardLineLayout = QHBoxLayout()
                
        if connectionCardLineLayout.count() < 3 :
            connectionCardLayout.addLayout(connectionCardLineLayout)
            
        mainLayout.addLayout(connectionCardLayout,0,0)

        widget = QWidget()
        widget.setLayout(mainLayout)
        self.setCentralWidget(widget)
        
        self.timer_id = self.startTimer(30)
        
    def timerEvent(self, event):
        for widget in self.streamsWidget:
            widget.refreshCards()
        
        
    def openPreferenceInterface(self):
        configureDialog = PreferencesInterface(self.streams.preferences)
        configureDialog.exec_()
        
    def closeEvent(self,event):
        self.streams.CloseAll()
        QApplication.quit()

class ConnectionCard :    
    def __init__(self,id : int ,stream : PortConfig , maxStreams : int ) -> None:
        self.stream = stream
        self.id = id
        self.maxStreams = maxStreams
        self.connectionCardWidget = self.ConnectionCard()
        
                
        
    def ConnectionCard(self):
        result = QGroupBox(f"Connection {self.id}")
        
        result.setFixedSize(300,350)
        #Top button
        self.connectButton = QPushButton("Connect")
        
        
        #Add slot : connect the selected stream
        self.configureButton = QPushButton("Configure")
        #add slot : create a new window to configure stream
        
        topButtonLayout = QHBoxLayout()
        topButtonLayout.addWidget(self.connectButton)
        topButtonLayout.addWidget(self.configureButton)
        
       # overviewText
        self.currentConfigOverview = QLabel()
        self.currentConfigOverview.setText(f"Current configuration :\n {self.stream.toString()}")
        self.currentConfigOverview.setAlignment(Qt.AlignmentFlag.AlignJustify)
        self.currentConfigOverview.setFixedHeight(150)
        
        # Status 
        self.status= QLabel()
        self.status.setAlignment(Qt.AlignHCenter)
        
        #Data Transfert 
        self.currentDataTransfert = QLabel()
        self.currentDataTransfert.setText(f"ingoing : {self.stream.dataTransferInput} kBps | outgoing : {self.stream.dataTransferOutput} kBps")
        self.currentDataTransfert.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        #showdata
        self.showDataButton = QPushButton("Show Data")
        
        
        # Final Layout
        cardLayout = QVBoxLayout(result)
        cardLayout.addLayout(topButtonLayout)
        cardLayout.addWidget(self.currentConfigOverview)
        cardLayout.addWidget(self.status)
        cardLayout.addWidget(self.currentDataTransfert)
        cardLayout.addLayout(self.linkLayout())
        cardLayout.addWidget(self.showDataButton)
        
        #Init in case of Startup Connect
        if self.stream.isConnected():
            self.connectButton.setText("Disonnect")
            self.configureButton.setDisabled(True)
            self.status.setText("Connected")
        # SIGNALS
        
        self.configureButton.pressed.connect(lambda : self.openConfigureInterface(self.stream))
        self.connectButton.pressed.connect(lambda : self.connectStream())
        self.showDataButton.pressed.connect(lambda : self.showData())
        
        return result
    
    def linkLayout(self):
        linkLayout = QHBoxLayout()
        linkLayout.addWidget(QLabel("Links : "))
        for a in range(self.maxStreams):
            newCheckBox = QCheckBox(str(a))
            if self.id == a :
                newCheckBox.setDisabled(True)
            if a in self.stream.linkedPort : 
                newCheckBox.setChecked(True)
            newCheckBox.stateChanged.connect(lambda state,x=a : self.toggleLinkedPort(x))
            
            linkLayout.addWidget(newCheckBox)
        return linkLayout
    def toggleLinkedPort(self , linkindex):
        self.stream.UpdatelinkedPort(linkindex)
    
    def openConfigureInterface(self,stream : PortConfig = None):
        configureDialog = ConfigureInterface(stream)
        configureDialog.accepted.connect(lambda : self.refreshCards())
        configureDialog.exec_()
        
    def refreshCards(self):
        self.currentConfigOverview.setText(f"Current configuration :\n {self.stream.toString()}")
        self.currentDataTransfert.setText(f"ingoing : {self.stream.dataTransferInput} kBps | outgoing : {self.stream.dataTransferOutput} kBps")
        if not self.stream.connected and self.connectButton.text() =="Disconnect" :
            self.connectButton.setText("Connect")
            self.configureButton.setDisabled(False)
            self.status.setText("")
        
        
    def connectStream(self):
        if not self.stream.connected:
            try : 
                self.stream.Connect()
                self.configureButton.setDisabled(True)
                self.status.setText("Connected")
                self.connectButton.setText("Disconnect")
            except Exception as e : 
                self.status.setText(f"Couldn't connect : \n {e}")
                self.status.setToolTip(str(e))
        else :
            try : 
                self.stream.Disconnect()
                self.configureButton.setDisabled(False)
                self.status.setText("")
                self.connectButton.setText("Connect")
            except Exception as e : 
                self.status.setText(f"Couldn't Disconnect : \n {e}")
                self.status.setToolTip(str(e))
                
    def showData(self):
        if self.stream.ShowInputData.is_set() or self.stream.ShowOutputData.is_set():
            self.showDataButton.setText("Show Data")
            self.showdatadialog.closeDialog()
        else:
            self.showDataButton.setText("Hide Data")
            self.showdatadialog = ShowDataInterface(self.stream)
            self.showdatadialog.finished.connect(lambda : self.showDataButton.setText("Show Data"))
            self.showdatadialog.show()
            
    
    def getWidget(self):
        return self.connectionCardWidget
   
        
class ConfigureInterface(QDialog) :
    def __init__(self , stream : PortConfig  = None) -> None:
        super().__init__()
        self.setWindowTitle(f"Configure Connection {stream.id}")
        self.stream = stream
        self.streamsave = copy.copy(stream)
        self.setModal(True)
        self.setFixedSize(350,580)
        configureLayout = QVBoxLayout(self)
        
        serialMenu = self.serialMenu()
        tcpMenu = self.tcpMenu()
        udpMenu =  self.udpMenu()
        ntripMenu = self.ntripMenu()
        
        configTabs = QTabWidget()
        configTabs.addTab(self.generalMenu(), "General")
        index = configTabs.addTab(serialMenu , "Serial")            
        configTabs.addTab(tcpMenu, "TCP")
        configTabs.addTab(udpMenu, "UDP")
        configTabs.addTab(ntripMenu, "NTRIP")
        
        if len(SerialSettings.GetAvailablePort()) == 0 : 
            configTabs.setTabEnabled(index,False)

        configureLayout.addWidget(configTabs)
        configureLayout.addLayout(self.bottomButtonLayout())
        
    def generalMenu(self):
        result = QGroupBox(f"General Settings")
        
        # Select Connection
        streamTypeBox = QGroupBox("Select the connection type")
        streamTypeBoxLayout = QHBoxLayout(streamTypeBox)
        streamTypeList = QComboBox()
        for type in StreamType :
            streamTypeList.addItem(type.name, type)
        if self.stream.serialSettings.baudrate is not None :
            index = streamTypeList.findData(self.stream.StreamType) 
        else : 
            index = streamTypeList.findData(StreamType.NONE)
        streamTypeList.setCurrentIndex(index)
        streamTypeBoxLayout.addWidget(streamTypeList)
        streamTypeBoxLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        # Connect/Close Script
        scriptBox = QGroupBox("Scripts")
        scriptBoxLayout = QVBoxLayout(scriptBox)
        
        openScriptCheckBox = QCheckBox()
        openScriptCheckBox.setChecked(self.stream.sendStartupScript)
        openScriptLabel = QLabel("Connect Script : ")
        openScriptEdit = QLineEdit()
        openScriptEdit.setDisabled(not self.stream.sendStartupScript)
        openScriptEdit.setText(self.stream.startupScript)
        scriptBoxLayout.addLayout(TrioWidgets(openScriptCheckBox,openScriptLabel,openScriptEdit))
        
        closeScriptCheckBox = QCheckBox()
        closeScriptCheckBox.setChecked(self.stream.sendCloseScript)
        closeScriptLabel = QLabel("Close Script : ")
        closeScriptEdit = QLineEdit()
        closeScriptEdit.setDisabled(not self.stream.sendCloseScript)
        closeScriptEdit.setText(self.stream.closeScript)
        scriptBoxLayout.addLayout(TrioWidgets(closeScriptCheckBox,closeScriptLabel,closeScriptEdit))
    
        # Logging file 
        logBox = QGroupBox("Logging")
        logBoxLayout = QVBoxLayout(logBox)
        
        logCheckBox = QCheckBox()
        logLabel = QLabel("Log File : ")
        logEdit = QLineEdit()
        logEdit.setDisabled(True)
        logBoxLayout.addLayout(TrioWidgets(logCheckBox,logLabel,logEdit))
        
        # Final Layout 
        resultLayout = QVBoxLayout(result)
        resultLayout.addWidget(streamTypeBox)
        resultLayout.addWidget(scriptBox)
        resultLayout.addWidget(logBox)
        resultLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # SIGNALS
        
        streamTypeList.currentIndexChanged.connect(lambda : self.stream.setStreamType(streamTypeList.currentData()))
        openScriptCheckBox.checkStateChanged.connect(lambda : self.openScriptFile(openScriptEdit,openScriptCheckBox , True))
        closeScriptCheckBox.checkStateChanged.connect(lambda : self.openScriptFile(closeScriptEdit,closeScriptCheckBox , False))
        
        return result
    
        
    def serialMenu(self):
        result = QGroupBox(f"Serial connection")
        
        #Available Port
        availablePortList = QComboBox()
        ports = SerialSettings.GetAvailablePort() 
        if len(ports) > 0 : 
            for port in ports : 
                availablePortList.addItem(port[0].replace("/dev/ttyACM","COM") + " - " + port[1].split("-")[0],port[0])
            availablePortList.setCurrentIndex(-1)
        else : 
            availablePortList.addItem("no com port detected")
            availablePortList.setDisabled(True)
        if self.stream.serialSettings.port != "":
            index = availablePortList.findData(self.stream.serialSettings.port)
            availablePortList.setCurrentIndex(index)
        availablePortLabel = QLabel("Port COM:")
        availablePortLabel.setBuddy(availablePortList)
        
        #Baudrate
        baudRateList = QComboBox()
        for baudrate in BaudRate :
            baudRateList.addItem(baudrate.value, baudrate)
        if self.stream.serialSettings.baudrate is not None :
            index = baudRateList.findData(self.stream.serialSettings.baudrate) 
            baudRateList.setCurrentIndex(index)
        baudRateListLabel = QLabel("Baudrate :")
        baudRateListLabel.setBuddy(baudRateList)        
        
        #Parity
        parityList = QComboBox()
        for parity in Parity :
            parityList.addItem( parity.value + " - " +  parity.name.replace("PARITY_","") , parity )
        if self.stream.serialSettings.parity is not None :
            index = parityList.findData(self.stream.serialSettings.parity) 
            parityList.setCurrentIndex(index)
        parityListLabel = QLabel("Parity :")
        parityListLabel.setBuddy(parityList)
        
        #Stop bits
        stopBitsList = QComboBox()
        for stopbits in StopBits :
            stopBitsList.addItem(str(stopbits.value),stopbits)
        if self.stream.serialSettings.stopbits is not None :
            index = stopBitsList.findData(self.stream.serialSettings.stopbits) 
            stopBitsList.setCurrentIndex(index)
        stopBitsListLabel = QLabel("StopBits :")
        stopBitsListLabel.setBuddy(stopBitsList)
        
         #ByteSize
        byteSizeList = QComboBox()
        for bytesize in ByteSize :
            byteSizeList.addItem(str(bytesize.value) , bytesize)
        index = byteSizeList.findData(self.stream.serialSettings.bytesize) 
        byteSizeList.setCurrentIndex(index)
        byteSizeListLabel = QLabel("Bytesize :")
        byteSizeListLabel.setBuddy(byteSizeList)
        
        #RTscts
        rtsctsList = QComboBox()
        rtsctsList.addItem("True", True)
        rtsctsList.addItem("False", False)   
        index = rtsctsList.findData(self.stream.serialSettings.rtscts) 
        rtsctsList.setCurrentIndex(index)
        rtsctsListLabel = QLabel("Rts-Cts :")
        rtsctsListLabel.setBuddy(rtsctsList)
        
                 
        # Final Layout
        widgetLayout = QVBoxLayout(result)
        widgetLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        widgetLayout.addLayout(PairWidgets(availablePortLabel , availablePortList))
        widgetLayout.addLayout(PairWidgets(baudRateListLabel,baudRateList))
        widgetLayout.addLayout(PairWidgets(parityListLabel,parityList))
        widgetLayout.addLayout(PairWidgets(stopBitsListLabel,stopBitsList))
        widgetLayout.addLayout(PairWidgets(byteSizeListLabel ,byteSizeList ))
        widgetLayout.addLayout(PairWidgets(rtsctsListLabel,rtsctsList))
        
        # SIGNAL
        availablePortList.currentIndexChanged.connect(lambda : self.stream.serialSettings.setPort(availablePortList.currentData()))
        parityList.currentIndexChanged.connect(lambda : self.stream.serialSettings.set_parity(parityList.currentData()))
        baudRateList.currentIndexChanged.connect(lambda : self.stream.serialSettings.set_baudrate(baudRateList.currentData()))
        stopBitsList.currentIndexChanged.connect(lambda : self.stream.serialSettings.set_stopbits(stopBitsList.currentData()))
        byteSizeList.currentIndexChanged.connect(lambda : self.stream.serialSettings.set_bytesize(byteSizeList.currentData()))
        rtsctsList.currentIndexChanged.connect(lambda : self.stream.serialSettings.set_rtscts(rtsctsList.currentData()))
        return result
    
    def tcpMenu(self):
        
        result = QWidget()        
        resultLayout = QVBoxLayout(result)
        
        # Connection mode Box
        connectionModeBox = QGroupBox("Connection Mode")
        clientMode = QRadioButton("TCP/IP Client")
        serverMode = QRadioButton("TCP/IP Server")
        if self.stream.tcpSettings.StreamMode == StreamMode.CLIENT:
            clientMode.setChecked(True)
        else:
            serverMode.setChecked(True)
        
        connectionModeLayout = QHBoxLayout(connectionModeBox)
        connectionModeLayout.addWidget(clientMode)
        connectionModeLayout.addWidget(serverMode)
        connectionModeLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Host name Box
        hostNameBox = QGroupBox("Host-Name or IP-Address")
        
        hostName = QLineEdit()
        hostName.setText(self.stream.tcpSettings.host)
        
        hostNameLayout = QHBoxLayout(hostNameBox)
        hostNameLayout.addWidget(hostName)
        hostNameLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        serverMode.toggled.connect(hostName.setDisabled)
        
        # Port Box 
        PortBox = QGroupBox("Port number")
        
        Port = QSpinBox()
        Port.setMaximumWidth(100)
        Port.setMaximum(65535)
        Port.setValue(self.stream.tcpSettings.port)
    
        PortLayout = QHBoxLayout(PortBox)
        PortLayout.addWidget(Port)
        PortLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Final Layout
        
        resultLayout.addWidget(connectionModeBox)
        resultLayout.addWidget(hostNameBox)
        resultLayout.addWidget(PortBox)
        resultLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # SIGNALS
        clientMode.clicked.connect(lambda : self.stream.tcpSettings.set_StreamMode(StreamMode.CLIENT))
        serverMode.clicked.connect(lambda : self.stream.tcpSettings.set_StreamMode(StreamMode.SERVER))
        hostName.editingFinished.connect(lambda : self.stream.tcpSettings.setHost(hostName.text()))
        Port.editingFinished.connect(lambda : self.stream.tcpSettings.setPort(Port.value()))
        
        return result
    
    def udpMenu(self):
        result = QWidget()        
        resultLayout = QVBoxLayout(result)
        
        #Host name box
        hostNameBox = QGroupBox("Host-Name or IP-Address")
        
        specificHost = QCheckBox("Listen/Transmit to a specific Host Name or IP Address")
        hostName = QLineEdit()
        hostName.setText(self.stream.udpSettings.host)
        hostName.setDisabled(True)
        
        hostNameLayout = QVBoxLayout(hostNameBox)
        hostNameLayout.addWidget(specificHost)
        hostNameLayout.addWidget(hostName)
        hostNameLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Port Box
        PortBox = QGroupBox("Port number")
        
        Port = QSpinBox()
        Port.setMaximumWidth(100)
        Port.setMaximum(65535)
        Port.setValue(self.stream.udpSettings.port)
        
        PortLayout = QHBoxLayout(PortBox)
        PortLayout.addWidget(Port)
        PortLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Data flow Box
        dataFlowBox = QGroupBox("Data Flow")
        
        dataFlowBoxLayout = QHBoxLayout(dataFlowBox)
        dataflowList = QComboBox()
        for dataflow in DataFlow :
            dataflowList.addItem( dataflow.name , dataflow )
        if self.stream.udpSettings.DataFlow is not None :
            index = dataflowList.findData(self.stream.udpSettings.DataFlow) 
        dataflowList.setCurrentIndex(index)
        dataFlowBoxLayout.addWidget(dataflowList)
        
        # Final Layout 
        resultLayout.addWidget(hostNameBox)
        resultLayout.addWidget(PortBox)
        resultLayout.addWidget(dataFlowBox)
        resultLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # SIGNALS
        specificHost.toggled.connect(lambda : hostName.setDisabled( not specificHost.isChecked()))
        
        hostName.editingFinished.connect(lambda : self.stream.udpSettings.setHost(hostName.text()))
        Port.editingFinished.connect(lambda : self.stream.udpSettings.setPort(Port.text()))
        dataflowList.currentIndexChanged.connect(lambda : self.stream.udpSettings.set_DataFlow(dataflowList.currentData()))
        
        return result

    def ntripMenu(self):
        result = QWidget()        
        resultLayout = QVBoxLayout(result)
        
        # Host name Box
        
        ntripCasterBox = QGroupBox("Ntrip Caster")   
        ntripCasterLayout = QVBoxLayout(ntripCasterBox) 
        
        hostName = QLineEdit()
        hostName.setText(self.stream.ntripClient.ntripSettings.host)
        hostNameLabel= QLabel("Host : ")
        hostNameLabel.setBuddy(hostName)
        
        hostNameLayout = QHBoxLayout()
        hostNameLayout.addWidget(hostNameLabel)
        hostNameLayout.addWidget(hostName)
        hostNameLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        ntripCasterLayout.addLayout(hostNameLayout)
        
        # Port Box
        Port = QSpinBox()
        Port.setMaximumWidth(100)
        Port.setMaximum(65535)
        Port.setValue(self.stream.ntripClient.ntripSettings.port)
        
        PortLabel = QLabel("Port : ")
        PortLabel.setBuddy(Port)
        
        PortLayout = QHBoxLayout()
        PortLayout.addWidget(PortLabel)
        PortLayout.addWidget(Port)
        PortLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        PortLayout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        ntripCasterLayout.addLayout(PortLayout)
        
        
        # Stream - MountPoint Box
        mountPointBox = QGroupBox("Stream")   
        mountPointBoxLayout = QVBoxLayout(mountPointBox)
        mountPointList = QComboBox()
        mountPointList.setPlaceholderText("List unavailable")

        mountPointBoxLayout.addWidget(mountPointList)
        # TLS
        tlsBox = QGroupBox("TLS")  
        tlsBox.setCheckable(True)
        tlsBox.setChecked(self.stream.ntripClient.ntripSettings.tls)
        
        tlsBoxLayout = QVBoxLayout(tlsBox)
        
        self.cert = QLineEdit()
        self.cert.setText(self.stream.ntripClient.ntripSettings.cert)
        certLabel= QLabel("Certificate : ")
        certLabel.setBuddy(self.cert)
        certSelectFile = QPushButton("...")
        certSelectFile.setToolTip("Only .cer, .crt, .pem or .key Files are allowed")
        tlsBoxLayout.addLayout(TrioWidgets(certLabel,self.cert,certSelectFile))
        
        # Authentification Box
        authBox = QGroupBox("Authentification")  
        authBox.setCheckable(True)
        authBox.setChecked(self.stream.ntripClient.ntripSettings.auth)
        
        authBoxLayout = QVBoxLayout(authBox)
        
        user = QLineEdit()
        user.setText(self.stream.ntripClient.ntripSettings.username)
        userLabel= QLabel("User : ")
        userLabel.setBuddy(user)
        authBoxLayout.addLayout(PairWidgets(userLabel,user))
        
        password = QLineEdit()
        password.setText(self.stream.ntripClient.ntripSettings.password)
        passwordLabel= QLabel("Password : ")
        passwordLabel.setBuddy(password)
        authBoxLayout.addLayout(PairWidgets(passwordLabel , password))
        
        # FIXED POSITION Box
        
        fixedPositionBox = QGroupBox("Fixed position for GGA ")  
        fixedPositionBox.setCheckable(True)
        fixedPositionBox.setChecked(self.stream.ntripClient.ntripSettings.fixedPos)
        
        fixedPositionBoxLayout = QVBoxLayout(fixedPositionBox)
        
        latitude = QLineEdit()
        latitude.setInputMask("!N 99.999999999")
        input_validator = QRegularExpressionValidator(QRegularExpression("[NS] [0-9]{2}.[0-9]{9}"))
        latitude.setValidator(input_validator)
        latitude.setText(self.stream.ntripClient.ntripSettings.getLatitude())
        latitudeLabel= QLabel("Latitude : ")
        latitudeLabel.setBuddy(latitude)
        fixedPositionBoxLayout.addLayout(PairWidgets(latitudeLabel,latitude))
        
        longitude = QLineEdit()         
        longitude.setInputMask("!E 999.999999999")
        input_validator = QRegularExpressionValidator(QRegularExpression("[EW] [0-9]{3}.[0-9]{9}"))
        longitude.setValidator(input_validator)
        longitude.setText(self.stream.ntripClient.ntripSettings.getLongitude())
        longitudeLabel= QLabel("Longitude : ")
        longitudeLabel.setBuddy(longitude)
        fixedPositionBoxLayout.addLayout(PairWidgets(longitudeLabel,longitude))
        
        height = QSpinBox()
        height.setMaximum(100000)
        height.setMaximumWidth(100)
        height.setValue(self.stream.ntripClient.ntripSettings.height)
        heightLabel = QLabel("Height")
        heightLabel.setBuddy(height)
        fixedPositionBoxLayout.addLayout(PairWidgets(heightLabel,height))
        

        # Final Layout
        resultLayout.addWidget(ntripCasterBox)
        resultLayout.addWidget(mountPointBox)
        resultLayout.addWidget(tlsBox)
        resultLayout.addWidget(authBox)
        resultLayout.addWidget(fixedPositionBox)
        resultLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        #   SIGNALS
        hostName.editingFinished.connect(lambda :  self.updateMountpointList(mountPointList , hostName))
        hostName.editingFinished.emit()
        
        Port.valueChanged.connect(lambda : self.stream.ntripClient.ntripSettings.setPort(Port.value()))
        
        mountPointList.currentIndexChanged.connect(lambda : self.stream.ntripClient.ntripSettings.setMountpoint(mountPointList.currentData()))
        
        authBox.toggled.connect(lambda : self.stream.ntripClient.ntripSettings.setAuth(authBox.isChecked()))
        user.editingFinished.connect(lambda : self.stream.ntripClient.ntripSettings.setUsername(user.text()))
        password.editingFinished.connect(lambda : self.stream.ntripClient.ntripSettings.setPassword(password.text()))
        fixedPositionBox.toggled.connect(lambda : self.stream.ntripClient.ntripSettings.setFixedPos(fixedPositionBox.isChecked()))
        latitude.editingFinished.connect(lambda : self.stream.ntripClient.ntripSettings.setLatitude(latitude.text()))
        longitude.editingFinished.connect(lambda : self.stream.ntripClient.ntripSettings.setLongitude(longitude.text()))
        height.valueChanged.connect(lambda x : self.stream.ntripClient.ntripSettings.setHeight(height.value()))
        certSelectFile.pressed.connect(lambda : self.selectCertFile() )
        self.cert.editingFinished.connect(lambda : self.stream.ntripClient.ntripSettings.setCert(self.cert.text()))
        tlsBox.toggled.connect(lambda : self.stream.ntripClient.ntripSettings.setTls(tlsBox.isChecked()))
        return result
        
    def updateMountpointList(self, mountPointList: QComboBox, hostName: QLineEdit):
            mountPointList.clear()
            if len(hostName.text()) > 0:
                try:
                    self.stream.ntripClient.set_Settings_Host(hostName.text())
                    sourcetable = self.stream.ntripClient.ntripSettings.sourceTable
                    if len(sourcetable) != 0:
                        for source in sourcetable:
                            mountPointList.addItem(source.mountpoint, source.mountpoint)
                            if self.stream.ntripClient.ntripSettings.mountpoint is not None:
                                index = mountPointList.findData(self.stream.ntripClient.ntripSettings.mountpoint)
                            else : 
                                index : int = 3
                            mountPointList.setPlaceholderText("")
                            mountPointList.setCurrentIndex(index)
                except:
                    mountPointList.setPlaceholderText("List unavailable")
            else:
                mountPointList.setPlaceholderText("List unavailable")
            
    def bottomButtonLayout(self):
                
        #Valid Button : confirm all modification
        validButton = QPushButton("OK")
        validButton.pressed.connect(self.confirm)
        
        #return : close the dialog with no modification
        
        returnButton = QPushButton("Cancel")
        returnButton.pressed.connect(self.cancel)
        
        bottomButtonLayout = QHBoxLayout()
        bottomButtonLayout.addWidget(validButton)
        bottomButtonLayout.addWidget(returnButton)
        
        return bottomButtonLayout        
    def confirm(self):
        if self.stream.ntripClient.ntripSettings.fixedPos :
            self.stream.ntripClient._createGgaString()
        self.accept()
    
    def cancel(self):
        self.stream = self.streamsave
        self.reject()
        
    def openScriptFile(self, inputWidget : QLineEdit, checkbox: QCheckBox, connectScript : bool = None ):
        if connectScript :
            self.stream.sendStartupScript = checkbox.isChecked()
        else :
            self.stream.sendCloseScript = checkbox.isChecked()
        if checkbox.isChecked(): 
            fileName = QFileDialog.getOpenFileName(self,"Select Script")
            if fileName[0] != '' and fileName[1] != '':
                try : 
                    if connectScript:
                        self.stream.setStartupScriptPath(fileName[0])
                        self.stream.setStartupScript()
                    else:
                        self.stream.setCloseScriptPath(fileName[0])
                        self.stream.setCloseScript()
                    inputWidget.setDisabled(False)
                    inputWidget.setText(fileName[0])
                except : 
                    print("problem")
                    checkbox.click()
                    inputWidget.setDisabled(True)
            else: 
                checkbox.click()
        else :
            inputWidget.setDisabled(True)
    
    def selectCertFile(self):
            fileName = QFileDialog.getOpenFileName(self,"Select certificat")
            if fileName[0] != '' and fileName[1] != '':
                if fileName[1] in [ ".cer", ".crt", ".pem"  ,".key"] :
                    self.stream.ntripClient.ntripSettings.setCert(fileName[0])
                    self.cert.setText(fileName[0])


class ShowDataInterface(QDialog):

    def __init__(self,stream : PortConfig) -> None:
        super().__init__()
        self.stream = stream
        self.setFixedSize(350,300)
        self.setWindowTitle("Data Link Connection " + str(stream.id))
        configureLayout = QVBoxLayout(self)
        self.showDataOutput = QTextEdit()
        self.showDataOutput.setLineWrapColumnOrWidth(1000) 
        self.showDataOutput.setLineWrapMode(QTextEdit.LineWrapMode.FixedPixelWidth)
        self.showDataOutput.setReadOnly(True)
        self.freeze = False
        self.stream.ShowInputData.set()
        self.stream.ShowOutputData.set()
        
        self.sendCommandEdit = QLineEdit()
        self.sendCommandEdit.returnPressed.connect(lambda  : self.sendCommand(self.sendCommandEdit.text()))
        showData = QComboBox()
        showData.addItem("All Data")
        showData.addItem("Only incomming Data")
        showData.addItem("Only outgoing Data")
        showData.setCurrentIndex(0)
        showData.currentIndexChanged.connect(lambda test : self.changeDataVisibility(test))
        
        configureLayout.addWidget(self.showDataOutput)
        configureLayout.addWidget(self.sendCommandEdit)
        configureLayout.addWidget(showData)
        configureLayout.addLayout(self.bottomButton())
        
        self.timer_id = self.startTimer(10)
        
    def timerEvent(self, event):
        if self.stream.DataToShow.empty() is False :
                value = self.stream.DataToShow.get()
                if not self.freeze :
                    self.showDataOutput.insertPlainText( value + "\n" )
                    self.showDataOutput.moveCursor(QTextCursor.End)
                    self.showDataOutput.horizontalScrollBar().setValue(self.showDataOutput.horizontalScrollBar().minimum())
        
        
    def bottomButton(self):
        
        #Valid Button : confirm all modification

        
        clearButton = QPushButton("Clear")
        clearButton.pressed.connect(lambda : self.showDataOutput.clear())
        clearButton.setDefault(False)
        clearButton.setAutoDefault(False)
        freezeButton = QPushButton("Freeze")
        freezeButton.setDefault(False)
        freezeButton.setAutoDefault(False)
        freezeButton.pressed.connect(lambda : self.freezeDataFlow())
        validButton = QPushButton("Close")
        validButton.setDefault(False)
        validButton.setAutoDefault(False)
        validButton.pressed.connect(lambda : self.closeDialog())
        
        #return : close the dialog with no modification
        
        bottomButtonLayout = QHBoxLayout()
        bottomButtonLayout.addWidget(clearButton)
        bottomButtonLayout.addWidget(freezeButton)
        bottomButtonLayout.addWidget(validButton)
        
        return bottomButtonLayout
    def closeDialog(self):
        self.stream.ShowInputData.clear()
        self.stream.ShowOutputData.clear()
        self.killTimer(self.timer_id)
        self.reject()
        
    def closeEvent(self, event):
        self.stream.ShowInputData.clear()
        self.stream.ShowOutputData.clear()
        self.killTimer(self.timer_id)
        self.reject()
        
    def freezeDataFlow(self):
        self.freeze = not self.freeze
        
    def changeDataVisibility(self,index):
        if index == 0 : 
            self.allDataVisibility()
        elif index == 1:
            self.incomingDataVisibility()
        elif index == 2 :
            self.outgoingDataVisibility()
        
    def allDataVisibility(self):
        if not self.stream.ShowInputData.is_set() :
            self.stream.ShowInputData.set()
        if not self.stream.ShowOutputData.is_set() :
            self.stream.ShowOutputData.set()
            
    def incomingDataVisibility(self):
        if not self.stream.ShowInputData.is_set() :
            self.stream.ShowInputData.set()
        if  self.stream.ShowOutputData.is_set() :
            self.stream.ShowOutputData.clear()

    def outgoingDataVisibility(self):
        if  self.stream.ShowInputData.is_set() :
            self.stream.ShowInputData.clear()
        if  not self.stream.ShowOutputData.is_set() :
            self.stream.ShowOutputData.set()
     
    def sendCommand(self,CMD):
        self.stream.sendCommand(CMD)
        self.sendCommandEdit.setText("")
class PreferencesInterface(QDialog):
    
    def __init__(self,preference : Preferences) -> None:
        super().__init__()
        
        self.preference = preference
        preferenceLayout = QVBoxLayout(self)
        
        #Configuration File 
        generalBox = QGroupBox("General")
        generalLayout = QVBoxLayout(generalBox)
        configNameLabel = QLabel("Current Config Name")
        configNameInput = QLineEdit()
        configNameInput.setText(preference.configName)
        generalLayout.addLayout(PairWidgets(configNameLabel , configNameInput))
        
        # line Termination
        # List of 3 : \n \r \r\n
        lineTerminationLabel = QLabel("Line Termination")
        lineTerminationComboBox = QComboBox()
        lineTerminationComboBox.addItem("<CR>","\n")
        lineTerminationComboBox.addItem("<LF>","\r")
        lineTerminationComboBox.addItem("<CR><LF>","\n\r")
        generalLayout.addLayout(PairWidgets(lineTerminationLabel,lineTerminationComboBox))
        
        #Number of streams
        maxStreamLabel = QLabel("Number of Port Panels")
        maxStreamsInput = QSpinBox()
        maxStreamsInput.setMaximumWidth(50)
        maxStreamsInput.setMaximum(6)
        maxStreamsInput.setMinimum(1)
        maxStreamsInput.setValue(preference.maxStreams)
        generalLayout.addLayout(PairWidgets(maxStreamLabel,maxStreamsInput))
        
        # Connect list
        
        startupConnectBox = QGroupBox("Connect at Startup")
        startupConnectLayout = QVBoxLayout(startupConnectBox)
        startupConnectLabel = QLabel("Select the ports that should auto connect at startup")
        startupConnectLayout.addWidget(startupConnectLabel)
        startupConnectLayout.addLayout(self.startupConnectLayout())
              
        # Final Layout
        
        preferenceLayout.addWidget(generalBox)
        preferenceLayout.addWidget(startupConnectBox)
        
        #SIGNALS
        # self.preference.setMaxStream(newvalue)
        maxStreamsInput.valueChanged.connect(lambda  : self.preference.setMaxStream(maxStreamsInput.value()))
        lineTerminationComboBox.currentIndexChanged.connect(lambda : self.preference.setLineTermination(lineTerminationComboBox.currentData()))
        configNameInput.editingFinished.connect(lambda : self.preference.setConfigName(configNameInput.text()))
        
        
        
    def startupConnectLayout(self):
        startupConnectFinalLayout = QVBoxLayout()   
        for portId in range(6):
            newCheckBox = QCheckBox(f"Connect {portId}")
            if self.preference.Connect[portId] : 
                newCheckBox.setChecked(True)
            newCheckBox.stateChanged.connect(lambda state,x=portId : self.toggleStartupConnection(x))
            startupConnectFinalLayout.addWidget(newCheckBox)
        return startupConnectFinalLayout
    
    def toggleStartupConnection(self, portid):
        self.preference.Connect[portid] = not self.preference.Connect[portid]
        