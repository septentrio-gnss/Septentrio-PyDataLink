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

from src.StreamConfig import App
from src.StreamConfig.Stream import Stream

class CommandLineInterface: 
    def __init__(self,app : App , showdataId : int = None) -> None:
        self.App = app
        self.showdataid = showdataId

    def print(self, message):
        print(message)

    def run(self):
        if len(self.App.stream_list) == 0 : 
            return 0
        else : 
            if self.showdataid is not None: 
                target = self._showDataTask
            else :
                target = self._showDataTransfert
                self.showDataPort = self.App
                
            stopShowDataEvent = threading.Event()
            stopShowDataEvent.clear()
            showDataThread = threading.Thread(target=target , args=(stopShowDataEvent , self.showDataPort,))
            showDataThread.start()
            input("Press Enter to close the program \n")
            stopShowDataEvent.set()
            showDataThread.join()
            self.App.close_all()
    
    
    def _showDataTask(self,stopShowDataEvent, selectedPort : Stream):
        while stopShowDataEvent.is_set() is False:
            if selectedPort.data_to_show.empty() is False :
                print(selectedPort.data_to_show.get())
        return 0
    
    def _showDataTransfert(self,stopShowDataEvent, app : App):
        speed = "\r"
        while stopShowDataEvent.is_set() is False:
            time.sleep(1)
            speed = "\r"
            for port in app.stream_list:
                speed += "Port "+ str(port.id) +" : in "+ str(port.data_transfer_input) + " kBps ; out "+ str(port.data_transfer_output) + " kBps "
            print(speed, end="\r")    
        return 0
        
    

    
    
    