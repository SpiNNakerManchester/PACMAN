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

import math
from typing import Any, Optional, TextIO, Union

import numpy

from spinn_utilities.overrides import overrides
from pacman.exceptions import PacmanConfigurationException
from .abstract_sdram import AbstractSDRAM
from .constant_sdram import ConstantSDRAM


def _ceil(value: Union[int, float, numpy.integer, numpy.floating]) -> int:
    return math.ceil(value)


class VariableSDRAM(AbstractSDRAM):
    """
    Represents an amount of SDRAM used on a chip in the machine.

    This is where the usage increase as the run time increases
    """

    __slots__ = (
        # The amount of SDRAM in bytes used no matter what
        "_fixed_sdram",
        # The amount of extra SDRAm used for each timestep
        "_per_timestep_sdram")

    def __init__(self, fixed_sdram: int, per_timestep_sdram: float):
        """
        :param fixed_sdram:
            The amount of SDRAM (in bytes) that represents static overhead
        :param per_timestep_sdram:
            The amount of SDRAM (in bytes) required per timestep.
            Often represents the space to record a timestep.
        """
        self._fixed_sdram = int(fixed_sdram)
        self._per_timestep_sdram = float(per_timestep_sdram)

    @overrides(AbstractSDRAM.get_total_sdram)
    def get_total_sdram(self, n_timesteps: Optional[int]) -> int:
        if n_timesteps is not None:
            return _ceil(
                self._fixed_sdram + self._per_timestep_sdram * n_timesteps)
        if self._per_timestep_sdram == 0:
            return self._fixed_sdram
        raise PacmanConfigurationException(
            "Unable to run forever with a variable SDRAM cost")

    @property
    @overrides(AbstractSDRAM.fixed)
    def fixed(self) -> int:
        return self._fixed_sdram

    @property
    @overrides(AbstractSDRAM.per_timestep)
    def per_timestep(self) -> float:
        return self._per_timestep_sdram

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, VariableSDRAM):
            if other.fixed != self.fixed:
                return False
            else:
                return other.per_timestep == self.per_timestep
        elif isinstance(other, ConstantSDRAM):
            if self._per_timestep_sdram != 0:
                return False
            else:
                return other.fixed == self.fixed
        else:
            return False

    def __add__(self, other: AbstractSDRAM) -> AbstractSDRAM:
        if isinstance(other, ConstantSDRAM):
            return VariableSDRAM(
                self._fixed_sdram + other.fixed,  self._per_timestep_sdram)
        elif isinstance(other, VariableSDRAM):
            return VariableSDRAM(
                self._fixed_sdram + other.fixed,
                self._per_timestep_sdram + other.per_timestep)
        else:
            #  SharedSDRAM, MultiRegionSDRAM
            return other + self

    @overrides(AbstractSDRAM.report)
    def report(self, timesteps: Optional[int], indent: str = "",
               preamble: str = "", target: Optional[TextIO] = None) -> None:
        print(indent, preamble,
              f"Fixed {self._fixed_sdram} bytes "
              f"Per_timestep {self._per_timestep_sdram} bytes "
              f"for a total of {self.get_total_sdram(timesteps)}", file=target)

    @property
    @overrides(AbstractSDRAM.short_str)
    def short_str(self) -> str:
        return (f"fixed:{self._fixed_sdram} "
                f"per_timestep:{self._per_timestep_sdram}")
