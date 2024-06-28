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
import threading
import queue
import logging
from  datetime import datetime
import time
from serial import Serial, SerialException

from ..NTRIP.NtripSettings import NtripSettingsException
from ..StreamSettings.UdpSettings import UDPSettingsException, UdpSettings
from ..StreamSettings.SerialSettings import SerialSettings, SerialSettingsException
from ..StreamSettings.TcpSettings import StreamMode, TCPSettingsException , TcpSettings
from ..NTRIP.NtripClient import NtripClient , NtripClientError
from ..constants import DEFAULTLOGFILELOGGER

class StreamException(Exception):
    """
        Exception class for Stream class 
    """
    def __init__(self, message, error_code = None):
        super().__init__(message)
        self.error_code = error_code
class MissingSettingsException(StreamException):
    """Raised when the settings used to conect a stream is missing
    """
class OpenConnectionError(StreamException):
    """Raised when openning connection failed
    """
class InvalidStreamTypeException(StreamException):
    """Raised when the given stream type is not supported
    """
class DisconnectError(StreamException):
    """Raised when the disconnection failed
    """
class ScriptFileException(StreamException):
    """Raised when a issue occur with a script file
    """
class LogFileException(StreamException):
    """Raised when a issue occur with the log file"""
class TaskException(StreamException):
    """Raised when a issue occur in a Task function
    """
class StreamThreadException(StreamException):
    """Raised when a issue occur with the stream thread
    """
    
class StreamType(Enum):
    """Possible communication type
    """
    Serial = 0
    TCP = 1
    UDP = 2
    NTRIP = 3
    NONE = None

