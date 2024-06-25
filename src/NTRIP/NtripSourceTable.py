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

class Carrier(Enum):
    NO = 0
    YESL1 = 1
    YESL1L2= 2

class Solution(Enum):
    SIMPLE_BASE = 0
    NETWORK = 1

class Authentication(Enum):
    NONE = 'N'
    BASIC = 'B'
    DIGEST = 'D'
class Fee(Enum) :
    N = "No user fee"
    Y = "Usage is charged"
class NtripSourceTable :

    def __init__(self,mountpoint : str = None ,identifier : str = None , ntrip_format :str = None , format_detail : str = None ) -> None:

        self.mountpoint : str = mountpoint
        self.identifier :str = identifier
        self.ntrip_format : str = ntrip_format
        self.format_detail : str = format_detail
        self.carrier : Carrier
        self.nav_system : str
        self.network :str
        self.country :str
        self.latitude : float
        self.longitude : float
        self.nmea :str
        self.solution : Solution
        self.generator : str
        self.compr_encryp :str
        self.authentification : Authentication
        self.fee : Fee
        self.bitrate :str
        self.misc :str
