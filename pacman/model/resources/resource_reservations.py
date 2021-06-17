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


class ResourceReservations(object):
    """ Container object for preallocated resources
    """

    __slots__ = [
        # Sdram to preallocate on all none ethernet Chips
        "_sdram_all",

        # sdram to preallocate for Ethernet Chips
        # This includes the values from _sdram_all
        "_sdram_ethernet",

        # Number of cores to preallocate on all none ethernet chips
        "_cores_all",

        # Number of cores to preallocate on ethernet chips
        # This includes the cores in cores_all
        "_cores_ethernet",

        # iptag resources to be perallocated on all everynets
        "_iptag_resources"]

    def __init__(self):
        self._sdram_all = ConstantSDRAM(0)
        self._sdram_ethernet = ConstantSDRAM(0)
        self._cores_all = 0
        self._cores_ethernet = 0
        self._iptag_resources = []

    @property
    def sdram_all(self):
        return self._sdram_all

    def add_sdram_all(self, extra):
        """
        Add extra sdram to preallocate on all chips including ethernets

        :param AbstractSDRAM extra: Additioanal sdram required
        """
        self._sdram_all += extra
        self._sdram_ethernet += extra

    @property
    def sdram_ethernet(self):
        return self._sdram_ethernet

    def add_sdram_ethernet(self, extra):
        """
        Add extra sdram to preallocate on ethernet chips

        :param AbstractSDRAM extra: Additioanal sdram required
        """
        self._sdram_ethernet += extra

    @property
    def specific_core_resources(self):
        return self._specific_core_resources

    @property
    def cores_all(self):
        return self._cores_all

    def add_cores_all(self, extra):
        """
        Add extra core requirement for all cores including ethernets

        :param int extra: number of extra cores
        """
        self._cores_all += extra
        self._cores_ethernet += extra

    @property
    def cores_ethernet(self):
        return self._cores_ethernet

    def add_cores_ethernet(self, extra):
        """
        Add extra core requirement for all cores including ethernets

        :param int extra: number of extra cores
        """
        self._cores_ethernet += extra

    @property
    def iptag_resources(self):
        return self._iptag_resources

    def add_iptag_resource(self, extra):
        """
        Adds an additional iptag resource to be reserved on all ethernet chips
        :param IPtagResource extraa:
        """
        self._iptag_resources.append(extra)
