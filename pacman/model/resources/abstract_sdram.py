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

from spinn_utilities.abstract_base import (
    AbstractBase, abstractmethod, abstractproperty)


class AbstractSDRAM(object, metaclass=AbstractBase):
    """ Represents an amount of SDRAM used on a chip in the machine.
    """

    @abstractmethod
    def get_total_sdram(self, n_timesteps):
        """
        The total SDRAM.

        :param int n_timesteps: number of timesteps to cost for
        :return:
        """

    @abstractmethod
    def __add__(self, other):
        """
        Combines this SDRAM resource with the other one and creates a new one

        :param AbstractSDRAM other: another SDRAM resource
        :return: a New AbstractSDRAM
        :rtype: AbstractSDRAM
        """

    @abstractmethod
    def __sub__(self, other):
        """ Creates a new SDRAM which is this one less the other

        :param AbstractSDRAM other: another SDRAM resource
        :return: a New AbstractSDRAM
        :rtype: AbstractSDRAM
        """

    @abstractmethod
    def sub_from(self, other):
        """ Creates a new SDRAM which is the other less this one

        :param AbstractSDRAM other: another SDRAM resource
        :return: a New AbstractSDRAM
        :rtype: AbstractSDRAM
        """

    @abstractproperty
    def fixed(self):
        """ Returns the fixed SDRAM cost
        """

    @abstractproperty
    def per_timestep(self):
        """ Returns extra SDRAM cost for each additional timestep

        .. warning::
            May well be zero.
        """

    def __eq__(self, other):
        if not isinstance(other, AbstractSDRAM):
            return False
        if other.fixed != self.fixed:
            return False
        return other.per_timestep == self.per_timestep

    @abstractmethod
    def report(self, timesteps, indent="", preamble="", target=None):
        """ Writes a description of this SDRAM to the target.

        :param int timesteps: Number of timesteps to do total cost for
        :param str indent: Text at the start of this and all children
        :param str preamble:
            Additional text at the start but not in children
        :param file target: Where to write the output.
            ``None`` is standard print
        """
