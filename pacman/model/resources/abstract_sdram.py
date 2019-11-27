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

from six import add_metaclass
from spinn_utilities.abstract_base import (
    AbstractBase, abstractmethod, abstractproperty)


@add_metaclass(AbstractBase)
class AbstractSDRAM(object):
    """ Represents an amount of SDRAM used on a chip in the machine.
    """

    @abstractmethod
    def get_sdram_for_simtime(self, time_in_ms):
        """
        The total SDRAM need to run for this amount of time/simtime

        Warning: This method is guaranteed to produce accurate results if the\
        time is a multiple of the timestep.  Best is to use a time_in_ms which
        is a multple of all different timesteps used.

        This allows costed elements like vertexes and graph to calculate their
        per_ms_sdram as their per_timestep_sdram / their timestep.
        The implementations of this method should round up to the nearest int.

        :param time_in_ms The simulation time in ms for which space should
        be saved. A None value will be considered run forever
        :type time_in_ms: int or None
        :rtype: int
        raises: PacmanConfigurationException if a None time_in_ms (run forever)
        is requested and there is a variable sdram requirement.,
        """

    def get_total_sdram(self, n_timesteps):
        # Hack to not brek to much at once
        if n_timesteps is None:
            return self.fixed
        else:
            return self.fixed + self.per_simtime_ms * 1000 * n_timesteps

    @abstractmethod
    def __add__(self, other):
        """
        Combines this SDRAM resource with the other one and creates a new one

        :param other: another SDRAM resource
        :type other: ~.AbstractSDRAM
        :return: a New AbstractSDRAM
        :rtype: ~.AbstractSDRAM
        """

    @abstractmethod
    def __sub__(self, other):
        """ Creates a new SDRAM which is this one less the other

        :param other: another SDRAM resource
        :type other: ~.AbstractSDRAM
        :return: a New AbstractSDRAM
        :rtype: ~.AbstractSDRAM
        """

    @abstractmethod
    def sub_from(self, other):
        """ Creates a new SDRAM which is the other less this one

        :param other: another  SDRAM resource
        :type other: ~.AbstractSDRAM
        :return: a New AbstractSDRAM
        :rtype: ~.AbstractSDRAM
        """

    @abstractproperty
    def fixed(self):
        """ Returns the fixed SDRAM cost
        """

    @abstractproperty
    def per_simtime_ms(self):
        """ Returns extra SDRAM cost for each additional ms of simtime

        Warning: SDram required is only guaranteed to produce accurate\
        results if the time is a multiple of the timestep.
        Best is to use a time_in_ms which is a multple of all different \
        timesteps used.

        The value returned by this method may will probably just be the
        per_timestep_sdram / timestep.
        """

    @property
    def per_timestep(self):
        # Hack to not break too much at once
        return self.per_simtime_ms * 1000
