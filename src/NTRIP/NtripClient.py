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
import datetime
import math
import logging
from .NtripSourceTable import NtripSourceTable
from .NtripSettings import NtripSettings, NtripSettingsException
from ..constants import DEFAULTLOGFILELOGGER

RAD2DEGREES = 180.0 / 3.141592653589793

class NtripClientError(Exception):
    """Raised when a error with the NTRIP Client
    """
    def __init__(self, message, error_code=None):
        super().__init__(message)
        self.error_code = error_code

class SendRequestError(NtripClientError):
    """Error while sending message to NTRIP Caster
    """

class ReceiveRequestError(NtripClientError):
    """Error while receiving a message from NTRIP Caster
    """

class SourceTableRequestError(NtripClientError):
    """
    Error while requesting the source table from NTRIP Caster
    """
class ConnectRequestError(NtripClientError):
    """Error while establishing a connection with NTRIP Caster
    """

class ClosingError(NtripClientError):
    """Error while closing the connection with NTRIP Caster
    """


class NtripClient:
    """Class for a ntrip client 
    """

    def __init__(self, ntrip_settings : NtripSettings = NtripSettings(), debug_logging : bool = False)->None:

        self.ntrip_settings : NtripSettings = ntrip_settings
        self.socket = None
        self.connected : bool = False
        self.fixed_pos_gga : str
        if debug_logging :
            self.log_file : logging.Logger = DEFAULTLOGFILELOGGER
        else :
            self.log_file = None

    def connect(self):
        """Try to start the ntrip connection
        """
        try:
            if self.log_file is not None :
                self.log_file.debug("Create NTRIP Client socket")
            self.socket = self.ntrip_settings.connect()
            self.connected = True
            if self.log_file is not None :
                self.log_file.info("NTRIP Client socket Created")
            self._connect_request()
        except NtripSettingsException as e:
            self.connected = False
            raise e

    def send_nmea(self, nmea_message):
        """Sending nmea message to the ntrip caster
        """
        if self.ntrip_settings.ntrip_version == 2 :
            request = "GET /"+ self.ntrip_settings.mountpoint +" HTTP/1.1\r\n"
        else :
            request = "GET /"+ self.ntrip_settings.mountpoint +" HTTP/1.0\r\n"
        request += "Host: " + self.ntrip_settings.host + "\r\n"
        request += "User-Agent: NTRIP Python Client\r\n"
        if self.ntrip_settings.ntrip_version == 2 :
            request += "Ntrip-Version: Ntrip/2.0\r\n"
        else :
            request += "Ntrip-Version: Ntrip/1.0\r\n"
        if self.ntrip_settings.auth :
            request += "Authorization: Basic " +  base64.b64encode((self.ntrip_settings.username + ":" + self.ntrip_settings.password).encode()).decode() + "\r\n"
        if self.ntrip_settings.ntrip_version ==2 :
            request += "Ntrip-GGA: " + nmea_message + "\r\n"
            request += "Connection: close\r\n\r\n"
        else :
            request +=  nmea_message + "\r\n"
        try :
            self._send_request(request)
        except NtripClientError as e :
            raise SendRequestError(e) from e

    def get_source_table(self):
        """retrive source table from a ntrip caster ,
        if the ntripclient not yet connect ,
        it will open a temporary connection
        """
        if self.log_file is not None :
            self.log_file.debug("Getting source table from NTRIP Caster %s",self.ntrip_settings.host)
        temp_connection = None
        if not self.connected:
            try :
                self.socket = self.ntrip_settings.connect()
            except Exception as e:
                self.log_file.error("Failed to connect to NTRIP caster %s : %s",self.ntrip_settings.host,e)
                raise SourceTableRequestError(e) from e
            temp_connection = True

        request = "GET / HTTP/1.1\r\n"
        request += "Host: " + self.ntrip_settings.host + "\r\n"
        request += "User-Agent: NTRIP pydatalink Client\r\n"
        request += "Ntrip-Version: Ntrip/2.0\r\n"
        if self.ntrip_settings.auth :
            request+="Authorization: Basic " +  base64.b64encode((self.ntrip_settings.username + ":" + self.ntrip_settings.password).encode()).decode() + "\r\n"
        request += "Connection: close\r\n\r\n"

        try :
            self._send_request(request)
        except SendRequestError as e :
            if self.log_file is not None :
                self.log_file.error("Failed to send Header : %s" ,e)
            raise SourceTableRequestError("Failed to send header") from e
        try :
            response : str = self._receive_response()
        except ReceiveRequestError as e :
            if self.log_file is not None :
                self.log_file.error("Failed to read source table : %s" ,e)
            raise SourceTableRequestError("Failed to read source table") from e
        if "200" in response :
            if self.log_file is not None :
                self.log_file.info("parsing source table ")
            # Parse the response to extract the resource table
            source_table : list[NtripSourceTable]= []
            response : str= response.split("\r\n\r\n")[1]
            sources = response.split("STR;")
            
            if len(sources) <= 2 :
                if self.log_file is not None :
                    self.log_file.debug("returned source table empty")
                return source_table
            sources.pop(0)
            sources.pop()
            for source in sources :
                newsourcetable = source.split(";")
                source_table.append(NtripSourceTable(newsourcetable[0],newsourcetable[1],newsourcetable[2],newsourcetable[3]))
            if temp_connection is not None:
                self.close()
            if self.log_file is not None :
                self.log_file.debug("Number of mountpoints available from %s : %s " , self.ntrip_settings.host , str(len(source_table)))
            return source_table
        else :
            if self.log_file is not None :
                self.log_file.error("The return value is inccorect")
                self.log_file.debug("NTRIP Caster response : %s",response)
            raise SourceTableRequestError("Error in returned source table")

    def _connect_request(self):

        if self.ntrip_settings.ntrip_version == 2 :
            request = "GET /"+ self.ntrip_settings.mountpoint +" HTTP/1.1\r\n"
        else :
            request = "GET /"+ self.ntrip_settings.mountpoint +" HTTP/1.0\r\n"
        request += f"Host: {self.ntrip_settings.host}\r\n"
        request += "User-Agent: NTRIP pydatalink Client\r\n"
        if self.ntrip_settings.ntrip_version == 2 :
            request += "Ntrip-Version: Ntrip/2.0\r\n"
        else :
            request += "Ntrip-Version: Ntrip/1.0\r\n"
        if self.ntrip_settings.auth :
            request += "Authorization: Basic " +  base64.b64encode((self.ntrip_settings.username + ":" + self.ntrip_settings.password).encode()).decode() + "\r\n"
        if self.ntrip_settings.ntrip_version ==2 :
            request += "Connection: close\r\n\r\n"

        try :
            self._send_request(request)
        except SendRequestError as e :
            if self.log_file is not None :
                self.log_file.error("Failed to send request : %s",e)
            raise SendRequestError("Failed to send request") from e
        try :
            response = self._receive_response()
            self.log_file.debug("return value from the request :  %s", response)

        except ReceiveRequestError as e:
            if self.log_file is not None :
                self.log_file.debug("return value from the request :  %s", response)
                self.log_file.error("Failed to catch response : %s",e)
            raise ReceiveRequestError("Failed to catch receive a response") from e

        if "HTTP/1.1 40" in response or "HTTP/1.0 40" in response :
            error = response.split("\r\n\r\n")[0].split("\r\n")[0].replace("HTTP/1.1","").replace("HTTP/1.0","")
            if self.log_file is not None :
                self.log_file.error("Client error : %s",error.replace("\n","").replace("\r",""))
            raise ConnectRequestError("Caster Response :"  + error)

    def _send_request(self, request : str):
        try:
            self.socket.sendall(request.encode())
        except Exception as e:
            raise SendRequestError(e) from e

    def _receive_response(self):
        response = ""
        while True:
            try :
                data = self.socket.recv(4096)
                if not data:
                    break
                response += data.decode(encoding='ISO-8859-1')
                if "\r\n\r\n" in response and "sourcetable" not in response :
                    break
            except Exception as e :
                raise ReceiveRequestError(e) from e
        return response

    def create_gga_string(self):
        """Generate GGA String with fixed position
        """
        result = ""
        time_string = datetime.datetime.now().strftime("%H%M%S") + ".00"
        minutes,degrees  = math.modf(self.ntrip_settings.latitude)
        minutes *= 60
        lat_string = f"{int(abs(degrees)):02d}{abs(minutes):08.5f},{'N' if self.ntrip_settings.latitude > 0 else 'S'}"
        minutes,degrees = math.modf(self.ntrip_settings.longitude)
        minutes *= 60
        lon_string = f"{int(abs(degrees)):03d}{abs(minutes):08.5f},{'E' if self.ntrip_settings.longitude > 0 else 'W'}"
        height_string = f"{self.ntrip_settings.height:0.2f},M,0.00,M"
        result = f"$GPGGA,{time_string},{lat_string},{lon_string},1,08,0.75,{height_string},,*"

        checksum = 0

        for i in range(1, len(result) - 1):
            checksum ^= ord(result[i])

        result += f"{checksum:02X}\r\n"
        self.fixed_pos_gga = result

        if self.log_file is not None :
            self.log_file.debug("New GGA String : %s " , result.replace("\n","").replace("\r",""))
        return result

    def close(self):
        """Close current ntrip connection
        """
        try:
            self.socket.close()
            self.connected = False
        except Exception as e:
            raise ClosingError("Error while clossing the socket") from e
        
    def update_source_table(self):
        try :
            self.ntrip_settings.source_table = self.get_source_table()
        except NtripClientError as e :
            if self.log_file is not None:
                self.log_file.error("Failed to get Source Table : %s" , e )
            raise SourceTableRequestError("Error while getting the new source table") from e

    def set_settings_host(self, host):
        """
        Set a new ntrip caster hostname and retrieve the new source table
        """
        if host != self.ntrip_settings.host :
            self.ntrip_settings.set_host(host)
            if self.log_file is not None:
                self.log_file.info("New NTRIP Host Name : %s" , host)
            try :
                self.update_source_table()
            except SourceTableRequestError as e :
                raise e
        
