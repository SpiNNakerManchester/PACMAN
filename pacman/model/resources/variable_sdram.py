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
from pacman.exceptions import PacmanConfigurationException


class VariableSDRAM(AbstractSDRAM):
    """ Represents an amount of SDRAM used on a chip in the machine.

    This is where the usage increase as the run time increases
    """

    __slots__ = [
        # The amount of SDRAM in bytes used no matter what
        "_fixed_sdram"
        # The amount of extra SDRAm used for each timestep
        "_per_timestep_sdram"
    ]

    def __init__(self, fixed_sdram, per_timestep_sdram):
        """
        :param int fixed_sdram:
            The amount of SDRAM (in bytes) that represents static overhead
        :param int per_timestep_sdram:
            The amount of SDRAM (in bytes) required per timestep.
            Often represents the space to record a timestep.
        """
        self._fixed_sdram = fixed_sdram
        self._per_timestep_sdram = per_timestep_sdram

    def get_total_sdram(self, n_timesteps):
        if n_timesteps is not None:
            return (self._fixed_sdram +
                    self._per_timestep_sdram * n_timesteps)
        if self._per_timestep_sdram == 0:
            return self._fixed_sdram
        raise PacmanConfigurationException(
            "Unable to run forever with a variable SDRAM cost")

    @property
    def fixed(self):
        return self._fixed_sdram

    @property
    def per_timestep(self):
        return self._per_timestep_sdram

    def __add__(self, other):
        return VariableSDRAM(
            self._fixed_sdram + other.fixed,
            self._per_timestep_sdram + other.per_timestep)

    def __sub__(self, other):
        return VariableSDRAM(
            self._fixed_sdram - other.fixed,
            self._per_timestep_sdram - other.per_timestep)

    def sub_from(self, other):
        return VariableSDRAM(
            other.fixed - self._fixed_sdram,
            other.per_timestep - self._per_timestep_sdram)
