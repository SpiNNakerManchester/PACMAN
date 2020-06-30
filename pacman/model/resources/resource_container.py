# Copyright (c) 2017-2019 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from .constant_sdram import ConstantSDRAM
from .cpu_cycles_per_tick_resource import CPUCyclesPerTickResource
from .dtcm_resource import DTCMResource


class ResourceContainer(object):
    """ Container for the types of resources so that ordering is not\
        a problem.
    """

    __slots__ = [

        # a DTCMResource object that reflects the amount of DTCM (in bytes)
        # used by a machine vertex on the SpiNNaker machine
        "_dtcm_usage",

        # a SDRAMResource object that reflects the amount of SDRAM (in bytes)
        # used by a machine vertex on the SpiNNaker machine
        "_sdram_usage",

        # a CPUCyclesPerTickResource object that reflects the number of
        # CPU cycles the machine vertex is expected to use on a SpiNNaker
        # machine
        "_cpu_cycles",

        # An iterable of IPtagResource objects that reflect the number of IP
        # tags a machine vertex is going to use on a SpiNNaker machine, as well
        # as the configuration data of said IP tags.
        "_iptags",

        # A iterable of ReverseIPtagResource objects that reflect the number of
        # Reverse IP tags a machine vertex is going to use on a SpiNNaker
        # machine, as well as the configuration data of said reverse IP tags.
        "_reverse_iptags"
    ]

    def __init__(
            self, dtcm=None, sdram=None, cpu_cycles=None, iptags=None,
            reverse_iptags=None):
        """
        :param dtcm: the amount of dtcm used
        :type dtcm: None or DTCMResource
        :param sdram: the amount of SDRAM used
        :type sdram: None or AbstractSDRAM
        :param cpu_cycles: the amount of CPU used
        :type cpu_cycles: None or CPUCyclesPerTickResource
        :param iptags: the IP tags required
        :type iptags: None or list(IPtagResource)
        :param reverse_iptags: the reverse IP tags required
        :type reverse_iptags: None or \
            list(SpecificBoardReverseIPtagResource)
        """
        # pylint: disable=too-many-arguments
        self._dtcm_usage = dtcm
        self._sdram_usage = sdram
        self._cpu_cycles = cpu_cycles
        self._iptags = iptags
        self._reverse_iptags = reverse_iptags

        # check for none resources
        if self._dtcm_usage is None:
            self._dtcm_usage = DTCMResource(0)
        if self._sdram_usage is None:
            self._sdram_usage = ConstantSDRAM(0)
        if self._cpu_cycles is None:
            self._cpu_cycles = CPUCyclesPerTickResource(0)
        if self._reverse_iptags is None:
            self._reverse_iptags = []
        if self._iptags is None:
            self._iptags = []

    @property
    def dtcm(self):
        return self._dtcm_usage

    @property
    def cpu_cycles(self):
        return self._cpu_cycles

    @property
    def sdram(self):
        return self._sdram_usage

    @property
    def iptags(self):
        return self._iptags

    @property
    def reverse_iptags(self):
        return self._reverse_iptags

    def extend(self, other):
        """
        :param ResourceContainer other:
        """
        # added CPU stuff
        self._cpu_cycles = CPUCyclesPerTickResource(
            self._cpu_cycles.get_value() + other.cpu_cycles.get_value())

        # added dtcm
        self._dtcm_usage = DTCMResource(
            self._dtcm_usage.get_value() + other.dtcm.get_value())

        # add SDRAM usage
        self._sdram_usage = self._sdram_usage + other.sdram

        # add IPtags
        self._iptags.extend(other.iptags)

        # add reverse IPtags
        self._reverse_iptags.extend(other.reverse_iptags)

    def __eq__(self, other):
        if self._dtcm_usage.get_value() != other.dtcm.get_value():
            return False
        if self._sdram_usage.fixed != other._sdram_usage.fixed:
            return False
        if self._sdram_usage.per_timestep != other._sdram_usage.per_timestep:
            return False
        if self._cpu_cycles.get_value() != other.cpu_cycles.get_value():
            return False
        if self._iptags != other._iptags:
            return False
        return self._reverse_iptags == other._reverse_iptags

    def __hash__(self):
        return hash((self._dtcm_usage.get_value(),
                     self._sdram_usage.fixed,
                     self._sdram_usage.per_timestep,
                     self._cpu_cycles.get_value(),
                     self._iptags,
                     self._reverse_iptags))

    def __ne__(self, other):
        return not self.__eq__(other)
