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
import copy
from  datetime import datetime
from enum import Enum
import os
import socket
import time
from serial import Serial
import threading
import configparser
import queue
import logging
from ..NTRIP import *
from .UdpSettings import *
from .SerialSettings import *
from .TcpSettings import *
from .Preferences import *

class StreamType(Enum):
    Serial = 0
    TCP = 1
    UDP = 2
    NTRIP = 3
    NONE = None
    
def Task_UpdateLinkedPort(updateLinkedPort : queue.Queue , LinkedPort : list[int] ):
        for _ in range(updateLinkedPort.qsize()):
                    port = updateLinkedPort.get()
                    if port in LinkedPort:
                        LinkedPort.remove(port)
                    else:
                        LinkedPort.append(port)
        return LinkedPort
def Task_SendCommand(linkedData : queue.Queue , Stream , ShowData : bool = False , udpsendaddress : str = None 
                     , DataToShow : queue.Queue = None , logger : logging = None , lineTermination : str = "\r\n"):
    try : 
        for _ in range(linkedData.qsize()):
            outputData : str = linkedData.get()
            if type(Stream) == Serial :
                Stream.write((outputData+"\n").encode(encoding='ISO-8859-1'))
            elif type(Stream) == socket.socket and udpsendaddress is None: 
                Stream.sendall((outputData + lineTermination).encode(encoding='ISO-8859-1'))
            elif type(Stream) == socket.socket:
                Stream.sendto((outputData + lineTermination).encode(encoding='ISO-8859-1'), udpsendaddress)
            elif type(Stream) == NtripClient :
                if "GPGGA" in outputData:
                    Stream.sendNMEA(outputData)             
            else : continue
            if ShowData and len(outputData) != 0 : 
                DataToShow.put(outputData)
                if logger is not None:
                    logger.log(0,outputData)
            return len(outputData)
    except Exception as e :
        raise e
                    

