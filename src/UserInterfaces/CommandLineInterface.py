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
import time
from ..StreamConfig import *

class CommandLineInterface: 
    def __init__(self,streams : Streams , showdataId : int = None) -> None:
        self.Streams = streams
        self.showdataid = showdataId

    def print(self, message):
        print(message)

    def run(self):
        if len(self.Streams.StreamList) == 0 : 
            return 0
        else : 
            if self.showdataid is not None: 
                target = self._showDataTask
            else :
                target = self._showDataTransfert
                self.showDataPort = self.Streams
                
            stopShowDataEvent = threading.Event()
            stopShowDataEvent.clear()
            showDataThread = threading.Thread(target=target , args=(stopShowDataEvent , self.showDataPort,))
            showDataThread.start()
            input("Press Enter to close the program \n")
            stopShowDataEvent.set()
            showDataThread.join()
            self.Streams.CloseAll()
    
    
    def _showDataTask(self,stopShowDataEvent, selectedPort : PortConfig):
        while stopShowDataEvent.is_set() is False:
            if selectedPort.DataToShow.empty() is False :
                print(selectedPort.DataToShow.get())
        return 0
    
    def _showDataTransfert(self,stopShowDataEvent, stream : Streams):
        speed = "\r"
        while stopShowDataEvent.is_set() is False:
            time.sleep(1)
            speed = "\r"
            for port in stream.StreamList:
                speed += "Port "+ str(port.id) +" : in "+ str(port.dataTransferInput) + " kBps ; out "+ str(port.dataTransferOutput) + " kBps "
            print(speed, end="\r")    
        return 0
        
    

    
    
    