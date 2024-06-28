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
import logging
import os
import datetime
import sys

if getattr(sys, 'frozen', False):
    PROJECTPATH = sys._MEIPASS
    DATAFILESPATH = os.path.join(PROJECTPATH, "data" )
else:
    PROJECTPATH = os.path.abspath(os.path.dirname(__file__)).replace("\\src","") #Path to the project folder
    DATAFILESPATH = os.path.join(PROJECTPATH , "src" , "Data Files" )
    


APPNAME = "PyDataLink"
APPVERSION = "1.0.0-a"
APPRELEASEDATA="27/06/2024"

MAINSCRIPTPATH = os.path.join(PROJECTPATH , "pyDatalink.py")
MAXFILENUMBER = 20
DATAPATH = os.path.join(os.path.expanduser("~") , ".septentrio") # Path to the PyDataLink Data Folder
CONFIGPATH = os.path.join(DATAPATH , "confs" )   # Path to the Configuration folder
LOGFILESPATH =  os.path.join(DATAPATH ,"logs")   # Path to the Logs folder
DEFAULTCONFIGFILE = os.path.join(CONFIGPATH ,"pydatalink.conf")  # Path to the default configuration file

# Check if folder exist else create them 
if os.path.exists(DATAPATH) is not True :
    os.mkdir(DATAPATH)
if os.path.exists( CONFIGPATH ) is not True:
    os.mkdir(CONFIGPATH )
if os.path.exists( LOGFILESPATH ) is not True:
    os.mkdir(LOGFILESPATH )
    
# Create logging file for the app
now = datetime.datetime.now()
filename = now.strftime("pyDatalink_%Y-%m-%d_%H-%M.log")
DEFAULTLOGFILEPATH = LOGFILESPATH + "\\" + filename
logging.basicConfig(filename= DEFAULTLOGFILEPATH, encoding='utf-8', level=logging.DEBUG, format='[%(asctime)s] %(levelname)s : %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
DEFAULTLOGFILELOGGER = logging.getLogger("PyDatalink")