class PortConfig:
    """
    Represents a port/stream for data streaming.
    
    """

    def __init__(self, id: int = 0, linkedData: list[queue.Queue] = None ,confFile : configparser.SectionProxy = None  
                 , commandLineConfig : str = None ):

        self.id = id
        self.linkedPort: list[int] = []
        self.connected: bool = False  
        self.currentTask = None
        self.StreamType: StreamType = StreamType.NONE
        self.Stream : Serial | socket.socket | NtripClient  = None
        self.lineTermination :str = "\r\n"
        self.dataTransferInput : float = 0.0
        self.dataTransferOutput :float = 0.0
        
        # logging file 
        self.logging : bool = False
        self.loggingFile : str = ""
        self.logger : logging  = None 
        # Startup and close script
        self.startupScript : str = "" 
        self.closeScript : str = ""
        self.sendStartupScript : bool = False
        self.sendCloseScript : bool = False

        # Event for data visibility and stop

        self.ShowInputData = threading.Event()
        self.ShowOutputData = threading.Event()
        self.StopEvent = threading.Event()

        # Queue for data link between ports

        self.linkedData = linkedData
        self.updateLinkedPort: queue.Queue = queue.Queue()
        self.DataToShow: queue.Queue = queue.Queue()

        # Thread for data read/link

        self.dataLinkStreamThread: threading.Thread = None

        # Stream settings
        if confFile is not None:
            self.ConfFileConfig(confFile)
        elif commandLineConfig is not None :
            self.CommandLineConfig(commandLineConfig)       
        else:
            self.serialSettings = SerialSettings()
            self.tcpSettings = TcpSettings()
            self.udpSettings = UdpSettings()
            self.ntripClient = NtripClient()

    
        
    def Connect(self, Streamtype : StreamType = None):
        """
        Connects the port using the specified Stream type.

        Args:
            Streamtype: The type of Stream.

        Returns:
            int: 0 if the Stream fails, otherwise None.
        """
        if Streamtype is None : 
            Streamtype = self.StreamType
        if self.connected is not True:
            if Streamtype == StreamType.Serial:
                if self.serialSettings.port != "":
                    try:
                        self.Stream = self.serialSettings.Connect()
                        self.connected = True
                        task = self.DatalinkSerialTask
                        self.StreamType = Streamtype
                    except Exception as e:
                        self.Stream = None
                        self.connected = False
                        raise e
                else:
                    raise Exception("Connection Error","Serial port hasn't been configured yet")
            elif Streamtype == StreamType.TCP:
                if self.tcpSettings is not None:
                    try:
                        socket.gethostbyname(self.tcpSettings.host)
                        self.Stream = self.tcpSettings.connect()
                        self.connected = True
                        if self.tcpSettings.StreamMode == StreamMode.SERVER:
                            task = self.DatalinkTCPServerTask
                        else :
                            task = self.DatalinkTCPClientTask
                        self.StreamType = Streamtype
                    except socket.gaierror as e:
                        self.Stream = None
                        self.connected = False
                        raise e
                    except ConnectionRefusedError as e:
                        self.Stream = None
                        self.connected = False
                        raise e
                    except Exception as e :
                        self.Stream = None
                        self.connected = False
                        raise e
                else:
                    raise Exception("Connection Error","tcp settings are empty !")
            elif Streamtype == StreamType.UDP:
                if self.udpSettings is not None:
                    try:
                        socket.gethostbyname(self.tcpSettings.host)
                        self.Stream = self.udpSettings.connect()
                    except Exception as e:
                        self.Stream = None
                        self.connected = False
                        raise e
                else:
                    raise Exception("Connection Error","udp settings are empty!")
            elif Streamtype == StreamType.NTRIP:
                    if self.ntripClient is not None:
                        try:
                            if len(self.ntripClient.ntripSettings.host.replace(" ","")) != 0 :
                                socket.gethostbyname(self.ntripClient.ntripSettings.host)
                                self.ntripClient.connect()
                                self.Stream = self.ntripClient
                                self.StopEvent.clear()
                                self.connected = True
                                task = self.DatalinkNTRIPTask
                                self.StreamType = Streamtype   
                                if self.ntripClient.ntripSettings.fixedPos:
                                    self.ntripClient._createGgaString()
                            else:
                                raise Exception("Connection Error","NTRIP host is not set !")
                        except Exception as e:
                            self.Stream = None
                            self.connected = False 
                            raise e
                    else:
                        raise Exception("Connection Error","ntrip client is not set !")
            else:
                raise Exception("Connection Error","Invalid Stream type!")
            if self.connected is True:
                try:
                    
                    self.StopEvent.clear()
                    if self.logging :
                        self.logger = logging.getLogger(self.loggingFile)
                    if self.sendStartupScript:
                        self._clearQueue(self.linkedData[self.id])
                        self.sendScript(self.linkedData[self.id], True)
                    self.dataLinkStreamThread = threading.Thread(target=task,args=(self.Stream, self.linkedData, self.updateLinkedPort,self.DataToShow))
                    self.dataLinkStreamThread.start()  
                    self.currentTask = task
                    if len(self.linkedPort) != 0:    
                        for link in self.linkedPort:  
                            self.updateLinkedPort.put(link)
                except Exception as e:
                    self.connected = False
                    raise e

    def Disconnect(self):
        """
        Disconnects the port if is connected.
        """
        if self.Stream is not None:
            try:
                if self.sendCloseScript:
                    self.sendScript(self.linkedData[self.id], False)
                self.StopEvent.set()
                self.currentTask = None
                self.dataLinkStreamThread.join()
                self.Stream.close()
                self.connected = False
                self.dataTransferInput = 0.0
                self.dataTransferOutput = 0.0
            except Exception as e:
                raise e
      
    def UpdatelinkedPort(self, link : int):
        """
        Updates the linked port with the specified link.

        Args:
            link: The link to update.

        """
        if link in self.linkedPort:
            self.linkedPort.remove(link)
        else:
            self.linkedPort.append(link)
        if self.connected :
            self.updateLinkedPort.put(link)

    def toString(self):
        """
        Return current running stream settings class as a string
        Returns:
            classToString(str , None):  Return the class as a string
        """
        if self.StreamType == StreamType.Serial:
            return self.serialSettings.toString()
        elif self.StreamType == StreamType.TCP:
            return self.tcpSettings.toString()
        elif self.StreamType == StreamType.UDP:
            return self.udpSettings.toString()
        elif self.StreamType == StreamType.NTRIP:
            return self.ntripClient.ntripSettings.toString()
        else:
            return None
        
    def sendScript(self, queue : queue.Queue , startup : bool):
        """
        ouput every command found in a script file
        Args:
            queue (queue.Queue): output queue
            startup (bool): if startup script then True , else False

        Raises:
            Exception: Error while opening script file 
        """
        try : 
            if startup :
                if self.startupScript != "":
                    OpenScript = open(self.startupScript,"r")
                    if OpenScript is not None:
                        for line in OpenScript:
                            queue.put(line)
            else :
                 if self.closeScript != "":
                    OpenScript = open(self.closeScript,"r")
                    if OpenScript is not None:
                        for line in OpenScript:
                            queue.put(line)
                
        except Exception as e:
            raise Exception("Error : couldn't open the script file " + e)
    
    def sendCommand(self, CMD :str):    
        """
        send a command to ouput
        """    
        self.linkedData[self.id].put(CMD)
    # Getter & Setter 
      
    def ToggleInputDataVisibility(self):
        """
        Toggles the visibility of input data.
        """
        self.ShowInputData.clear() if self.ShowInputData.is_set() is True else self.ShowInputData.set()

    def ToggleOutputDataVisibility(self):
        """
        Toggles the visibility of output data.
        """
        self.ShowOutputData.clear() if self.ShowOutputData.is_set() is True else self.ShowOutputData.set()

    def ToggleAllDataVisibility(self):
        """
        Toggle the data visibility for both output and input
        """
        self.ToggleInputDataVisibility()
        self.ToggleOutputDataVisibility()

    def setLogging(self):
        """
        Toggle the logging event
        """
        if self.logging:
            self.logging = False
        else :
            self.logging = True
    
    def setStartupScript(self):
        """
        Toggle the send script on startup event
        """
        if self.sendStartupScript :
            self.sendStartupScript = False
        else : 
            self.sendStartupScript = True
            
    def setCloseScript(self):
        """
        Toggle the send script on closeup event
        """
        if self.sendCloseScript :
            self.sendCloseScript = False
        else : 
            self.sendCloseScript = True
            
    def setCloseScriptPath(self , newpath :str ):
        """
        set the path to the closeup script file

        Args:
            newpath (str): the new path to the closeup script

        Raises:
            Exception: File not found
        """
        if os.path.exists(newpath) :
            self.closeScript = newpath
        else : 
            raise Exception("File not found !")
        
    def setStartupScriptPath(self,newpath :str ):
        """
        set the path to the startup script file
        Args:
            newpath (str): the new path to the startup script

        Raises:
            Exception: File not Found 
        """
        if os.path.exists(newpath) :
            self.startupScript = newpath
        else : 
            raise Exception("File not found !")
        
    def setLoggingFileName(self,newFileName : str):
        """
        Set the logging file name use when logging is True

        Args:
            newFileName (str): the new file name of the logging file
        """
        if os.path.exists("./log"):
            os.makedirs("./log")
        self.loggingFile = newFileName
        
    def setStreamType(self,newStreamType : StreamType):
        """
        Change the stream type of the current stream

        Args:
            newStreamType (StreamType): the new stream type
        """
        self.StreamType = newStreamType
        
    def setLineTermination(self,newLineTermination :str):
        """
        set new line of termination

        Args:
            newLineTermination (str): the new line termination
        """
        self.lineTermination = newLineTermination
    
    def isConnected(self):
        """
        return the current state of the stream

        Returns:
            status(bool): return True if stream is connected , otherwise False
        """
        if self.dataLinkStreamThread is None :
            return False
        if self.dataLinkStreamThread.is_alive() :
            self.connected = True
        else :
            self.connected = False
        return self.connected 
    
    
    
    # Thread task Methods 
    
    def DatalinkSerialTask(self, serial: Serial, linkedData: list[queue.Queue], updateLinkedPort: queue.Queue 
                           , dataToShow : queue.Queue  ):
        """
        The task for data link Stream using serial communication.

        Args:
            serial: The serial Stream object.
            linkedData: A list of linked data queues.
            updateLinkedPort: The queue for updating linked ports.

        Returns:
            int: 0 if the task completes, otherwise None.
        """
        LinkedPort = []
        datarate = 0 
        tempInputTranfert = 0
        tempOutputTransfert = 0
        # Send startup command
        try:
            if not linkedData[self.id].empty():
                Task_SendCommand(linkedData[self.id],serial,logger=self.logger,lineTermination=self.lineTermination)
        except Exception as e :
            self._ExceptionDisconnect()
            raise Exception("Error : Start script couldn't finish " + e)
        currentTime = datetime.now()
        #Main loop
        while self.StopEvent.is_set() is not True:
            now = datetime.now()
            if (now-currentTime).total_seconds() >=  1 : 
                currentTime = now 
                self.dataTransferInput = round(tempInputTranfert/1000,1)
                self.dataTransferOutput = round(tempOutputTransfert/1000,1)
                tempInputTranfert = 0 
                tempOutputTransfert = 0
            try:
                if serial is not None:
                    if serial.is_open:
                        inputData = serial.readline().decode(encoding='ISO-8859-1')
                        
                        tempInputTranfert += len(inputData)
                        if self.ShowInputData.is_set() and len(inputData) != 0:
                            dataToShow.put(inputData)
                            if self.logging:
                                self.logger.log(0,inputData)
                        if LinkedPort is not None:
                            for portid in LinkedPort:
                                portQueue: queue.Queue = linkedData[portid]
                                portQueue.put(inputData)
                        if not linkedData[self.id].empty():
                            tempOutputTransfert += Task_SendCommand(linkedData[self.id],serial,self.ShowOutputData.is_set(), DataToShow=dataToShow,logger=self.logger,lineTermination=self.lineTermination )
            except Exception as e:
                self._ExceptionDisconnect()
                raise Exception(f"Stream {self.id} {self.StreamType} has been disconnected, error: {e}")
            #Update current linked Streams list
            if not updateLinkedPort.empty():
                Task_UpdateLinkedPort(updateLinkedPort , LinkedPort)
        #Send closeup commands
        try : 
            if not linkedData[self.id].empty():
                Task_SendCommand(linkedData[self.id],serial,logger=self.logger,lineTermination=self.lineTermination)
        except Exception as e :
            raise Exception("Error : closing script couldn't finish " + e)
        return 0

    def DatalinkTCPServerTask(self, tcp: socket.socket, linkedData: list[queue.Queue], updateLinkedPort: queue.Queue 
                              ,  dataToShow : queue.Queue):
        """
        The task for data link Stream using TCP communication.

        """
        LinkedPort: list[int] = []
        tcp.settimeout(0.1)
        tcp.setblocking(0)
        tempInputTranfert = 0
        tempOutputTransfert = 0
        # Wait for a client to connect to the server
        while True:
                try:
                    tcp.listen()
                    conn, address = tcp.accept()
                    conn.settimeout(0.1)
                    break
                except Exception as e :
                    if self.StopEvent.is_set():
                        return 0
        # Send startup command
        try:
            if not linkedData[self.id].empty():
                Task_SendCommand(linkedData[self.id],conn,logger=self.logger,lineTermination=self.lineTermination)
        except Exception as e :
            self._ExceptionDisconnect()
            raise Exception("Error : Start script couldn't finish " + e)
        currentTime = datetime.now()
        #Main loop
        while self.StopEvent.is_set() is not True:
            now = datetime.now()
            if (now-currentTime).total_seconds() >=  1 : 
                currentTime = now 
                self.dataTransferInput = round(tempInputTranfert/1000,1)
                self.dataTransferOutput = round(tempOutputTransfert/1000,1)
                tempInputTranfert = 0 
                tempOutputTransfert = 0
            try:
                #If a client is connected
                if conn is not None:
                    #Read input data 
                    try:
                        inputData = conn.recv(4096).decode(encoding='ISO-8859-1')
                        tempInputTranfert += len(inputData)
                        if len(inputData) == 0:
                            conn = None
                    except socket.timeout:
                        inputData = ""
                    # Print data if show data input 
                    if self.ShowInputData.is_set() and len(inputData) != 0:
                        dataToShow.put(inputData)
                        if self.logging:
                                self.logger.log(0,inputData)
                    # Send input data to linked Streams
                    if LinkedPort is not None and len(inputData) != 0:
                        for portid in LinkedPort:
                            portQueue: queue.Queue = linkedData[portid]
                            portQueue.put(inputData)
                            
                    #Send output data comming from other streams and print data if showdata is set
                    if not linkedData[self.id].empty():
                        tempOutputTransfert+= Task_SendCommand(linkedData[self.id] , conn , self.ShowOutputData.is_set(), DataToShow=dataToShow,logger=self.logger,lineTermination=self.lineTermination)
                else : 
                    time.sleep(1)
                    #Wait for a new Client if the current one has disconnect
                    
                    while True:
                        try:
                            tcp.listen()
                            conn, address = tcp.accept()
                            conn.settimeout(0.1)
                            break
                        except Exception as e:
                            if self.StopEvent.is_set():
                                print("end")
                                return 0
            except Exception as e:
                self._ExceptionDisconnect()
                raise Exception(f"Stream {self.id} {self.StreamType} has been disconnected, error: {e}")
            #Update current linked Streams list
            if not updateLinkedPort.empty():
                LinkedPort = Task_UpdateLinkedPort(updateLinkedPort , LinkedPort)
        #Send closeup commands
        try : 
            if not linkedData[self.id].empty():
               Task_SendCommand(linkedData[self.id],conn,logger=self.logger,lineTermination=self.lineTermination)
        except Exception as e :
            raise Exception("Error : closing script couldn't finish " + e)
        return 0
    
    def DatalinkTCPClientTask(self, tcp: socket.socket, linkedData: list[queue.Queue], updateLinkedPort: queue.Queue 
                              ,  dataToShow : queue.Queue):
        """
        The task for data link Stream using TCP communication.

        """
        LinkedPort: list[int] = []
        tcp.settimeout(0.1)
        conn = 1
        tempInputTranfert = 0
        tempOutputTransfert = 0
        #Send startup command
        try:
            if not linkedData[self.id].empty():
                Task_SendCommand(linkedData[self.id],tcp,logger=self.logger,lineTermination=self.lineTermination)
        except Exception as e :
                        self._ExceptionDisconnect()
                        self.connected = False
                        raise Exception("Error : Start script couldn't finish " + e)
        currentTime = datetime.now()
        #Main loop
        while self.StopEvent.is_set() is not True:
            now = datetime.now()
            if (now-currentTime).total_seconds() >=  1 : 
                currentTime = now 
                self.dataTransferInput = round(tempInputTranfert/1000,1)
                self.dataTransferOutput = round(tempOutputTransfert/1000,1)
                tempInputTranfert = 0 
                tempOutputTransfert = 0          
            try:
                #While Connection still up 
                if conn  is not None :
                    #Read input data 
                    try:
                        inputData = tcp.recv(4096).decode(encoding='ISO-8859-1')
                        tempInputTranfert += len(inputData)
                        if len(inputData) == 0:
                            conn = None
                    except socket.timeout:
                        inputData = ""
                    except ConnectionResetError : 
                        conn = None
                    except BrokenPipeError : 
                        conn = None
                    # Print if show data 
                    if self.ShowInputData.is_set() and len(inputData) != 0:
                        dataToShow.put(inputData)
                        if self.logging:
                                self.logger.log(0,inputData)
                    # Send data to linked stream
                    if LinkedPort is not None and len(inputData) != 0:
                        for portid in LinkedPort:
                            portQueue: queue.Queue = linkedData[portid]
                            portQueue.put(inputData)
                    # Output data comming from other streams
                    if not linkedData[self.id].empty():
                        tempOutputTransfert+= Task_SendCommand(linkedData[self.id],tcp,self.ShowOutputData.is_set(),DataToShow=dataToShow,logger=self.logger,lineTermination=self.lineTermination)
                else : 
                    # If connection Lost try to reconnect to the server 
                    while True:
                        try:
                            tcp = self.tcpSettings.connect()
                            conn = 1
                            break
                        except Exception as e:
                            if self.StopEvent.is_set():
                                return 0
                            
            #If there is any probleme , disconnect everything and kill thread 
            except Exception as e:
                self._ExceptionDisconnect()
                raise Exception(f"Stream {self.id} {self.StreamType} has been disconnected, error: {e}")
            
            # Update Current linked Stream list
            if not updateLinkedPort.empty():
                Task_UpdateLinkedPort(updateLinkedPort,LinkedPort)
        # Send Closeup command
        try : 
            Task_SendCommand(linkedData[self.id],tcp,logger=self.logger,lineTermination=self.lineTermination)
        except Exception as e :
            raise Exception("Error : closing script couldn't finish " + e)
        return 0
                    
    def DatalinkUDPTask(self, udp: socket.socket, linkedData: list[queue.Queue], updateLinkedPort: queue.Queue 
                        ,  dataToShow : queue.Queue):
        """
        Task for data link Stream using UDP communication.
        """
        LinkedPort = []
        tempInputTranfert = 0
        tempOutputTransfert = 0
        if self.udpSettings.specificHost is True:
            sendaddress = (self.udpSettings.host, self.udpSettings.port)
        else:
            sendaddress = ('', self.udpSettings.port)
        #Send Startup command
        try:
            if not linkedData[self.id].empty():
                if sendaddress is not None:
                    Task_SendCommand(linkedData[self.id] , Stream=udp , udpsendaddress=sendaddress,logger=self.logger,lineTermination=self.lineTermination)
        except Exception as e :
            self._ExceptionDisconnect()
            raise Exception("Error : Start script couldn't finish " + e)
        currentTime = datetime.now()
        #Main loop
        while self.StopEvent.is_set() is not True:
            now = datetime.now()
            if (now-currentTime).total_seconds() >=  1 : 
                currentTime = now 
                self.dataTransferInput = round(tempInputTranfert/1000,1)
                self.dataTransferOutput = round(tempOutputTransfert/1000,1)
                tempInputTranfert = 0 
                tempOutputTransfert = 0 
            try:
                #Continue is Stream is still up
                if udp is not None:
                    if self.udpSettings.DataFlow in (1, 2):
                        bytesAddressPair = udp.recvfrom(4096)
                        inputData = bytesAddressPair[0].decode(encoding='ISO-8859-1')
                        tempInputTranfert += len(inputData)
                        
                        if self.ShowInputData.is_set() and len(inputData) != 0:
                            dataToShow.put(inputData)
                            if self.logging:
                                self.logger.log(0,inputData)
                            
                        if LinkedPort is not None and len(inputData) != 0:
                            for port in LinkedPort:
                                linkedData[port].put(inputData)

                    if self.udpSettings.DataFlow in (0, 2):
                        if not linkedData[self.id].empty():
                            if sendaddress is not None:
                                tempOutputTransfert+= Task_SendCommand(linkedData[self.id] , udp , self.ShowOutputData.is_set() , sendaddress, dataToShow,logger=self.logger,lineTermination=self.lineTermination)
            except Exception as e:
                self._ExceptionDisconnect()
                raise Exception(f"Stream {self.id} {self.StreamType.name} has been disconnected, error: {e}")
            #Update linked Streams list
            if not updateLinkedPort.empty():
                Task_UpdateLinkedPort(updateLinkedPort,LinkedPort)
        #Send closeup Commands
        try : 
            if not linkedData[self.id].empty():
                if sendaddress is not None:
                    Task_SendCommand(linkedData[self.id] ,Stream= udp  , udpsendaddress=sendaddress,logger=self.logger,lineTermination=self.lineTermination)
        except Exception as e :
            raise Exception("Error : closing script couldn't finish " + e)
        return 0
    
    def DatalinkNTRIPTask(self, ntrip: NtripClient, linkedData: list[queue.Queue], updateLinkedPort: queue.Queue 
                          ,  dataToShow : queue.Queue):
        """
        Process the NTRIP data received from the NTRIP client and send correction to other the linked streams .

        Args:
            ntrip (NtripClient): The NTRIP client object.
            linkedData (list[queue.Queue]): list of queues for sending or reading data to/from other streams .
            updateLinkedPort (queue.Queue): The queue for updating the linked ports.
        """
        LinkedPort: list[int] = []
        ntrip.socket.settimeout(0.1)
        tempInputTranfert = 0
        tempOutputTransfert = 0
        # Send startup command
        try:
            if self.ntripClient.ntripSettings.fixedPos :
                linkedData[self.id].put(self.ntripClient.fixedPosGga)
            if not linkedData[self.id].empty():
                Task_SendCommand(linkedData[self.id],ntrip ,logger=self.logger,lineTermination=self.lineTermination)
        except Exception as e :
            self._ExceptionDisconnect()
            raise Exception("Error : Start script couldn't finish " + e)         
        currentTime = datetime.now()
        #Main loop
        while self.StopEvent.is_set() is not True:
            now = datetime.now()
            if (now-currentTime).total_seconds() >=  1 : 
                currentTime = now 
                self.dataTransferInput = round(tempInputTranfert/1000,1)
                self.dataTransferOutput = round(tempOutputTransfert/1000,1)
                tempInputTranfert = 0 
                tempOutputTransfert = 0 
            try:
                if ntrip is not None:
                    #Read input data 
                    try:
                        inputData = ntrip.socket.recv(4096).decode(encoding='ISO-8859-1')
                        tempInputTranfert += len(inputData)
                    except socket.timeout:
                        inputData = ""
                    # Print data if show data input 
                    if self.ShowInputData.is_set() and len(inputData) != 0:
                        dataToShow.put(inputData)
                        if self.logging:
                                self.logger.log(0,inputData)
                        
                    # Send input data to linked Streams
                    if LinkedPort is not None and len(inputData) != 0:
                        for portid in LinkedPort:
                            portQueue: queue.Queue = linkedData[portid]
                            portQueue.put(inputData)
                    #Send output data comming from other streams and print data if showdata is set
                    if not linkedData[self.id].empty():
                        print("not empty")
                        tempOutputTransfert+= Task_SendCommand(linkedData[self.id],ntrip ,self.ShowOutputData.is_set(),DataToShow=dataToShow,logger=self.logger,lineTermination=self.lineTermination)
                        
            except Exception as e:
                self._ExceptionDisconnect()
                raise Exception(f"Stream {self.id} {self.StreamType} has been disconnected, error: {e}")
            
            #Update current linked Streams list
            if not updateLinkedPort.empty():
                Task_UpdateLinkedPort(updateLinkedPort,LinkedPort)
        #Send closeup commands
        try : 
            if not linkedData[self.id].empty():
                Task_SendCommand(linkedData[self.id],ntrip,logger=self.logger,lineTermination=self.lineTermination)
        except Exception as e :
            self._ExceptionDisconnect()
            raise Exception("Error : closing script couldn't finish " + e) 
        return 0

    # Command line Configuration Functions 
    
    def CommandLineConfig(self,commandLineConfig : str):
        """
        Configure a Stream with a single line of configuration 
        
        Args:
            commandLineConfig (str): Configuration line 

        """
        PortToLink = []
        try :
                streamType :str = commandLineConfig.split("://")[0]
                config: str = commandLineConfig.split("://")[1]
                if '#' in config : 
                    PortToLink = config.split("#")[1].split(",")
                    config = config.split("#")[0]
                if streamType.lower() == "serial":
                    self.ConfigSerialStream(commandConfig=config)
                elif streamType.lower() == "tcpcli":
                    self.ConfigTCPStream(isServer=False , commandConfig=config)
                elif streamType.lower() == "tcpsrv":
                    self.ConfigTCPStream(isServer=True, commandConfig=config)
                elif streamType.lower() == "udp":
                    self.ConfigUDPStream(commandConfig=config)
                elif streamType.lower() == "udpspe":
                    self.ConfigUDPStream(specificHost=True, commandConfig= config)
                elif streamType.lower() == "ntrip":
                    self.ConfigNTRIPStream(config)
                    
        except Exception as e  : 
                raise Exception(f"config line is not correct ! , {e}")

        if len(PortToLink) > 0 :
            for i in PortToLink:
                try :
                    link = int(i)
                    if link != self.id:
                        self.linkedPort.append(link)
                except :
                    pass
        try:
            self.Connect(self.StreamType)
        except Exception as e: 
            raise e
    
    def ConfigNTRIPStream(self,CommandConfig : str ):
        """
        Init a NTRIP Client with a configuration line

        Args:
            CommandConfig (str): configuration line
        """
        credentials = CommandConfig.split("@")[0].split(":")
        if len(credentials) != 2 :
            raise Exception("Missing a credential paremeter !")
        
        host = CommandConfig.split("@")[1].split(":")
        if len(host) != 2:
            raise Exception("Missing a host paremeter !")
        
        mountpoint = CommandConfig.split("@")[1].split("/")
        if len(mountpoint) != 2:
            raise Exception("Missing a MountPoint paremeter !")
        
        try : 
            self.ntripClient = NtripClient(host = host[0], port = int(host[1].split("/")[0]), auth= (True if len(credentials[0]) > 0 and len(credentials[1]) > 0  else False) ,username= credentials[0],password= credentials[1],mountpoint=mountpoint[1])
            self.StreamType = StreamType.NTRIP
        except Exception as e : 
            raise Exception(f"Error : given parameters for a NTRIP Client stream are incorrect : \n{e}")
        
    def ConfigUDPStream(self,specificHost : bool = False, commandConfig : str = None):
        """
            Init a UDP stream with a configuration line
        Args:
            specificHost (bool, optional): if True the UDP Stream will stream only to a specific host name. Defaults to False.
            commandConfig (str, optional): Configuration line. Defaults to None.

        Raises:
            Exception: too few or too much parameter
            Exception: Given parameter incorrect 
            Exception: Given parameter incorrect (Specific host)
        """
        if specificHost :
            config = commandConfig.split(":")[0]
            if len(config) != 2 : 
                raise Exception("Error : too few or too much parameter") 
            else :
                try:
                    self.udpSettings = UdpSettings(host=config[0],  port=int(config[1]), specificHost=specificHost)
                    self.StreamType = StreamType.UDP
                except Exception as e : 
                    raise Exception("Error : given parameter for a UDP stream are incorrect : \n{e}")
        else :
            try:
                self.udpSettings = UdpSettings(port=int(commandConfig))
                self.StreamType = StreamType.UDP
            except Exception as e : 
                raise Exception("Error : given parameter for a UDP stream are incorrect : \n{e}")      
        
    def ConfigTCPStream(self,isServer : bool = False ,commandConfig : str = None) -> None:
        """
            Init a TCP stream with a configuration line
        Args:
            isServer (bool, optional): If True the TCP stream will be configure as a Server. Defaults to False.
            commandConfig (str, optional): Configuration line . Defaults to None.

        Raises:
            Exception: too few or too much parameter
            Exception: Given parameter incorrect (Server)
            Exception: Given parameter incorrect (Client)
        """
        if isServer : 
            config = commandConfig.split(":")
            if len(config) != 2 : 
                raise Exception("Error : too few or too much parameter") 
            try : 
                self.tcpSettings = TcpSettings(host=config[0] , port=config[1], streamMode= StreamMode.SERVER)        
            except Exception as e : 
                raise Exception("Error : given parameters for a TCP Server stream are incorrect : \n{e}")   
        else : 
            try : 
                self.tcpSettings = TcpSettings(port=commandConfig , streamMode= StreamMode.CLIENT)
            except Exception as e : 
                raise Exception("Error : given parameters for a TCP Client stream are incorrect : \n{e}")   
        self.StreamType = StreamType.TCP
        
    def ConfigSerialStream(self,commandConfig :str) -> None:
        """
            Init a Serial stream with a configuration line
            exemple : 
        Args:
            commandConfig (str): Configuration line

        Raises:
            Exception: If too few argument for a proper configuration
            Exception: If given argument are Incorrect
        """
        config = commandConfig.split(":")
        if len(config) != 6 : 
            raise Exception("Error : too few or too much parameter") 
        port : str = config[0]
        try :
                baudrate : BaudRate = BaudRate(config[1])
        except : 
                baudrate : BaudRate = BaudRate.eBAUD115200
        try :    
                parity : Parity = Parity(config[2])
        except : 
                parity : Parity = Parity.PARITY_NONE
        try : 
                stopbits : StopBits = StopBits(config[3])
        except :
                stopbits : StopBits = StopBits.STOPBITS_ONE
        try :
                bytesize : ByteSize= ByteSize(config[4])
        except : 
                bytesize : ByteSize = ByteSize.EIGHTBITS
                 
        rtscts : bool = True if config[5] == "1" else False
        try :
            self.serialSettings = SerialSettings(Port= port , baudrate=baudrate , parity=parity , stopbits=stopbits,bytesize=bytesize , Rtscts=rtscts)
            self.StreamType = StreamType.Serial
        except Exception as e :
            raise Exception("Error : given parameters for a Serial stream are incorrect : \n{e}")   
    
    # .conf file Configuration Functions
    
    def ConfFileConfig(self,confFile : configparser.SectionProxy) :
        """
        Init a stream and it's settings with a configuration file 
        
        Args:
            confFile (configparser.SectionProxy): section of a stream in a configuration file
        """
        self.serialSettings: SerialSettings = ConfFileSerial(confFile)
        self.tcpSettings: TcpSettings = ConfFileTCP(confFile)
        
        self.udpSettings : UdpSettings = ConfFileUDP(confFile)
        self.ntripClient : NtripClient = ConfFileNTRIPClient(confFile)
        try :
            self.StreamType : StreamType = StreamType(int(confFile.get("connectionType")))
        except :
            self.StreamType : StreamType = StreamType.NONE
        links = confFile.get("linksChecked").replace("[","").replace(" ","").replace("]","").split(",")
        for link in links:
            if link != '':
                self.linkedPort.append(int(link))
        self.startupScript = confFile.get("startupscriptfile")        
        try : 
            self.sendStartupScript = True if confFile.get("startupscript").lower() == "true" else False
        except : 
            self.sendStartupScript = False
        self.closeScript = confFile.get("closescriptfile")        
        try : 
            self.sendCloseScript = True if confFile.get("closescript").lower() == "true" else False
        except : 
            self.sendCloseScript = False
        self.loggingFile = confFile.get("logfile")
        if self.loggingFile != "":
            self.logging = True

    # Private Methods 
    
    def _ExceptionDisconnect(self):
        """
        Disconnects the port if is connected in case of a exception caused in the task Thread
        """
        self.StopEvent.set()
        self.currentTask = None
        try :
            self.Stream.close()
        finally:
            self.connected = False  
            self.dataTransferInput = 0.0
            self.dataTransferOutput = 0.0
    
    def _clearQueue(self, queue : queue.Queue):
        """
        clear the queue passed as argument
        Args:
            queue (queue.Queue): queue to empty
        """
        while not queue.empty():
            queue.get() 
    
