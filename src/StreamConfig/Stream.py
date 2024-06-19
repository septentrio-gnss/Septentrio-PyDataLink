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
from io import TextIOWrapper
import os
import socket
import base64
from  datetime import datetime
import time
from serial import Serial
import threading
import queue
import logging
from ..StreamSettings.UdpSettings import *
from ..StreamSettings.SerialSettings import *
from ..StreamSettings.TcpSettings import *
from ..NTRIP import *

from .Preferences import *
from ..constants import DEFAULTLOGFILELOGGER

class StreamType(Enum):
    Serial = 0
    TCP = 1
    UDP = 2
    NTRIP = 3
    NONE = None

class Stream:
    """
    Represents a port/stream for data streaming.
    
    """

    def __init__(self, id: int = 0, linkedData: list[queue.Queue] = None , debugLogging : bool  = False ): # type: ignore

        self.id = id
        self.linkedPort: list[int] = []
        self.connected: bool = False  
        self.currentTask = None
        self.StreamType: StreamType = StreamType.NONE
        self.Stream : Serial | socket.socket | NtripClient | None  = None
        self.lineTermination :str = "\r\n"
        self.dataTransferInput : float = 0.0
        self.dataTransferOutput :float = 0.0
        self.debugLogging : bool = debugLogging
        
        #Support Log File 
        if debugLogging :
            self.logFile : logging.Logger = DEFAULTLOGFILELOGGER
        else : 
            self.logFile  = None
        
        # logging file 
        self.logging : bool = False
        self.loggingFile : str = ""
        self.logger : TextIOWrapper  = None 
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
        
        # Init all Settings
        self.serialSettings = SerialSettings(debugLogging = debugLogging)
        self.tcpSettings = TcpSettings(debugLogging = debugLogging)
        self.udpSettings = UdpSettings(debugLogging = debugLogging)
        self.ntripClient = NtripClient(debugLogging = debugLogging)
            
        
    def Connect(self, Streamtype : StreamType = None):
        """
        Connects the port using the specified Stream type.

        Args:
            Streamtype: The type of Stream.

        Returns:
            int: 0 if the Stream fails, otherwise None.
        """
        if self.logFile is not None : 
            self.logFile.info("Connecting Stream %s " , self.id)
        if Streamtype is None : 
            Streamtype = self.StreamType
            if self.logFile is not None : 
                self.logFile.info("Stream %s : start new %s Stream" , self.id , Streamtype.name)
        if self.connected is  True:
            if self.logFile is not None : 
                self.logFile.error("Stream %s : Stream was already connected",self.id)
        else : 
            if Streamtype == StreamType.Serial:
                if self.serialSettings.port == "" or self.serialSettings is None:
                    if self.logFile is not None : 
                        self.logFile.error("Stream %s : Failed to open Serial stream : Serial port hasn't been configured yet" , self.id)
                    raise Exception("Connection Error","Serial port hasn't been configured yet")
                else:
                    try:
                        self.Stream = self.serialSettings.Connect()
                        self.connected = True
                        task = self.DatalinkSerialTask
                        if self.logFile is not None : 
                            self.logFile.info("Stream %s : Stream openned succesfully " , self.id)
                    except Exception as e:
                        if self.logFile is not None : 
                            self.logFile.error("Stream %s : Failed to connect to the serial port : %s" , self.id,e)
                        self.Stream = None
                        self.connected = False
                        raise e

            elif Streamtype == StreamType.TCP:
                if self.logFile is not None : 
                    self.logFile.debug("Stream %s : Create TCP %s with host : %s and port : %s" , self.id,self.StreamType.name,self.tcpSettings.host , self.tcpSettings.port)
                if self.tcpSettings is None:
                    if self.logFile is not None : 
                            self.logFile.error("Stream %s : Failed to open TCP stream : TCP settings not set " , self.id)
                    raise Exception("Connection Error","tcp settings are empty !")
                else:
                    try:
                        socket.gethostbyname(self.tcpSettings.host)
                        self.Stream = self.tcpSettings.connect()
                        self.connected = True
                        if self.tcpSettings.StreamMode == StreamMode.SERVER:
                            task = self.DatalinkTCPServerTask
                        else :
                            task = self.DatalinkTCPClientTask
                        if self.logFile is not None : 
                            self.logFile.info("Stream %s : Stream openned succesfully " , self.id)
                    except Exception as e :
                        self.Stream = None
                        self.connected = False
                        if self.logFile is not None : 
                            self.logFile.error("Stream %s : Failed to open TCP stream: %s" , self.id,e)
                        raise e
                
            elif Streamtype == StreamType.UDP:
                if self.udpSettings is  None:
                    if self.logFile is not None : 
                            self.logFile.error("Stream %s : Failed to open UDP stream : UDP settings not set " , self.id)
                    raise Exception("Connection Error","udp settings are empty!")
                else:
                    try:
                        socket.gethostbyname(self.tcpSettings.host)
                        self.Stream = self.udpSettings.connect()
                        task = self.DatalinkUDPTask
                        if self.logFile is not None : 
                            self.logFile.info("Stream %s : Stream openned succesfully " , self.id)
                    except Exception as e:
                        self.Stream = None
                        self.connected = False
                        if self.logFile is not None : 
                            self.logFile.error("Stream %s : Failed to open TCP stream: %s" , self.id,e)
                        raise e
                
            elif Streamtype == StreamType.NTRIP:
                    if self.ntripClient is  None:
                         raise Exception("Connection Error","ntrip client is not set !")
                    else:
                        try:
                            if len(self.ntripClient.ntripSettings.host.replace(" ","")) == 0 :
                                if self.logFile is not None : 
                                    self.logFile.error("Stream %s : Failed to open NTRIP stream : NTRIP Host Name not set " , self.id)
                                raise Exception("Connection Error","NTRIP host is not set !")
                            else:
                                socket.gethostbyname(self.ntripClient.ntripSettings.host)
                                self.ntripClient.connect()
                                self.Stream = self.ntripClient
                                self.connected = True
                                task = self.DatalinkNTRIPTask
                                if self.ntripClient.ntripSettings.fixedPos:
                                    self.ntripClient._createGgaString()
                                    
                                if self.logFile is not None : 
                                    self.logFile.info("Stream %s : Stream openned succesfully " , self.id)
                        except Exception as e:
                            self.Stream = None
                            self.connected = False 
                            if self.logFile is not None : 
                                self.logFile.error("Stream %s : Failed to open NTRIP stream: %s" , self.id,e)
                            raise e
                    
            else:
                if self.logFile is not None : 
                    self.logFile.error("Stream %s : Invalid Stream Type " , self.id)
                raise Exception("Connection Error","Invalid Stream type!")
            if self.connected is True:
                try:
                    if self.logFile is not None : 
                        self.logFile.debug("Stream %s : start final configuration " , self.id)
                    self.StopEvent.clear()
                    if self.logging :
                        self.logger = open(self.loggingFile,"w")
                        if self.logFile is not None : 
                            self.logFile.debug("Stream %s : init loggin file :  %s" , self.id,self.loggingFile)
                    if self.sendStartupScript:
                        if self.logFile is not None : 
                            self.logFile.debug("Stream %s : init startup script file :  %s" , self.id,self.startupScript)
                        self._clearQueue(self.linkedData[self.id])
                        self.sendScript(self.linkedData[self.id], True)
                    self.dataLinkStreamThread = threading.Thread(target=task)
                    if self.logFile is not None : 
                            self.logFile.debug("Stream %s : Starting Thread " , self.id)
                    self.dataLinkStreamThread.start()  
                    self.currentTask = task
                    if len(self.linkedPort) != 0:  
                        if self.logFile is not None :
                            self.logFile.error("Stream %s : update linked Port : %s" , self.id ,str(self.linkedPort) )  
                        for link in self.linkedPort:  
                            self.updateLinkedPort.put(link)
                    if self.logFile is not None :
                        self.logFile.info("Stream %s : final configuration finished " , self.id  )
                except Exception as e:
                    if self.logFile is not None :
                        self.logFile.error("Stream %s : Failed during final configuration : %s" , self.id ,e )
                    self.connected = False
                    raise e

    def Disconnect(self):
        """
        Disconnects the port if is connected.
        """
        if self.Stream is not None:
            if self.logFile is not None : 
                self.logFile.info("Stream %s : Disconnecting stream",self.id)
            try:
                if self.sendCloseScript:
                    self.sendScript(self.linkedData[self.id], False)
                self.StopEvent.set()
                self.currentTask = None
                self.dataLinkStreamThread.join()
                if self.logFile is not None : 
                    self.logFile.debug("Stream %s : wait for Thread to stop",self.id)
                self.Stream.close()
                self.connected = False
                self.dataTransferInput = 0.0
                self.dataTransferOutput = 0.0
                if self.logFile is not None : 
                    self.logFile.info("Stream %s : Disconnected",self.id)
            except Exception as e:
                if self.logFile is not None : 
                    self.logFile.error("Stream %s : Failed to disconnect stream : %s",self.id,e)
                raise e
      
    def UpdatelinkedPort(self, link : int):
        """
        Updates the linked port with the specified link.

        Args:
            link: The link to update.

        """
        if link in self.linkedPort:
            if self.logFile is not None : 
                    self.logFile.info("Stream %s : remove link : %s",self.id,link)
            self.linkedPort.remove(link)
        else:
            if self.logFile is not None : 
                    self.logFile.info("Stream %s : add link : %s",self.id,link)
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
                if self.logFile is not None : 
                    self.logFile.info("Stream %s : send Startup script command",self.id)
                if self.startupScript != "":
                    if self.logFile is not None : 
                        self.logFile.debug("Stream %s : open Startup script file",self.id)
                    OpenScript = open(self.startupScript,"r")
                    if OpenScript is not None:
                        if self.logFile is not None : 
                            self.logFile.debug("Stream %s : file not empty , send command to thread",self.id)
                        for line in OpenScript:
                            queue.put(line)
            else :
                if self.logFile is not None : 
                    self.logFile.info("Stream %s : send closeup script command",self.id)
                if self.closeScript != "":
                    if self.logFile is not None : 
                        self.logFile.debug("Stream %s : open closeup script file",self.id)
                    OpenScript = open(self.closeScript,"r")
                    if OpenScript is not None:
                        if self.logFile is not None : 
                            self.logFile.debug("Stream %s : file not empty , send command to thread",self.id)
                        for line in OpenScript:
                            queue.put(line)
                
        except Exception as e:
            if self.logFile is not None : 
                    self.logFile.error("Stream %s : failed to send script command to thread : %s",self.id,e)
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
            if self.logFile is not None : 
                self.logFile.error("Stream %s : Closeup file not found : %s",self.id,newpath)
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
            if self.logFile is not None : 
                self.logFile.error("Stream %s : Startup file not found : %s",self.id,newpath)
            raise Exception("File not found !")
        
    def setLoggingFileName(self,newFileName : str):
        """
        Set the logging file name use when logging is True

        Args:
            newFileName (str): the new file name of the logging file
        """
        if os.path.exists(newFileName):
            self.loggingFile = newFileName
        else : 
            if self.logFile is not None : 
                self.logFile.error("Stream %s : Logging file Path not found : %s",self.id,newFileName)
            raise Exception("Path not found !")
            
        
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
    
    
    def _clearQueue(self, queue : queue.Queue):
        """
        clear the queue passed as argument
        Args:
            queue (queue.Queue): queue to empty
        """
        while not queue.empty():
            queue.get() 
            
    def _ExceptionDisconnect(self):
        """
        Disconnects the port if is connected in case of a exception caused in the task Thread
        """
        self.StopEvent.set()
        self.currentTask = None
        try :
            if self.Stream is not None:
                self.Stream.close()
        finally:
            self.connected = False  
            self.dataTransferInput = 0.0
            self.dataTransferOutput = 0.0
            
        
    def DatalinkSerialTask(self):
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
        tempInputTranfert = 0
        tempOutputTransfert = 0
        # Send startup command
        if self.logFile is not None :
            self.logFile.info(f"Stream {self.id} : Task Started " )
            self.logFile.info(f"Stream {self.id} : sending startup script" )
        try:
            if not self.linkedData[self.id].empty():
                Task_SendCommand(self.linkedData[self.id],self.Stream,logger=self.logger,lineTermination=self.lineTermination)
        except Exception as e :
            if self.logFile is not None :
                    self.logFile.error(f"Stream {self.id} :  Start script couldn't finish : {e} " )
            self._ExceptionDisconnect()
            raise Exception(f"Error : Start script couldn't finish {e}")
        currentTime = datetime.now()
        #Main loop
        if self.logFile is not None :
            self.logFile.info(f"Stream {self.id} : sending startup script finished  " )
            self.logFile.info(f"Stream {self.id} : start main loop" )
        while self.StopEvent.is_set() is not True:
            tempInputTranfert ,tempOutputTransfert, currentTime =  Task_DataTransferRate(self , currentTime , tempInputTranfert , tempOutputTransfert)
            try:
                if self.Stream is Serial:
                    if self.Stream.is_open:
                        inputData = self.Stream.readline().decode(encoding='ISO-8859-1')
                        
                        tempInputTranfert += len(inputData)
                        # Print data if show data input 
                        Task_ShowData(self , inputData) 
                        # Send input data to linked Streams
                        Task_ShareData(LinkedPort , self.linkedData , inputData )
                        
                        if not self.linkedData[self.id].empty():
                            returnedValue = Task_SendCommand(self.linkedData[self.id],self.Stream,self.ShowOutputData.is_set(), DataToShow=self.DataToShow,logger=self.logger,lineTermination=self.lineTermination )
                            if returnedValue is not None : 
                                tempOutputTransfert += returnedValue
            except Exception as e:
                self._ExceptionDisconnect()
                if self.logFile is not None :
                    self.logFile.error(f"Stream {self.id} {self.StreamType} has been disconnected, error: {e}")
                raise Exception(f"Stream {self.id} {self.StreamType} has been disconnected, error: {e}")
            #Update current linked Streams list
            if not self.updateLinkedPort.empty():
                Task_UpdateLinkedPort(self.updateLinkedPort , LinkedPort)
        #Send closeup commands
        if self.logFile is not None :
            self.logFile.info(f"Stream {self.id} : main loop ended " )
            self.logFile.info(f"Stream {self.id} : sending closing script" )
        try : 
            if not self.linkedData[self.id].empty():
                Task_SendCommand(self.linkedData[self.id],self.Stream,logger=self.logger,lineTermination=self.lineTermination)
        except Exception as e :
            if self.logFile is not None :
                    self.logFile.error(f"Stream {self.id} :  closing script couldn't finish : {e} " )
            raise Exception("Error : closing script couldn't finish " + e)
        return 0

    def DatalinkTCPServerTask(self):
        """
        The task for data link Stream using TCP communication.

        """
        if self.Stream is not socket.socket :
            return self._ExceptionDisconnect()
            
        LinkedPort: list[int] = []
        self.Stream.settimeout(0.1)
        self.Stream.setblocking(0)
        tempInputTranfert = 0
        tempOutputTransfert = 0
        # Wait for a client to connect to the server
        if self.logFile is not None :
            self.logFile.info(f"Stream {self.id} : Task Started " )
            self.logFile.info(f"Stream {self.id} : waiting for client to connect " )
        while True:
                try:
                    self.Stream.listen()
                    conn, address = self.Stream.accept()
                    conn.settimeout(0.1)
                    break
                except Exception as e :
                    if self.StopEvent.is_set():
                        return 0
        # Send startup command
        if self.logFile is not None :
            self.logFile.info(f"Stream {self.id} : sending startup script" )
        try:
            if not self.linkedData[self.id].empty():
                Task_SendCommand(self.linkedData[self.id],conn,logger=self.logger,lineTermination=self.lineTermination)
        except Exception as e :
            if self.logFile is not None :
                    self.logFile.error(f"Stream {self.id} :  Start script couldn't finish : {e} " )
            self._ExceptionDisconnect()
            raise Exception(f"Error : Start script couldn't finish {e}")
        currentTime = datetime.now()
        #Main loop
        if self.logFile is not None :
            self.logFile.info(f"Stream {self.id} : sending startup script finished  " )
            self.logFile.info(f"Stream {self.id} : start main loop" )
        while self.StopEvent.is_set() is not True:
            tempInputTranfert ,tempOutputTransfert, currentTime =  Task_DataTransferRate(self , currentTime , tempInputTranfert , tempOutputTransfert)
            try:
                #If a client is connected
                if conn is not socket.socket:
                    #Read input data 
                    try:
                        inputData = conn.recv(4096).decode(encoding='ISO-8859-1')
                        tempInputTranfert += len(inputData)
                        if len(inputData) == 0:
                            conn = None
                    except socket.timeout:
                        inputData = ""
                    # Print data if show data input 
                    Task_ShowData(self , inputData) 
                    # Send input data to linked Streams
                    Task_ShareData(LinkedPort , self.linkedData , inputData )
                            
                    #Send output data comming from other streams and print data if showdata is set
                    if not self.linkedData[self.id].empty():
                        returnedValue = Task_SendCommand(self.linkedData[self.id] , conn , self.ShowOutputData.is_set(), DataToShow=self.DataToShow,logger=self.logger,lineTermination=self.lineTermination)
                        if returnedValue is not None : 
                                tempOutputTransfert += returnedValue
                else : 
                    time.sleep(1)
                    #Wait for a new Client if the current one has disconnect
                    if self.logFile is not None :
                                self.logFile.info(f"Stream {self.id} : Client disconnected  {e}")
                    while True:
                        try:
                            self.Stream.listen()
                            conn, address = self.Stream.accept()
                            conn.settimeout(0.1)
                            if self.logFile is not None :
                                self.logFile.info(f"Stream {self.id} : new Client Connected  {e}")
                            break
                        except Exception as e:
                            if self.StopEvent.is_set():
                                print("end")
                                return 0
            except Exception as e:
                self._ExceptionDisconnect()
                if self.logFile is not None :
                    self.logFile.error(f"Stream {self.id} {self.StreamType} has been disconnected, error: {e}")
                raise Exception(f"Stream {self.id} {self.StreamType} has been disconnected, error: {e}")
            #Update current linked Streams list
            if not self.updateLinkedPort.empty():
                LinkedPort = Task_UpdateLinkedPort(self.updateLinkedPort , LinkedPort)
        #Send closeup commands
        if self.logFile is not None :
            self.logFile.info(f"Stream {self.id} : main loop ended " )
            self.logFile.info(f"Stream {self.id} : sending closing script" )
        try : 
            if not self.linkedData[self.id].empty():
                Task_SendCommand(self.linkedData[self.id],conn,logger=self.logger,lineTermination=self.lineTermination)
        except Exception as e :
            if self.logFile is not None :
                    self.logFile.error(f"Stream {self.id} :  closing script couldn't finish : {e} " )
            raise Exception("Error : closing script couldn't finish " + e)
        return 0

    def DatalinkTCPClientTask(self):
        """
        The task for data link Stream using TCP communication.

        """
        if self.Stream is not socket.socket :
            self._ExceptionDisconnect()
            return 0 
        LinkedPort: list[int] = []
        self.Stream.settimeout(0.1)
        conn = 1
        tempInputTranfert = 0
        tempOutputTransfert = 0
        #Send startup command
        if self.logFile is not None :
            self.logFile.info(f"Stream {self.id} : Task Started " )
            self.logFile.info(f"Stream {self.id} : sending startup script" )
        try:
            if not self.linkedData[self.id].empty():
                Task_SendCommand(self.linkedData[self.id],self.Stream,logger=self.logger,lineTermination=self.lineTermination)
        except Exception as e :
            if self.logFile is not None :
                    self.logFile.error(f"Stream {self.id} :  Start script couldn't finish : {e} " )
            self._ExceptionDisconnect()
            raise Exception("Error : Start script couldn't finish " + e)
        currentTime = datetime.datetime.now()
        #Main loop
        if self.logFile is not None :
            self.logFile.info(f"Stream {self.id} : sending startup script finished  " )
            self.logFile.info(f"Stream {self.id} : start main loop" )
        while self.StopEvent.is_set() is not True:
            tempInputTranfert ,tempOutputTransfert,currentTime =  Task_DataTransferRate(self , currentTime , tempInputTranfert , tempOutputTransfert)          
            try:
                #While Connection still up 
                if conn  is not None :
                    #Read input data 
                    try:
                        inputData = self.Stream.recv(4096).decode(encoding='ISO-8859-1')
                        tempInputTranfert += len(inputData)
                        if len(inputData) == 0:
                            conn = None
                    except socket.timeout:
                        inputData = ""
                    except ConnectionResetError : 
                        conn = None
                    except BrokenPipeError : 
                        conn = None
                        
                    # Print data if show data input 
                    Task_ShowData(self , inputData) 
                    # Send input data to linked Streams
                    Task_ShareData(LinkedPort , self.linkedData , inputData )
                    # Output data comming from other streams
                    if not self.linkedData[self.id].empty():
                        returnedValue = Task_SendCommand(self.linkedData[self.id],self.Stream,self.ShowOutputData.is_set(),DataToShow=self.DataToShow,logger=self.logger,lineTermination=self.lineTermination)
                        if returnedValue is not None :
                            tempOutputTransfert += returnedValue
                
                else : 
                    # If connection Lost try to reconnect to the server 
                    while True:
                        try:
                            self.Stream = self.tcpSettings.connect()
                            conn = 1
                            break
                        except Exception as e:
                            if self.StopEvent.is_set():
                                return 0
                            
            #If there is any probleme , disconnect everything and kill thread 
            except Exception as e:
                self._ExceptionDisconnect()
                if self.logFile is not None :
                    self.logFile.error(f"Stream {self.id} {self.StreamType} has been disconnected, error: {e}")
                raise Exception(f"Stream {self.id} {self.StreamType} has been disconnected, error: {e}")
            
            # Update Current linked Stream list
            if not self.updateLinkedPort.empty():
                Task_UpdateLinkedPort(self.updateLinkedPort,LinkedPort)
        # Send Closeup command
        if self.logFile is not None :
            self.logFile.info(f"Stream {self.id} : main loop ended " )
            self.logFile.info(f"Stream {self.id} : sending closing script" )
        try : 
            Task_SendCommand(self.linkedData[self.id],self.Stream,logger=self.logger,lineTermination=self.lineTermination)
        except Exception as e :
            if self.logFile is not None :
                    self.logFile.error(f"Stream {self.id} :  closing script couldn't finish : {e} " )
            raise Exception("Error : closing script couldn't finish " + e)
        return 0
                    
    def DatalinkUDPTask(self):
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
        if self.logFile is not None :
            self.logFile.info(f"Stream {self.id} : Task Started " )
            self.logFile.info(f"Stream {self.id} : sending startup script" )
        try:
            if not self.linkedData[self.id].empty():
                if sendaddress is not None:
                    Task_SendCommand(self.linkedData[self.id] , stream=self.Stream , udpsendaddress=sendaddress[0],logger = self.logger,lineTermination = self.lineTermination)
        except Exception as e :
            if self.logFile is not None :
                    self.logFile.error(f"Stream {self.id} :  Start script couldn't finish : {e} " )
            self._ExceptionDisconnect()
            raise Exception("Error : Start script couldn't finish {e}")
        currentTime = datetime.now()
        #Main loop
        if self.logFile is not None :
            self.logFile.info(f"Stream {self.id} : sending startup script finished  " )
            self.logFile.info(f"Stream {self.id} : start main loop" )
        while self.StopEvent.is_set() is not True:
            tempInputTranfert ,tempOutputTransfert,currentTime =  Task_DataTransferRate(self , currentTime , tempInputTranfert , tempOutputTransfert)
            try:
                #Continue is Stream is still up
                if self.Stream is socket.socket:
                    if self.udpSettings.DataFlow in (1, 2):
                        bytesAddressPair = self.Stream.recvfrom(4096)
                        inputData = bytesAddressPair[0].decode(encoding='ISO-8859-1')
                        tempInputTranfert += len(inputData)
                        
                        # Print data if show data input 
                        Task_ShowData(self , inputData) 
                        # Send input data to linked Streams
                        Task_ShareData(LinkedPort , self.linkedData , inputData )

                    if self.udpSettings.DataFlow in (0, 2):
                        if not self.linkedData[self.id].empty():
                            if sendaddress is not None:
                                returnedValue = Task_SendCommand(self.linkedData[self.id] , self.Stream , self.ShowOutputData.is_set() , sendaddress[0], self.DataToShow,logger=self.logger,lineTermination=self.lineTermination)
                                if returnedValue is not None :
                                    tempOutputTransfert += returnedValue
            
            except Exception as e:
                self._ExceptionDisconnect()
                if self.logFile is not None :
                    self.logFile.error(f"Stream {self.id} {self.StreamType} has been disconnected, error: {e}")
                raise Exception(f"Stream {self.id} {self.StreamType.name} has been disconnected, error: {e}")
            #Update linked Streams list
            if not self.updateLinkedPort.empty():
                Task_UpdateLinkedPort(self.updateLinkedPort,LinkedPort)
        #Send closeup Commands
        if self.logFile is not None :
            self.logFile.info(f"Stream {self.id} : main loop ended " )
            self.logFile.info(f"Stream {self.id} : sending closing script" )
        try : 
            if not self.linkedData[self.id].empty():
                if sendaddress is not None:
                    Task_SendCommand(self.linkedData[self.id] ,stream= self.Stream  , udpsendaddress=sendaddress[0],logger=self.logger,lineTermination=self.lineTermination)
        except Exception as e :
            if self.logFile is not None :
                    self.logFile.error(f"Stream {self.id} :  closing script couldn't finish : {e} " )
            raise Exception("Error : closing script couldn't finish " + e)
        return 0

    def DatalinkNTRIPTask(self):
        """
        Process the NTRIP data received from the NTRIP client and send correction to other the linked streams .

        Args:
            ntrip (NtripClient): The NTRIP client object.
            linkedData (list[queue.Queue]): list of queues for sending or reading data to/from other streams .
            updateLinkedPort (queue.Queue): The queue for updating the linked ports.
        """
        LinkedPort: list[int] = []
        self.Stream.socket.settimeout(0.1)
        tempInputTranfert = 0
        tempOutputTransfert = 0
        # Send startup command
        if self.logFile is not None :
            self.logFile.info(f"Stream {self.id} : Task Started " )
            self.logFile.info(f"Stream {self.id} : sending startup script" )
        try:
            if self.ntripClient.ntripSettings.fixedPos :
                self.linkedData[self.id].put(self.ntripClient.fixedPosGga)
            if not self.linkedData[self.id].empty():
                Task_SendCommand(self.linkedData[self.id],self.Stream ,logger=self.logger,lineTermination=self.lineTermination)
        except Exception as e :
            if self.logFile is not None :
                    self.logFile.error(f"Stream {self.id} :  Start script couldn't finish : {e} " )
            self._ExceptionDisconnect()
            raise Exception(f"Error : Start script couldn't finish {e}")         
        currentTime = datetime.now()
        #Main loop
        if self.logFile is not None :
            self.logFile.info(f"Stream {self.id} : sending startup script finished  " )
            self.logFile.info(f"Stream {self.id} : start main loop" )
        while self.StopEvent.is_set() is not True:
            tempInputTranfert ,tempOutputTransfert,currentTime =  Task_DataTransferRate(self , currentTime , tempInputTranfert , tempOutputTransfert) 
            try:
                if self.Stream is not None:
                    #Read input data 
                    try:
                        inputData = self.Stream.socket.recv(4096).decode(encoding='ISO-8859-1')
                        tempInputTranfert += len(inputData)
                    except socket.timeout:
                        inputData = ""
                    # Print data if show data input 
                    Task_ShowData(self , inputData) 
                    # Send input data to linked Streams
                    Task_ShareData(LinkedPort , self.linkedData , inputData )
                    #Send output data comming from other streams and print data if showdata is set
                    if not self.linkedData[self.id].empty():
                        returnedValue= Task_SendCommand(self.linkedData[self.id],self.Stream ,self.ShowOutputData.is_set(),DataToShow=self.DataToShow,logger=self.logger,lineTermination=self.lineTermination)
                        if returnedValue is not None :
                            tempOutputTransfert += returnedValue 
            except Exception as e:
                self._ExceptionDisconnect()
                raise Exception(f"Stream {self.id} {self.StreamType} has been disconnected, error: {e}")
            
            #Update current linked Streams list
            if not self.updateLinkedPort.empty():
                Task_UpdateLinkedPort(self.updateLinkedPort,LinkedPort)
        if self.logFile is not None :
            self.logFile.info(f"Stream {self.id} : main loop ended " )
            self.logFile.info(f"Stream {self.id} : sending closing script" )
        #Send closeup commands
        try : 
            if not self.linkedData[self.id].empty():
                Task_SendCommand(self.linkedData[self.id],self.Stream,logger=self.logger,lineTermination=self.lineTermination)
        except Exception as e :
            if self.logFile is not None :
                    self.logFile.error(f"Stream {self.id} :  closing script couldn't finish : {e} " )
            raise Exception("Error : closing script couldn't finish " + e) 
        return 0
  
