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

class Preferences :
    """
    Preferences class : save every preferences and options done previously
    """

    def __init__(self,max_streams : int = 2, config_name : str = "Datalink_Config" ,
                 line_termination :str = "\r\n") -> None:
        self.max_streams = max_streams
        self.connect : list[bool] = []
        self.config_name : str = config_name
        for _ in range(max_streams) :
            self.connect.append(False)
        self.line_termination : str = line_termination

    def set_max_stream(self,new_max_stream : int ):
        """
        Set number of stream that can be configure
        
        Args:
            new_max_stream (int): the new number of stream
        """
        self.max_streams = new_max_stream

    def set_config_name(self , new_name : str):
        """
        Set the current configuration file name 

        Args:
            new_name (str): the new file name 
        """
        self.config_name = new_name

    def set_line_termination(self,new_line_termination :str):
        """
        Set the Termination line when showing data and sending data

        Args:
            new_line_termination (str): the new termination line 
        """
        self.line_termination = new_line_termination

    def get_line_termination(self):
        """
        Convert the termination line to readable string

        Returns:
            termination Line : readable termination line
        """
        return self.line_termination.replace("\n","\\n").replace("\r","\\r")


