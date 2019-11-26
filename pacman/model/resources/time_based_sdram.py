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

from .abstract_sdram import AbstractSDRAM
from .constant_sdram import ConstantSDRAM
from pacman.exceptions import PacmanConfigurationException


class TimeBasedSDRAM(AbstractSDRAM):
    """ Represents an amount of SDRAM used on a chip in the machine.

    This is where the usage increase as the run time increases
    """

    __slots__ = [
        # The amount of SDRAM in bytes used no matter what
        "_fixed_sdram"
        # The amount of extra SDRAm used for each simtime ms
        "_per_simtime_ms"
    ]

    def __init__(
            self, fixed_sdram, per_simtime_ms):
        """

        :param fixed_sdram: The amount of SDRAM in bytes
        :type fixed_sdram: int
        :param per_simtime_ms: The amount of extra sdram per simtime ms.
        Note: This needs only to be accurate at the timestep level.
        So may be simply per_timestep_sdram / timestep
        :type per_simtime_m: float
        """
        self._fixed_sdram = fixed_sdram
        self._per_simtime_ms = per_simtime_ms

    def get_sdram_for_simtime(self, time_in_ms):
        if time_in_ms is not None:
            return self._fixed_sdram + \
                   (self._per_simtime_ms * time_in_ms)
        else:
            if self._per_simtime_ms == 0:
                return self._fixed_sdram
            else:
                raise PacmanConfigurationException(
                    "Unable to run forever with a variable SDRAM cost")

    @property
    def fixed(self):
        return self._fixed_sdram

    @property
    def per_simtime_ms(self):
        return self._per_simtime_ms

    def __add__(self, other):
        return TimeBasedSDRAM(
            self.fixed + other.fixed,
            self.per_simtime_ms + other.per_simtime_ms)

    def __sub__(self, other):
        return TimeBasedSDRAM(
            self.fixed - other.fixed,
            self.per_simtime_ms - other.per_simtime_ms)

    def sub_from(self, other):
        return TimeBasedSDRAM(
            other.fixed - self.fixed,
            other.per_simtime_ms - self.per_simtime_ms)