#####################################################################################
# STREAM TASK
#####################################################################################

def Task_UpdateLinkedPort(updateLinkedPort : queue.Queue , LinkedPort : list[int] ):
        for _ in range(updateLinkedPort.qsize()):
                    port = updateLinkedPort.get()
                    if port in LinkedPort:
                        LinkedPort.remove(port)
                    else:
                        LinkedPort.append(port)
        return LinkedPort
    
def Task_SendCommand(linkedData : queue.Queue , stream , ShowData : bool = False , udpsendaddress : str = None 
                     , DataToShow : queue.Queue = None , logger : TextIOWrapper = None , lineTermination : str = "\r\n"):
    try : 
        for _ in range(linkedData.qsize()):
            outputData : str = linkedData.get()
            if type(stream) == Serial :
                stream.write((outputData+"\n").encode(encoding='ISO-8859-1'))
            elif type(Stream) == socket.socket and udpsendaddress is None: 
                stream.sendall((outputData + lineTermination).encode(encoding='ISO-8859-1'))
            elif type(Stream) == socket.socket:
                stream.sendto((outputData + lineTermination).encode(encoding='ISO-8859-1'), udpsendaddress)
            elif type(Stream) == NtripClient :
                if "GPGGA" in outputData:
                    stream.sendNMEA(outputData)             
            else : continue
            if ShowData and len(outputData) != 0 : 
                DataToShow.put(outputData)
                if logger is not None:
                    logger.write(outputData)
            return len(outputData)
    except Exception as e :
        raise e