class Stream:
    """
    Represents a port/stream for data streaming.
    
    """

    def __init__(self, stream_id : int = 0, linked_data: list[queue.Queue] = None ,
                 debug_logging : bool  = False ):

        self.stream_id = stream_id
        self.linked_ports: list[int] = []
        self.connected: bool = False
        self.current_task = None
        self.stream_type: StreamType = StreamType.NONE
        self.stream : Serial | socket.socket | NtripClient | None  = None
        self.line_termination :str = "\r\n"
        self.data_transfer_input : float = 0.0
        self.data_transfer_output :float = 0.0
        self.debug_logging : bool = debug_logging
        self.startup_error =""
        #Support Log File

        if debug_logging :
            self.log_file : logging.Logger = DEFAULTLOGFILELOGGER
        else :
            self.log_file  = None

        # logging file

        self.logging : bool = False
        self.logging_file : str = ""
        self.logger : TextIOWrapper  = None

        # Startup and close script

        self.startup_script : str = ""
        self.close_script : str = ""
        self.send_startup_script : bool = False
        self.send_close_script : bool = False

        # Event for data visibility and stop

        self.show_incoming_data = threading.Event()
        self.show_outgoing_data = threading.Event()
        self.stop_event = threading.Event()

        # Queue for data link between ports

        self.linked_data = linked_data
        self.update_linked_ports_queue: queue.Queue = queue.Queue()
        self.data_to_show: queue.Queue = queue.Queue()

        # Thread for data read/link

        self.datalink_stream_thread: threading.Thread = None

        # Init all Settings
        self.serial_settings = SerialSettings(debug_logging = debug_logging)
        self.tcp_settings = TcpSettings(debug_logging = debug_logging)
        self.udp_settings = UdpSettings(debug_logging = debug_logging)
        self.ntrip_client = NtripClient()

    def connect(self, stream_type : StreamType = None):
        """
        Connects the port using the specified Stream type.

        Args:
            stream_type: The type of Stream.

        Returns:
            int: 0 if the Stream fails, otherwise None.
        """
        if self.log_file is not None :
            self.log_file.info("Connecting Stream %s " , self.stream_id)
        if stream_type is None :
            stream_type = self.stream_type
            if self.log_file is not None :
                self.log_file.info("Stream %s : start new %s Stream" , self.stream_id , stream_type.name)
        if self.connected is  True:
            if self.log_file is not None :
                self.log_file.error("Stream %s : Stream was already connected",self.stream_id)
        else :
            if stream_type == StreamType.Serial:
                if self.serial_settings.port == "" or self.serial_settings is None:
                    if self.log_file is not None :
                        self.log_file.error("Stream %s : Failed to open Serial stream : Serial port hasn't been configured yet" , self.stream_id)
                    raise MissingSettingsException("Serial settings hasn't been given yet")
                else:
                    try:
                        self.stream = self.serial_settings.connect()
                        self.connected = True
                        task = self.datalink_serial_task
                        if self.log_file is not None :
                            self.log_file.info("Stream %s : Stream openned successfully " , self.stream_id)
                    except SerialSettingsException as e:
                        if self.log_file is not None :
                            self.log_file.error("Stream %s : Failed to connect to the serial port : %s" , self.stream_id,e)
                        self.stream = None
                        self.connected = False
                        raise OpenConnectionError(e) from e

            elif stream_type == StreamType.TCP:
                if self.log_file is not None :
                    self.log_file.debug("Stream %s : Create TCP %s with host : %s and port : %s" , self.stream_id,self.stream_type.name,self.tcp_settings.host , self.tcp_settings.port)
                if self.tcp_settings is None:
                    if self.log_file is not None :
                            self.log_file.error("Stream %s : Failed to open TCP stream : TCP settings not set " , self.stream_id)
                    raise MissingSettingsException("tcp settings are empty !")
                else:
                    try:
                        socket.gethostbyname(self.tcp_settings.host)
                        self.stream = self.tcp_settings.connect()
                        self.connected = True
                        if self.tcp_settings.stream_mode == StreamMode.SERVER:
                            task = self.datalink_tcp_server_task
                        else :
                            task = self.datalink_tcp_client_task
                        if self.log_file is not None :
                            self.log_file.info("Stream %s : Stream openned successfully " , self.stream_id)
                    except TCPSettingsException as e :
                        self.stream = None
                        self.connected = False
                        if self.log_file is not None :
                            self.log_file.error("Stream %s : Failed to open TCP stream: %s",self.stream_id,e)
                        raise OpenConnectionError(e) from e

            elif stream_type == StreamType.UDP:
                if self.udp_settings is  None:
                    if self.log_file is not None :
                        self.log_file.error("Stream %s : Failed to open UDP stream : UDP settings not set ", self.stream_id)
                    raise MissingSettingsException("udp settings are empty!")
                else:
                    try:
                        self.connected = True
                        socket.gethostbyname(self.tcp_settings.host)
                        self.stream = self.udp_settings.connect()
                        task = self.datalink_udp_task
                        if self.log_file is not None :
                            self.log_file.info("Stream %s : Stream openned successfully " , self.stream_id)
                    except UDPSettingsException as e:
                        self.stream = None
                        self.connected = False
                        if self.log_file is not None :
                            self.log_file.error("Stream %s : Failed to open TCP stream: %s" , self.stream_id,e)
                        raise OpenConnectionError(e) from e

            elif stream_type == StreamType.NTRIP:
                if self.ntrip_client is None or len(self.ntrip_client.ntrip_settings.host.replace(" ","")) == 0 :
                    if self.log_file is not None :
                        self.log_file.error("Stream %s : Failed to open NTRIP stream : Incorect Settings " , self.stream_id)
                    raise MissingSettingsException("ntrip client is not set !")
                else:
                    try:
                        socket.gethostbyname(self.ntrip_client.ntrip_settings.host)
                        self.ntrip_client.connect()
                        self.stream = self.ntrip_client
                        self.connected = True
                        task = self.datalink_ntrip_task
                        if self.ntrip_client.ntrip_settings.fixed_pos:
                            self.ntrip_client.create_gga_string()

                        if self.log_file is not None :
                            self.log_file.info("Stream %s : Stream openned successfully " , self.stream_id)
                    except (NtripClientError,NtripSettingsException) as e:
                        self.stream = None
                        self.connected = False
                        if self.log_file is not None :
                            self.log_file.error("Stream %s : Failed to open NTRIP stream: %s" , self.stream_id,e)
                        raise OpenConnectionError(f"Failed to open NTRIP Stream : {e}") from e
            elif stream_type == StreamType.NONE :
                if self.log_file is not None :
                    self.log_file.error("Stream %s : no configuration yet " , self.stream_id)
                    raise InvalidStreamTypeException(" No configuration selected ")
            else:
                if self.log_file is not None :
                    self.log_file.error("Stream %s : Invalid Stream Type " , self.stream_id)
                raise InvalidStreamTypeException(f" {stream_type.name} is not a valid Stream type !")
            if self.connected is True:
                try:
                    if self.log_file is not None :
                        self.log_file.debug("Stream %s : start final configuration " , self.stream_id)

                    self.stop_event.clear()
                    self._clear_queue(self.linked_data[self.stream_id])
                    if self.logging :
                        self.logger = open(self.logging_file,"w",encoding="utf-8")

                        if self.log_file is not None :
                            self.log_file.debug("Stream %s : init loggin file :  %s" , self.stream_id,self.logging_file)

                    if self.send_startup_script:

                        if self.log_file is not None :
                            self.log_file.debug("Stream %s : init startup script file :  %s" , self.stream_id,self.startup_script)

                        self.send_script(self.linked_data[self.stream_id], True)
                    self.datalink_stream_thread = threading.Thread(target=task,args=(self.stream, self.linked_data, self.update_linked_ports_queue,self.data_to_show , self.logger))

                    if self.log_file is not None :
                        self.log_file.debug("Stream %s : Starting Thread " , self.stream_id)

                    self.datalink_stream_thread.start()
                    self.current_task = task

                    if len(self.linked_ports) != 0:
                        
                        if self.log_file is not None :
                            self.log_file.info("Stream %s : update linked Port : %s" , self.stream_id ,str(self.linked_ports) )  

                        for link in self.linked_ports:
                            self.update_linked_ports_queue.put(link)

                    if self.log_file is not None :
                        self.log_file.info("Stream %s : final configuration finished " , self.stream_id  )

                except Exception as e:
                    if self.log_file is not None :
                        self.log_file.error("Stream %s : Failed during final configuration : %s" , self.stream_id ,e )
                    self.connected = False
                    raise StreamThreadException(e) from e

    def disconnect(self):
        """
        Disconnects the port if is connected.
        """
        if self.stream is not None:
            if self.log_file is not None :
                self.log_file.info("Stream %s : Disconnecting stream",self.stream_id)
            try:
                if self.send_close_script:
                    self.send_script(self.linked_data[self.stream_id], False)
                self.stop_event.set()
                self.current_task = None
                self.datalink_stream_thread.join()
                if self.log_file is not None :
                    self.log_file.debug("Stream %s : wait for Thread to stop",self.stream_id)
                self.stream.close()
                self.connected = False
                self.data_transfer_input = 0.0
                self.data_transfer_output = 0.0
                if self.log_file is not None :
                    self.log_file.info("Stream %s : Disconnected",self.stream_id)
            except Exception as e:
                if self.log_file is not None :
                    self.log_file.error("Stream %s : Failed to disconnect stream : %s",self.stream_id,e)
                raise DisconnectError(e) from e

    def update_linked_ports(self, link : int):
        """
        Updates the linked port with the specified link.

        Args:
            link: The link to update.

        """
        if link in self.linked_ports:
            if self.log_file is not None :
                self.log_file.info("Stream %s : remove link : %s",self.stream_id,link)
            self.linked_ports.remove(link)
        else:
            if self.log_file is not None :
                self.log_file.info("Stream %s : add link : %s",self.stream_id,link)
            self.linked_ports.append(link)
        if self.connected :
            self.update_linked_ports_queue.put(link)

    def to_string(self):
        """
        Return current running stream settings class as a string
        Returns:
            classToString(str , None):  Return the class as a string
        """
        if self.stream_type == StreamType.Serial:
            return self.serial_settings.to_string()
        elif self.stream_type == StreamType.TCP:
            return self.tcp_settings.to_string()
        elif self.stream_type == StreamType.UDP:
            return self.udp_settings.to_string()
        elif self.stream_type == StreamType.NTRIP:
            return self.ntrip_client.ntrip_settings.to_string()
        else:
            return ""

    def send_script(self, output_queue : queue.Queue , startup : bool):
        """
        ouput every command found in a script file
        Args:
            queue (queue.Queue): output queue
            startup (bool): if startup script then True , else False

        Raises:
            : Error while opening script file 
        """
        try :
            if startup :
                if self.log_file is not None :
                    self.log_file.info("Stream %s : send Startup script command",self.stream_id)
                if self.startup_script != "":
                    if self.log_file is not None :
                        self.log_file.debug("Stream %s : open Startup script file",self.stream_id)
                    open_script = open(self.startup_script,"r",encoding="utf-8")
                    if open_script is not None:

                        if self.log_file is not None :
                            self.log_file.debug("Stream %s : file not empty , send command to thread",self.stream_id)

                        for line in open_script:
                            output_queue.put(line)
            else :
                if self.log_file is not None :
                    self.log_file.info("Stream %s : send closeup script command",self.stream_id)

                if self.close_script != "":

                    if self.log_file is not None :
                        self.log_file.debug("Stream %s : open closeup script file",self.stream_id)

                    open_script = open(self.close_script,"r",encoding="utf-8")
                    if open_script is not None:

                        if self.log_file is not None :
                            self.log_file.debug("Stream %s : file not empty , send command to thread",self.stream_id)

                        for line in open_script:
                            output_queue.put(line)

        except Exception as e:
            if self.log_file is not None :
                    self.log_file.error("Stream %s : failed to send script command to thread : %s",self.stream_id,e)
            raise ScriptFileException("Couldn't open the script file " + e) from e
    
    def send_command(self, command :str):
        """
        send a command to ouput
        """
        self.linked_data[self.stream_id].put(command)
    # Getter & Setter

    def toggle_incomming_data_visibility(self):
        """
        Toggles the visibility of input data.
        """
        return self.show_incoming_data.clear() if self.show_incoming_data.is_set() is True else self.show_incoming_data.set()

    def toggle_outgoing_data_visibility(self):
        """
        Toggles the visibility of output data.
        """
        return self.show_outgoing_data.clear() if self.show_outgoing_data.is_set() is True else self.show_outgoing_data.set()

    def toggle_all_data_visibility(self):
        """
        Toggle the data visibility for both output and input
        """
        self.toggle_incomming_data_visibility()
        self.toggle_outgoing_data_visibility()

    def set_logging(self):
        """
        Toggle the logging event
        """
        if self.logging:
            self.logging = False
        else :
            self.logging = True

    def set_startup_script(self):
        """
        Toggle the send script on startup event
        """
        if self.send_startup_script :
            self.send_startup_script = False
        else :
            self.send_startup_script = True

    def set_close_script(self):
        """
        Toggle the send script on closeup event
        """
        if self.send_close_script :
            self.send_close_script = False
        else :
            self.send_close_script = True

    def set_close_script_path(self , new_path :str ):
        """
        set the path to the closeup script file

        Args:
            new_path (str): the new path to the closeup script

        Raises:
            Exception: File not found
        """
        if os.path.exists(new_path) :
            self.close_script = new_path
        else :
            if self.log_file is not None :
                self.log_file.error("Stream %s : Closeup file not found : %s",self.stream_id,new_path)
            raise ScriptFileException("File not found ")

    def set_startup_script_path(self,new_path :str ):
        """
        set the path to the startup script file
        Args:
            new_path (str): the new path to the startup script

        Raises:
            ScriptFileException: File not Found 
        """
        if os.path.exists(new_path) :
            self.startup_script = new_path
        else :
            if self.log_file is not None :
                self.log_file.error("Stream %s : Startup file not found : %s",self.stream_id,new_path)
            raise ScriptFileException("File not found ")

    def set_logging_file_name(self,new_file_name : str):
        """
        Set the logging file name use when logging is True

        Args:
            new_file_name (str): the new file name of the logging file
        """
        if os.path.exists(new_file_name):
            self.logging_file = new_file_name
        else :
            if self.log_file is not None :
                self.log_file.error("Stream %s : Logging file Path not found : %s",self.stream_id,new_file_name)
            raise LogFileException("Path not found")

    def set_stream_type(self,new_stream_type : StreamType):
        """
        Change the stream type of the current stream

        Args:
            new_stream_type (StreamType): the new stream type
        """
        self.stream_type = new_stream_type

    def set_line_termination(self,new_line_termination :str):
        """
        set new line of termination

        Args:
            new_line_termination (str): the new line termination
        """
        self.line_termination = new_line_termination

    def is_connected(self):
        """
        return the current state of the stream

        Returns:
            status(bool): return True if stream is connected , otherwise False
        """
        if self.datalink_stream_thread is None :
            return False
        if self.datalink_stream_thread.is_alive() :
            self.connected = True
        else :
            self.connected = False
        return self.connected

    def _clear_queue(self, queue_to_empty : queue.Queue):
        """
        clear the queue passed as argument
        Args:
            queue (queue.Queue): queue to empty
        """
        while not queue_to_empty.empty():
            queue_to_empty.get()

    def _exception_disconnect(self):
        """
        Disconnects the port if is connected in case of a exception caused in the task Thread
        """
        self.stop_event.set()
        self.current_task = None
        try :
            if self.stream is not None:
                self.stream.close()
        finally:
            self.connected = False  
            self.data_transfer_input = 0.0
            self.data_transfer_output = 0.0
    
    
    
    # Thread task Methods 
    
    def datalink_serial_task(self, serial: Serial, linked_data: list[queue.Queue], update_linked_ports_queue: queue.Queue 
                           , data_to_show : queue.Queue  , logger ):
        """
        The task for data link Stream using serial communication.

        Args:
            serial: The serial Stream object.
            linkedData: A list of linked data queues.
            update_linked_ports_queue: The queue for updating linked ports.

        Returns:
            int: 0 if the task completes, otherwise None.
        """
        linked_ports = []
        temp_incoming_tranfert = 0
        temp_outgoing_tranfert = 0
        # Send startup command
        if self.log_file is not None :
            self.log_file.info("Stream %i : Task Started " , self.stream_id )
            self.log_file.info("Stream %i : sending startup script" , self.stream_id )
        try:
            if not self.linked_data[self.stream_id].empty():
                task_send_command(self.linked_data[self.stream_id],serial,logger=logger,line_termination=self.line_termination)
        except TaskException as e :
            if self.log_file is not None :
                self.log_file.error("Stream %i :  Start script couldn't finish : %e ", self.stream_id , e )
            self._exception_disconnect()
            raise ScriptFileException(f"Start script couldn't finish {e}") from e
        current_time = datetime.now()
        #Main loop
        if self.log_file is not None :
            self.log_file.info("Stream %i : sending startup script finished  ", self.stream_id )
            self.log_file.info("Stream %i : start main loop",self.stream_id )
        while self.stop_event.is_set() is not True:
            temp_incoming_tranfert ,temp_outgoing_tranfert, current_time =  self.task_data_transfer_rate( current_time , temp_incoming_tranfert , temp_outgoing_tranfert)
            try:
                if serial is not None:
                    if serial.is_open:
                        incoming_data = serial.readline()
                        temp_incoming_tranfert += len(incoming_data)
                        if len(incoming_data) != 0 :
                            if self.show_incoming_data.is_set() :
                                data_to_show.put(incoming_data.decode(encoding='ISO-8859-1'))
                            if self.logging:
                                logger.write(incoming_data.decode(encoding='ISO-8859-1'))
                            if linked_ports is not None:
                                for portid in linked_ports:
                                    linked_data[portid].put(incoming_data)
                        if not linked_data[self.stream_id].empty():
                            temp_outgoing_tranfert += task_send_command(linked_data[self.stream_id],serial,self.show_outgoing_data.is_set(), data_to_show=data_to_show,logger=logger,line_termination=self.line_termination )
            except Exception as e:
                self._exception_disconnect()
                if self.log_file is not None :
                    self.log_file.error("Stream %i %s has been disconnected, error: %e",self.stream_id , self.stream_type , e )
                raise StreamThreadException(f"Stream {self.stream_id} {self.stream_type} has been disconnected, error: {e}") from e
            #Update current linked Streams list
            if not update_linked_ports_queue.empty():
                task_update_linked_port(update_linked_ports_queue, linked_ports)
        #Send closeup commands
        if self.log_file is not None :
            self.log_file.info("Stream %i : main loop ended ",self.stream_id )
            self.log_file.info("Stream %i : sending closing script" , self.stream_id )
        try :
            if not self.linked_data[self.stream_id].empty():
                task_send_command(linked_data[self.stream_id],serial,logger=logger,line_termination=self.line_termination)
        except TaskException as e :
            if self.log_file is not None :
                self.log_file.error("Stream %i :  closing script couldn't finish : %e " , self.stream_id , e)
            raise ScriptFileException(f"Closeup script couldn't finish {e}") from e
        return 0

    def datalink_tcp_server_task(self, tcp: socket.socket, linked_data: list[queue.Queue], update_linked_ports_queue: queue.Queue 
                              ,  data_to_show : queue.Queue , logger):
        """
        The task for data link Stream using TCP communication.

        """
        linked_ports: list[int] = []
        tcp.settimeout(0.1)
        tcp.setblocking(0)
        temp_incoming_tranfert = 0
        temp_outgoing_tranfert = 0
        # Wait for a client to connect to the server
        if self.log_file is not None :
            self.log_file.info("Stream %i : Task Started " , self.stream_id )
            self.log_file.info("Stream %i : waiting for client to connect " , self.stream_id)
        while True:
            try:
                tcp.listen()
                conn, _ = tcp.accept()
                conn.settimeout(0.1)
                break
            except (TimeoutError , BlockingIOError) :
                if self.stop_event.is_set():
                    return self._exception_disconnect()
        # Send startup command
        if self.log_file is not None :
            self.log_file.info("Stream %i : sending startup script" , self.stream_id )
        try:
            if not self.linked_data[self.stream_id].empty():
                task_send_command(self.linked_data[self.stream_id],conn,logger=logger,line_termination=self.line_termination)
        except TaskException as e :
            if self.log_file is not None :
                self.log_file.error("Stream %i :  Start script couldn't finish : %e ", self.stream_id , e )
            self._exception_disconnect()
            raise ScriptFileException(f"Start script couldn't finish {e}") from e
        current_time = datetime.now()
        #Main loop
        if self.log_file is not None :
            self.log_file.info("Stream %i : sending startup script finished  ", self.stream_id )
            self.log_file.info("Stream %i : start main loop",self.stream_id )
        while self.stop_event.is_set() is not True:
            temp_incoming_tranfert ,temp_outgoing_tranfert, current_time =  task_data_transfer_rate(self , current_time , temp_incoming_tranfert , temp_outgoing_tranfert)
            try:
                #If a client is connected
                if conn is not None:
                    #Read input data 
                    try:
                        incoming_data = conn.recv(4096)
                        temp_incoming_tranfert += len(incoming_data)
                        if len(incoming_data) == 0:
                            conn = None
                    except socket.timeout:
                        incoming_data = ""
                    if len(incoming_data) != 0 :
                        if self.logging:
                            logger.write(incoming_data.decode(encoding='ISO-8859-1'))
                        # Print data if show data input
                        if self.show_incoming_data.is_set() :
                            data_to_show.put(incoming_data.decode(encoding='ISO-8859-1'))
                        # Send input data to linked Streams
                        if linked_ports is not None :
                            for portid in linked_ports:
                                linked_data[portid].put(incoming_data)
                    #Send output data comming from other streams and print data if showdata is set
                    if not linked_data[self.stream_id].empty():
                        temp_outgoing_tranfert+= task_send_command(linked_data[self.stream_id] , conn , self.show_outgoing_data.is_set(), data_to_show=data_to_show,logger=logger,line_termination=self.line_termination)
                else :
                    time.sleep(1)
                    #Wait for a new Client if the current one has disconnect
                    if self.log_file is not None :
                        self.log_file.info(f"Stream {self.stream_id} : Client disconnected  {e}")
                    while True:
                        try:
                           
                            tcp.listen()
                            conn, address = tcp.accept()
                            conn.settimeout(0.1)
                            if self.log_file is not None :
                                self.log_file.info(f"Stream {self.stream_id} : new Client Connected  {e}")
                            break
                        except Exception as e :
                            if self.stop_event.is_set():
                                raise e 
            except Exception as e:
                self._exception_disconnect()
                if self.log_file is not None :
                    self.log_file.error("Stream %i %s has been disconnected, error: %e",self.stream_id , self.stream_type , e )
                raise StreamThreadException(f"Stream {self.stream_id} {self.stream_type} has been disconnected, error: {e}") from e
            #Update current linked Streams list
            if not update_linked_ports_queue.empty():
                linked_ports = task_update_linked_port(update_linked_ports_queue , linked_ports)
        #Send closeup commands
        if self.log_file is not None :
            self.log_file.info("Stream %i : main loop ended ",self.stream_id )
            self.log_file.info("Stream %i : sending closing script" , self.stream_id )
        try : 
            if not self.linked_data[self.stream_id].empty():
                task_send_command(self.linked_data[self.stream_id],conn,logger=logger,line_termination=self.line_termination)
        except TaskException as e :
            if self.log_file is not None :
                    self.log_file.error("Stream %i :  closing script couldn't finish : %e " , self.stream_id , e)
            raise ScriptFileException(f"Closeup script couldn't finish {e}") from e
        return 0
    
    def datalink_tcp_client_task(self, tcp: socket.socket, linked_data: list[queue.Queue], update_linked_ports_queue: queue.Queue 
                              ,  data_to_show : queue.Queue , logger):
        """
        The task for data link Stream using TCP communication.

        """
        linked_ports: list[int] = []
        tcp.settimeout(0.1)
        conn = 1
        temp_incoming_tranfert = 0
        temp_outgoing_tranfert = 0
        #Send startup command
        if self.log_file is not None :
            self.log_file.info("Stream %i : Task Started " , self.stream_id )
            self.log_file.info("Stream %i : sending startup script" , self.stream_id )
        try:
            if not self.linked_data[self.stream_id].empty():
                task_send_command(self.linked_data[self.stream_id],tcp,logger=logger,line_termination=self.line_termination)
        except TaskException as e :
            if self.log_file is not None :
                self.log_file.error("Stream %i :  Start script couldn't finish : %e ", self.stream_id , e )
            self._exception_disconnect()
            raise ScriptFileException(f"Start script couldn't finish {e}") from e
        current_time = datetime.now()
        #Main loop
        if self.log_file is not None :
            self.log_file.info("Stream %i : sending startup script finished  ", self.stream_id )
            self.log_file.info("Stream %i : start main loop",self.stream_id )
        while self.stop_event.is_set() is not True:
            temp_incoming_tranfert ,temp_outgoing_tranfert,current_time =  task_data_transfer_rate(self , current_time , temp_incoming_tranfert , temp_outgoing_tranfert)          
            try:
                #While Connection still up 
                if conn  is not None :
                    #Read input data 
                    try:
                        incoming_data = tcp.recv(4096)
                        temp_incoming_tranfert += len(incoming_data)
                        if len(incoming_data) == 0:
                            conn = None
                    except socket.timeout:
                        incoming_data = ""
                    except ConnectionResetError :
                        conn = None
                    except BrokenPipeError :
                        conn = None
                    # Print if show data
                    if len(incoming_data) != 0:
                        if self.logging:
                            logger.write(incoming_data.decode(encoding='ISO-8859-1'))
                        if self.show_incoming_data.is_set():
                            data_to_show.put(incoming_data.decode(encoding='ISO-8859-1'))
                        # Send data to linked stream
                        if linked_ports is not None:
                            for portid in linked_ports:
                                linked_data[portid].put(incoming_data)
                    # Output data comming from other streams
                    if not linked_data[self.stream_id].empty():
                        returnedValue = task_send_command(linked_data[self.stream_id],tcp,self.show_outgoing_data.is_set(),data_to_show=data_to_show,logger=logger,line_termination=self.line_termination)
                        if returnedValue is not None :
                            temp_outgoing_tranfert += returnedValue
                else : 
                    # If connection Lost try to reconnect to the server
                    while True:
                        try:
                            tcp = self.tcp_settings.connect()
                            conn = 1
                            break
                        except TimeoutError:
                            if self.stop_event.is_set():
                                return 0
                            
            #If there is any probleme , disconnect everything and kill thread
            except Exception as e:
                self._exception_disconnect()
                if self.log_file is not None :
                    self.log_file.error("Stream %i %s has been disconnected, error: %e",self.stream_id , self.stream_type , e )
                raise StreamThreadException(f"Stream {self.stream_id} {self.stream_type} has been disconnected, error: {e}") from e
            
            # Update Current linked Stream list
            if not self.update_linked_ports_queue.empty():
                task_update_linked_port(self.update_linked_ports,linked_ports)
        # Send Closeup command
        if self.log_file is not None :
            self.log_file.info("Stream %i : main loop ended ",self.stream_id )
            self.log_file.info("Stream %i : sending closing script" , self.stream_id )
        try : 
            task_send_command(self.linked_data[self.stream_id],tcp,logger=logger,line_termination=self.line_termination)
        except TaskException as e :
            if self.log_file is not None :
                    self.log_file.error("Stream %i :  closing script couldn't finish : %e " , self.stream_id , e)
            raise ScriptFileException(f"Start script couldn't finish {e}") from e
        return 0
                    
    def datalink_udp_task(self, udp: socket.socket, linked_data: list[queue.Queue], update_linked_ports_queue: queue.Queue 
                           , data_to_show : queue.Queue, logger ):
        """
        Task for data link Stream using UDP communication.
        """
        linked_ports = []
        temp_incoming_tranfert = 0
        temp_outgoing_tranfert = 0
        bytes_address_pair = None
        udp.settimeout(0.1)
        if self.udp_settings.specific_host is True:
            sendaddress = (self.udp_settings.host, self.udp_settings.port)
        else:
            sendaddress = ('localhost', self.udp_settings.port)
        #Send Startup command
        if self.log_file is not None :
            self.log_file.info("Stream %i : Task Started " , self.stream_id )
            self.log_file.info("Stream %i : sending startup script" , self.stream_id )
        try:
            if not self.linked_data[self.stream_id].empty():
                if sendaddress is not None:
                    task_send_command(self.linked_data[self.stream_id] , stream=udp , udp_send_address=sendaddress,logger = logger,line_termination = self.line_termination)
        except TaskException as e :
            if self.log_file is not None :
                self.log_file.error("Stream %i :  Start script couldn't finish : %e ", self.stream_id , e )
            self._exception_disconnect()
            raise ScriptFileException(f"Start script couldn't finish {e}") from e
        current_time = datetime.now()
        #Main loop
        if self.log_file is not None :
            self.log_file.info("Stream %i : sending startup script finished  ", self.stream_id )
            self.log_file.info("Stream %i : start main loop",self.stream_id )
        while self.stop_event.is_set() is not True:
            temp_incoming_tranfert ,temp_outgoing_tranfert,current_time =  task_data_transfer_rate(self , current_time , temp_incoming_tranfert , temp_outgoing_tranfert)
            try:
                #Continue is Stream is still up
                if udp is not None:
                    if self.udp_settings.dataflow.value in (1, 2):
                        try :
                            bytes_address_pair = udp.recvfrom(4096)
                            incoming_data = bytes_address_pair[0]
                            temp_incoming_tranfert += len(incoming_data)
                        except socket.timeout :
                            incoming_data = ""
                        if len(incoming_data) != 0:
                            if self.show_incoming_data.is_set():
                                data_to_show.put(incoming_data.decode(encoding='ISO-8859-1'))
                                if self.logging:
                                    logger.write(incoming_data.decode(encoding='ISO-8859-1'))

                            if linked_ports is not None :
                                for port in linked_ports:
                                    linked_data[port].put(incoming_data)

                    if self.udp_settings.dataflow.value in (0, 2):
                        if not linked_data[self.stream_id].empty():
                            if bytes_address_pair is not None:
                                send_to_addresse = (bytes_address_pair[1],self.udp_settings.port)
                            else :
                                send_to_addresse = sendaddress
                                returned_value = task_send_command(self.linked_data[self.stream_id] , stream=self.stream , show_data=self.show_outgoing_data.is_set() , udp_send_address=send_to_addresse , data_to_show=self.data_to_show,logger=logger,line_termination=self.line_termination)
                                if returned_value is not None :
                                    temp_outgoing_tranfert += returned_value
            except Exception as e:
                self._exception_disconnect()
                if self.log_file is not None :
                    self.log_file.error("Stream %i %s has been disconnected, error: %e",self.stream_id , self.stream_type , e )
                raise StreamThreadException(f"Stream {self.stream_id} {self.stream_type} has been disconnected, error: {e}") from e
            #Update linked Streams list
            if not self.update_linked_ports_queue.empty():
                task_update_linked_port(update_linked_ports_queue,linked_ports)
        #Send closeup Commands
        if self.log_file is not None :
            self.log_file.info("Stream %i : main loop ended ",self.stream_id )
            self.log_file.info("Stream %i : sending closing script" , self.stream_id )
        try : 
            if not self.linked_data[self.stream_id].empty():
                if sendaddress is not None:
                    task_send_command(self.linked_data[self.stream_id] ,stream= udp  , udp_send_address=sendaddress,logger=logger,line_termination=self.line_termination)
        except TaskException as e :
            if self.log_file is not None :
                self.log_file.error("Stream %i :  closing script couldn't finish : %e " , self.stream_id , e)
            raise ScriptFileException(f"Start script couldn't finish {e}") from e
        return 0
    
    def datalink_ntrip_task(self, ntrip : NtripClient, linked_data: list[queue.Queue], update_linked_ports_queue: queue.Queue 
                           , data_to_show : queue.Queue , logger):
        """
        Process the NTRIP data received from the NTRIP client and send correction to other the linked streams .

        Args:
            ntrip (NtripClient): The NTRIP client object.
            linked_data (list[queue.Queue]): list of queues for sending or reading data to/from other streams .
            update_linked_ports (queue.Queue): The queue for updating the linked ports.
        """
        linked_ports: list[int] = []
        ntrip.socket.settimeout(0.1)
        temp_incoming_tranfert = 0
        temp_outgoing_tranfert = 0
        # Send startup command
        if self.log_file is not None :
            self.log_file.info("Stream %i : Task Started " , self.stream_id )
            self.log_file.info("Stream %i : sending startup script" , self.stream_id )
        try:
            if self.ntrip_client.ntrip_settings.fixed_pos :
                self.linked_data[self.stream_id].put(self.ntrip_client.fixed_pos_gga)
            if not self.linked_data[self.stream_id].empty():
                task_send_command(self.linked_data[self.stream_id],ntrip ,logger=logger,line_termination=self.line_termination)
        except TaskException as e :
            if self.log_file is not None :
                    self.log_file.error("Stream %i :  Start script couldn't finish : %e ", self.stream_id , e )
            self._exception_disconnect()
            raise ScriptFileException(f"Start script couldn't finish {e}") from e    
        current_time = datetime.now()
        #Main loop
        if self.log_file is not None :
            self.log_file.info("Stream %i : sending startup script finished  ", self.stream_id )
            self.log_file.info("Stream %i : start main loop",self.stream_id )
        while self.stop_event.is_set() is not True:
            temp_incoming_tranfert ,temp_outgoing_tranfert,current_time =  task_data_transfer_rate(self , current_time , temp_incoming_tranfert , temp_outgoing_tranfert) 
            try:
                if ntrip is not None:
                    #Read input data
                    try:
                        incoming_data = ntrip.socket.recv(4096)
                        temp_incoming_tranfert += len(incoming_data)
                    except socket.timeout:
                        incoming_data = ""
                    except (socket.gaierror,socket.herror) as e :
                        raise e
                    # Print data if show data input
                    if len(incoming_data) != 0:
                        if self.logging:
                            logger.write(str(incoming_data))
                        if self.show_incoming_data.is_set():
                            data_to_show.put(incoming_data.decode(encoding='ISO-8859-1'))
                        # Send input data to linked Streams
                        if linked_ports is not None:
                            for portid in linked_ports:
                                linked_data[portid].put(incoming_data.decode(encoding='ISO-8859-1'))
                    #Send output data comming from other streams and print data if showdata is set
                    if not linked_data[self.stream_id].empty():
                        returnedValue = task_send_command(linked_data[self.stream_id],ntrip ,self.show_outgoing_data.is_set(),data_to_show=data_to_show,logger=logger,line_termination=self.line_termination)
                        if returnedValue is not None :
                            temp_outgoing_tranfert += returnedValue
            except Exception as e:
                self._exception_disconnect()
                if self.log_file is not None :
                    self.log_file.error("Stream %i %s has been disconnected, error: %e",self.stream_id , self.stream_type , e )
                raise StreamThreadException(f"Stream {self.stream_id} {self.stream_type} has been disconnected, error: {e}") from e
            #Update current linked Streams list
            if not self.update_linked_ports_queue.empty():
                task_update_linked_port(update_linked_ports_queue,linked_ports)
        if self.log_file is not None :
            self.log_file.info("Stream %i : main loop ended ",self.stream_id )
            self.log_file.info("Stream %i : sending closing script" , self.stream_id )
        #Send closeup commands
        try :
            if not self.linked_data[self.stream_id].empty():

                task_send_command(self.linked_data[self.stream_id],ntrip,
                                  logger=logger,line_termination=self.line_termination)

        except TaskException as e :
            if self.log_file is not None :
                    self.log_file.error("Stream %i :  closing script couldn't finish : %e " , self.stream_id , e)
            raise ScriptFileException(f"Start script couldn't finish {e}") from e
        return 0

    # Command line Configuration Functions 

    
    def _ExceptionDisconnect(self):
        """
        Disconnects the port if is connected in case of a exception caused in the task Thread
        """
        if self.log_file is not None : 
            self.log_file.info("Stream %s : Disconnecting stream due to error in task")
        self.stop_event.set()
        self.current_task = None
        try :
            self.stream.close()
        finally:
            self.connected = False  
            self.data_transfer_input = 0.0
            self.data_transfer_output = 0.0
    
    def _clearQueue(self, queue : queue.Queue):
        """
        clear the queue passed as argument
        Args:
            queue (queue.Queue): queue to empty
        """
        while not queue.empty():
            queue.get()
            
    def task_data_transfer_rate(self , current_time  , temp_incoming_tranfert , temp_outgoing_tranfert) :
        """
        Calculate current data rate from incoming and outgoing stream
        """
        now = datetime.now()
        if (now-current_time).total_seconds() >=  1 :
            current_time = now
            self.data_transfer_input = round(temp_incoming_tranfert/1000,1)
            self.data_transfer_output = round(temp_outgoing_tranfert/1000,1)
            return 0 , 0 , current_time
        else :
            return temp_incoming_tranfert , temp_outgoing_tranfert ,current_time