def ConfFileSerial(confFile :configparser.SectionProxy):
    """
    Init Serial settings of the current stream with value from a configuration file.
    If no value in configuration file , default value will be use

    Args:
        confFile (configparser.SectionProxy): configuration file 

    Returns:
        SerialSetting: return a new SerialSettings
    """
    port : str = confFile.get('Serial.Port')
    try :
        baudrate : BaudRate = BaudRate(confFile.get('Serial.BaudRate'))
    except : 
        baudrate : BaudRate = BaudRate.eBAUD115200
    try :    
        parity : Parity = Parity(confFile.get('Serial.Parity'))
    except : 
        parity : Parity = Parity.PARITY_NONE
    try : 
        stopbits : StopBits = StopBits(confFile.get('Serial.StopBits') ) 
    except :
        stopbits : StopBits = StopBits.STOPBITS_ONE
    try :
        bytesize : ByteSize= ByteSize(confFile.get('Serial.ByteSize')) 
    except : 
        bytesize : ByteSize = ByteSize.EIGHTBITS 
    try : 
        rtscts : bool = True if confFile.get('Serial.RtcCts').lower() == "true" else False
    except :
        rtscts = False
    return SerialSettings(Port= port , baudrate=baudrate , parity=parity , stopbits=stopbits,bytesize=bytesize , Rtscts=rtscts)

