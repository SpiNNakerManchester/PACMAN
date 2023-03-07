# Copyright (c) 2017 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from spinn_utilities.overrides import overrides
from pacman.exceptions import PacmanConfigurationException
from .abstract_sdram import AbstractSDRAM


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
        :param fixed_sdram:
            The amount of SDRAM (in bytes) that represents static overhead
        :type dtcm: int or numpy.integer
        :param per_timestep_sdram:
            The amount of SDRAM (in bytes) required per timestep.
            Often represents the space to record a timestep.
        :type per_timestep_sdram: float or numpy.float
        """
        self._fixed_sdram = int(fixed_sdram)
        self._per_timestep_sdram = float(per_timestep_sdram)

    @overrides(AbstractSDRAM.get_total_sdram)
    def get_total_sdram(self, n_timesteps):
        if n_timesteps is not None:
            return (self._fixed_sdram +
                    self._per_timestep_sdram * n_timesteps)
        if self._per_timestep_sdram == 0:
            return self._fixed_sdram
        raise PacmanConfigurationException(
            "Unable to run forever with a variable SDRAM cost")

    @property
    @overrides(AbstractSDRAM.fixed)
    def fixed(self):
        return self._fixed_sdram

    @property
    @overrides(AbstractSDRAM.per_timestep)
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

    @overrides(AbstractSDRAM.sub_from)
    def sub_from(self, other):
        return VariableSDRAM(
            other.fixed - self._fixed_sdram,
            other.per_timestep - self._per_timestep_sdram)

    @overrides(AbstractSDRAM.report)
    def report(self, timesteps, indent="", preamble="", target=None):
        print(indent, preamble,
              "Fixed {} bytes Per_timestep {} bytes for a total of {}".format(
                  self._fixed_sdram, self._per_timestep_sdram,
                  self.get_total_sdram(timesteps)), file=target)