#####################################################################################
# STREAM TASK
#####################################################################################

def task_update_linked_port(update_linked_ports_queue : queue.Queue , linked_ports : list[int] ):
    """
    update the list of port to which we have to share incoming data
    """
    for _ in range(update_linked_ports_queue.qsize()):
        port = update_linked_ports_queue.get()
        if port in linked_ports:
            linked_ports.remove(port)
        else:
            linked_ports.append(port)
    return linked_ports


def task_send_command(linked_data : queue.Queue , stream  : Serial | socket.socket | NtripClient, show_data : bool = False ,
                      udp_send_address = None ,  data_to_show : queue.Queue = None ,
                      logger : TextIOWrapper = None , line_termination : str = "\r\n"):
    """
    output data from data queue
    """
    try :
        for _ in range(linked_data.qsize()):
            outgoing_data = linked_data.get()
            if isinstance(outgoing_data, str):
                outgoing_data = outgoing_data.encode(encoding='ISO-8859-1')
            if isinstance(stream , Serial):
                stream.write(outgoing_data)
            elif isinstance(stream, socket.socket) and udp_send_address is None:
                stream.sendall(outgoing_data)
            elif isinstance(stream, socket.socket) :
                stream.sendto(outgoing_data, udp_send_address)
            elif isinstance(stream, NtripClient): 
                if isinstance(outgoing_data , bytes):
                    outgoing_data = outgoing_data.decode(encoding='ISO-8859-1')
                if "GGA" in outgoing_data:
                    stream.send_nmea(outgoing_data)
            else : continue
            if show_data and len(outgoing_data) != 0 :
                data_to_show.put(outgoing_data)
                try :
                    if logger is not None:
                        logger.write(outgoing_data)
                except : pass
            return len(outgoing_data)
    except (NtripClientError, socket.gaierror, SerialException)  as e :
        raise TaskException(e) from e
    

def task_data_transfer_rate(stream :Stream , current_time  , temp_incoming_tranfert , temp_outgoing_tranfert) :
    """
    Calculate current data rate from incoming and outgoing stream
    """
    now = datetime.now()
    if (now-current_time).total_seconds() >=  1 :
        current_time = now 
        stream.data_transfer_input = round(temp_incoming_tranfert/1000,1)
        stream.data_transfer_output = round(temp_outgoing_tranfert/1000,1)
        return 0 , 0 , current_time
    else :
        return temp_incoming_tranfert , temp_outgoing_tranfert ,current_time 
 