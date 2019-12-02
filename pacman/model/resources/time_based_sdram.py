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

import math
from .abstract_sdram import AbstractSDRAM
from .constant_sdram import ConstantSDRAM
from pacman.exceptions import PacmanConfigurationException


class TimeBasedSDRAM(AbstractSDRAM):
    """ Represents an amount of SDRAM used on a chip in the machine.

    This is where the usage increase as the run time increases
    """

    __slots__ = [
        # The amount of SDRAM in bytes used no matter what
        "_fixed_sdram",
        # The amount of extra SDRAm used for each simtime us
        "_per_simtime_us"
    ]

    def __init__(
            self, fixed_sdram, per_simtime_us):
        """

        :param fixed_sdram: The amount of SDRAM in bytes
        :type fixed_sdram: int
        :param per_simtime_us: The amount of extra sdram per simtime us.
        Note: This needs only to be accurate at the timestep level.
        So may be simply per_timestep_sdram / timestep
        :type per_simtime_m: float
        """
        self._fixed_sdram = fixed_sdram
        self._per_simtime_us = per_simtime_us

    def get_sdram_for_simtime(self, time_in_us):
        if time_in_us is not None:
            return self._fixed_sdram + \
                   math.ceil(self._per_simtime_us * time_in_us)
        else:
            if self._per_simtime_us == 0:
                return self._fixed_sdram
            else:
                raise PacmanConfigurationException(
                    "Unable to run forever with a variable SDRAM cost")

    @property
    def fixed(self):
        return self._fixed_sdram

    @property
    def per_simtime_us(self):
        return self._per_simtime_us

    def __add__(self, other):
        if isinstance(other, (TimeBasedSDRAM, ConstantSDRAM)):
            return TimeBasedSDRAM(
                self.fixed + other.fixed,
                self.per_simtime_us + other.per_simtime_us)
        else:
            # The other is more complex so delegate to it
            return other.__add__(self)

    def __sub__(self, other):
        if isinstance(other, (TimeBasedSDRAM, ConstantSDRAM)):
            return TimeBasedSDRAM(
                self.fixed - other.fixed,
                self.per_simtime_us - other.per_simtime_us)
        else:
            # The other is more complex so delegate to it
            return other.sub_from(self)

    def sub_from(self, other):
        # Only Ever called from less complex so no type check required
        return TimeBasedSDRAM(
            other.fixed - self.fixed,
            other.per_simtime_us - self.per_simtime_us)