def ConfFileTCP(confFile : configparser.SectionProxy):
    """
    Init TCP settings of the current stream with value from a configuration file.
    If no value in configuration file , default value will be use

    Args:
        confFile (configparser.SectionProxy): configuration file 

    Returns:
        TcpSettings: return a new TcpSettings
    """        
    host : str = confFile.get('hostName')
    try : 
        port : int = int(confFile.get('portNumber'))
    except :
        port = 28784
        
    if bool(True if str(confFile.get('TCPserver')).lower() == "true" else False ) is True :
        host = ''
        streamMode : StreamMode = StreamMode.SERVER
    else:
        streamMode : StreamMode = StreamMode.CLIENT
            
    return TcpSettings(host= host , port= port ,streamMode=streamMode)
   
def ConfFileUDP(confFile : configparser.SectionProxy):
    """
    Init UDP settings of the current stream with value from a configuration file.
    If no value in configuration file , default value will be use

    Args:
        confFile (configparser.SectionProxy): configuration file 

    Returns:
        UdpSettings: return a new udpsettings
    """
    host : str = confFile.get('hostNameUDP')
    try : 
        port : int = int(confFile.get('portNumberUDP'))
    except : 
        port = 28784
    try: 
        dataFlow : DataFlow = DataFlow(confFile.get('dataDirUDP'))
    except :
        dataFlow : DataFlow = DataFlow.Both
    try  :
        specificHost : bool  = True if confFile.get('specificIpUDP').lower() == "true" else False
    except : 
        specificHost = False
    
    return UdpSettings(host=host,port=port , dataflow=dataFlow,specificHost=specificHost)
    
