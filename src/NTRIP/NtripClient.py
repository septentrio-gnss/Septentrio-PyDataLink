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
from .NtripSourceTable import NtripSourceTable
from .NtripSettings import NtripSettings
import logging
from ..constants import DEFAULTLOGFILELOGGER

RAD2DEGREES = 180.0 / 3.141592653589793

class SendRequestError(Exception):
    pass
class ReceiveRequestError(Exception):
    pass
class SourceTableRequestError(Exception):
    pass
class ConnectRequestError(Exception):
    pass
class ClosingError(Exception):
    pass
class NtripClient:
    
    def __init__(self, host : str = "" , port : int = 2101 , auth : bool = False, username : str = "" , password : str = "" , mountpoint :str = "",tls :bool =False ,
                 fixedPos : bool = False , latitude : float = 00.00, longitude : float = 00.00 , height : int = 0 , debugLogging : bool = False) -> None:
                  
        self.ntripSettings : NtripSettings = NtripSettings(host,port,auth,username,password,mountpoint,tls,fixedPos,latitude,longitude,height,debugLogging)
        self.socket = None
        self.connected : bool = False
        self.fixedPosGga : str 
        if debugLogging :
            self.logFile : logging.Logger = DEFAULTLOGFILELOGGER
        else :
            self.logFile = None
        

    def connect(self):
        self.logFile.debug("Create NTRIP Client socket")
        self.socket = self.ntripSettings.connect()
        self.connected = True
        self.logFile.info("NTRIP Client socket Created")
        try:
            self._connectRequest()
        except Exception as e:
            self.connected = False
            raise e

    def sendNMEA(self, nmeaMessage):
        if self.logFile is not None : 
            self.logFile.debug("Sending NMEA Message : %s", nmeaMessage)
        if self.ntripSettings.ntripVersion == 2 : 
            request = "GET /"+ self.ntripSettings.mountpoint +" HTTP/1.1\r\n"
        else : 
            request = "GET /"+ self.ntripSettings.mountpoint +" HTTP/1.0\r\n"
        request += "Host: " + self.ntripSettings.host + "\r\n"
        request += "User-Agent: NTRIP Python Client\r\n"
        if self.ntripSettings.ntripVersion == 2 : 
            request += "Ntrip-Version: Ntrip/2.0\r\n"
        else : 
            request += "Ntrip-Version: Ntrip/1.0\r\n"
        if self.ntripSettings.auth :
            request += "Authorization: Basic " +  base64.b64encode((self.ntripSettings.username + ":" + self.ntripSettings.password).encode()).decode() + "\r\n"
        if self.ntripSettings.ntripVersion ==2 : 
            request += "Ntrip-GGA: " + nmeaMessage + "\r\n"
            request += "Connection: close\r\n\r\n"
        else :
            request +=  nmeaMessage + "\r\n"
        
        self._sendRequest(request)
    
    def getSourceTable(self):
        if self.logFile is not None :
            self.logFile.debug("Getting source table from NTRIP Caster %s" ,self.ntripSettings.host )
        tempConnection = None
        if not self.connected:
            try :
                self.socket = self.ntripSettings.connect()
            except Exception as e: 
                self.logFile.error("Failed to connect to NTRIP caster %s : %s" , self.ntripSettings.host,e)
                raise SourceTableRequestError(e)
            tempConnection = True
            
        request = "GET / HTTP/1.1\r\n"
        request += "Host: " + self.ntripSettings.host + "\r\n"
        request += "User-Agent: NTRIP pydatalink Client\r\n"
        request += "Ntrip-Version: Ntrip/2.0\r\n"
        if self.ntripSettings.auth : 
            request+="Authorization: Basic " +  base64.b64encode((self.ntripSettings.username + ":" + self.ntripSettings.password).encode()).decode() + "\r\n"
        request += "Connection: close\r\n\r\n"
        
        try :
            self._sendRequest(request)
        except SendRequestError as e :
            if self.logFile is not None :
                self.logFile.error("Failed to send Header : %s" ,e)
            raise SourceTableRequestError("Failed to send header")
        try :
            response : str = self._receiveResponse()
        except ReceiveRequestError as e :
            if self.logFile is not None :
                self.logFile.error("Failed to read source table : %s" ,e)
            raise SourceTableRequestError("Failed to read source table")
        if "200" in response :
            if self.logFile is not None :
                self.logFile.info("parsing source table ")
            # Parse the response to extract the resource table
            response : str= response.split("\r\n\r\n")[1]
            sources = response.split("STR;")
            sources.pop(0)
            sources.pop()
            source_table : list[NtripSourceTable]= []
            for source in sources :
                newsourcetable = source.split(";")
                source_table.append(NtripSourceTable(newsourcetable[0],newsourcetable[1],newsourcetable[2],newsourcetable[3]))
            if tempConnection is not None:
                self.close()
            if self.logFile is not None :
                self.logFile.debug("Number of mountpoints available from %s : %s " , self.ntripSettings.host , str(len(source_table)))
            return source_table
        else :
            if self.logFile is not None : 
                        self.logFile.error("The return value is inccorect")
                        self.logFile.debug("NTRIP Caster response : %s",response)
            raise SourceTableRequestError("Error in returned source table")
        
    
    def _connectRequest(self):
        
        if self.ntripSettings.ntripVersion == 2 : 
            request = "GET /"+ self.ntripSettings.mountpoint +" HTTP/1.1\r\n"
        else : 
            request = "GET /"+ self.ntripSettings.mountpoint +" HTTP/1.0\r\n"
        request += f"Host: {self.ntripSettings.host}\r\n"
        request += "User-Agent: NTRIP pydatalink Client\r\n"
        if self.ntripSettings.ntripVersion == 2 : 
            request += "Ntrip-Version: Ntrip/2.0\r\n"
        else : 
            request += "Ntrip-Version: Ntrip/1.0\r\n"
        if self.ntripSettings.auth : 
            request += "Authorization: Basic " +  base64.b64encode((self.ntripSettings.username + ":" + self.ntripSettings.password).encode()).decode() + "\r\n"
        if self.ntripSettings.ntripVersion ==2 : 
            request += "Connection: close\r\n\r\n"
        
        try :
            self._sendRequest(request)
        except SendRequestError as e : 
            if self.logFile is not None : 
                self.logFile.error("Failed to send request : %s",e)
            raise SendRequestError(e)
        try :
            response = self._receiveResponse()
            self.logFile.debug("return value from the request :  %s", response)
            
        except ReceiveRequestError as e: 
            if self.logFile is not None : 
                self.logFile.debug("return value from the request :  %s", response)
                self.logFile.error("Failed to catch response : %s",e)
            raise ReceiveRequestError(e)
        if "HTTP/1.1 40" in response or "HTTP/1.0 40" in response : 
            error = response.split("\r\n\r\n")[1]
            if self.logFile is not None : 
                self.logFile.error("Client error : %s",error.replace("\n","").replace("\r",""))
            raise ConnectRequestError(error)
        
        
    def _sendRequest(self, request : str):
        try:
            self.socket.sendall(request.encode())
        except Exception as e:
            raise SendRequestError(e)
        
    def _receiveResponse(self):
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
                raise ReceiveRequestError(e)
        return response
    
    def _createGgaString(self):
        
        result = ""
        timeString = datetime.datetime.now().strftime("%H%M%S") + ".00"
        minutes,degrees  = math.modf(self.ntripSettings.latitude)
        minutes *= 60
        latString = "{:02d}{:08.5f},{}" .format(int(abs(degrees)), abs(minutes), "N" if self.ntripSettings.latitude > 0 else "S")
        minutes,degrees = math.modf(self.ntripSettings.longitude)
        minutes *= 60
        lonString = "{:03d}{:08.5f},{}".format(int(abs(degrees)), abs(minutes), "E" if self.ntripSettings.longitude > 0 else "W")
        heightString = "{:0.2f},M,0.00,M".format(self.ntripSettings.height)
        result = "$GPGGA,{},{},{},1,08,0.75,{},,*".format(timeString, latString, lonString, heightString)

        checkSum = 0

        for i in range(1, len(result) - 1):
            checkSum ^= ord(result[i])

        result += "{:02X}\r\n".format(checkSum)
        self.fixedPosGga = result
        
        if self.logFile is not None : 
                self.logFile.debug("New GGA String : %s " , result.replace("\n","").replace("\r",""))
        return result

    def close(self):
        try:
            self.socket.close()
            self.connected = False
        except Exception as e:
            raise ClosingError(e)

    def set_Settings_Host(self, host):
        self.ntripSettings.setHost(host)
        if self.logFile is not None: 
            self.logFile.info("New NTRIP Host Name : %s" , host)
        try : 
            self.ntripSettings.sourceTable = self.getSourceTable()
        except Exception as e :
            if self.logFile is not None: 
                self.logFile.error("Failed to get Source Table : %s" , e )
            raise e
