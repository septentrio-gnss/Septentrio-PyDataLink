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
    def __init__(self,app : App , show_data_id : int = None) -> None:
        self.app = app
        self.show_data_id = show_data_id

    def run(self):
        """Start the thread
        """
        if len(self.app.stream_list) == 0 :
            return 0
        else :
            if self.show_data_id is not None:
                target = self._showDataTask
                show_data_port = self.app.stream_list[self.show_data_id]
            else :
                target = self._showDataTransfert
                show_data_port = self.app

            stop_show_data_event = threading.Event()
            stop_show_data_event.clear()
            show_data_thread = threading.Thread(target=target ,args=(stop_show_data_event , show_data_port,))
            show_data_thread.start()
            input("Press Enter to close the program \n")
            stop_show_data_event.set()
            show_data_thread.join()
            self.app.close_all()


    def _showDataTask(self,stop_show_data_event, selected_port : Stream):
        """Show all the data of a specific stream
        """
        while stop_show_data_event.is_set() is False:
            if selected_port.data_to_show.empty() is False :
                print(selected_port.data_to_show.get())
        return 0

    def _showDataTransfert(self,stop_show_data_event, app : App):
        """Show the data transfert rate on all the configured stream
        """
        speed = "\r"
        while stop_show_data_event.is_set() is False:
            time.sleep(1)
            speed = "\r"
            for port in app.stream_list:
                speed += "Port "+ str(port.id) +" : in "+ str(port.data_transfer_input) + " kBps ; out "+ str(port.data_transfer_output) + " kBps "
            print(speed, end="\r") 
        return 0



    
    
    