def Task_ShareData(LinkedPort : list[int] , linkedData : list[queue.Queue] , inputData ) :
    """
    LinkedPort : list of linked port id 
    linkedData : list of stream queue
    inputData : Data to share 
    """
    if LinkedPort is not None and len(inputData) != 0:
                    for portid in LinkedPort:
                        portQueue: queue.Queue = linkedData[portid]
                        portQueue.put(inputData)
                        
def Task_ShowData(stream :Stream , inputData) : 
    if stream.ShowInputData.is_set() and len(inputData) != 0:
        stream.DataToShow.put(inputData)
        if stream.logging:
            stream.logger.write(inputData)
            
def Task_DataTransferRate(stream :Stream , currentTime  , tempInputTranfert , tempOutputTransfert) :
    now = datetime.now()
    if (now-currentTime).total_seconds() >=  1 : 
        currentTime = now 
        stream.dataTransferInput = round(tempInputTranfert/1000,1)
        stream.dataTransferOutput = round(tempOutputTransfert/1000,1)
        return 0 , 0 , currentTime
    else : 
        return tempInputTranfert , tempOutputTransfert ,currentTime

    



def _ExceptionDisconnect(stream):
    """
    Disconnects the port if is connected in case of a exception caused in the task Thread
    """
    stream.StopEvent.set()
    stream.currentTask = None
    try :
        stream.Stream.close()
    finally:
        stream.connected = False  
        stream.dataTransferInput = 0.0
        stream.dataTransferOutput = 0.0

    