def ConfFileNTRIPClient(confFile : configparser.SectionProxy ):
    """
    Init a Ntrip client with value from a configuration file.
    If no value in configuration file , default value will be use

    Args:
        confFile (configparser.SectionProxy): configuration file 

    Returns:
        NtripClient: return a new ntrip
    """
    host : str = confFile.get('NTRIP.hostname')
    try :
        port : int = int(confFile.get('NTRIP.portnumber'))
    except:
        port = 2101
    mountpoint : str = confFile.get('NTRIP.mountPoint')
    try : 
        auth : bool = True if confFile.get('NTRIP.authenticationenabled').lower() == "true" else False
    except : 
        auth = False
    username : str = confFile.get('NTRIP.user')
    try : 
        password : str = base64.b64decode((confFile.get('NTRIP.password')).encode()).decode()
    except : 
        password : str = ""
    try : 
        tls : bool = True if confFile.get('NTRIP.TLS').lower() == "true" else False
    except : 
        tls = False
    try : 
        fixedPos : bool = True if confFile.get('NTRIP.fixedpositionset').lower() == "true" else False
    except : 
        fixedPos = False
                
    try :
        latitude : float = float(confFile.get('NTRIP.fixedlatitude'))
    except :
        latitude = 00.000000000
    try :
        longitude : float = float(confFile.get('NTRIP.fixedlongitude'))
    except :
        longitude = 000.000000000
    try : 
        height : int = int(confFile.get('NTRIP.fixedheight'))
    except :
        height = 0
    
        
    return NtripClient(host=host , port=port , auth=auth , username=username , password= password , mountpoint=mountpoint 
                        , tls= tls ,fixedPos=fixedPos , latitude = latitude , longitude = longitude , height = height)
