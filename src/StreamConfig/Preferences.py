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

import configparser
import os

"""
Preferences class : save every preferences and options done previously
"""
class Preferences : 

    def __init__(self,maxStreams : int = 2, configName : str = "Datalink_Config" ,lineTermination :str = "\r\n") -> None:
            self.maxStreams = maxStreams
            self.Connect : list[bool] = []
            self.configName : str = configName
            for i in range(maxStreams) :
                self.Connect.append(False)
            self.lineTermination : str = lineTermination
    
    def setMaxStream(self,newMaxStream : int ):
        """
        Set number of stream that can be configure
        
        Args:
            newMaxStream (int): the new number of stream
        """
        self.maxStreams = newMaxStream
        
    def setConfigName(self , newName : str):
        """
        Set the current configuration file name 

        Args:
            newName (str): the new file name 
        """
        self.configName = newName
        
    def setLineTermination(self,newLineTermination :str):
        """
        Set the Termination line when showing data and sending data

        Args:
            newLineTermination (str): the new termination line 
        """
        self.lineTermination = newLineTermination
        
    def getLineTermination(self):
        """
        Convert the termination line to readable string

        Returns:
            termination Line : readable termination line
        """
        return self.lineTermination.replace("\n","\\n").replace("\r","\\r")
            
    