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
from typing import Any, Dict, Optional, TextIO, Union

import numpy

from spinn_utilities.overrides import overrides
from pacman.exceptions import PacmanConfigurationException
from .abstract_sdram import AbstractSDRAM
from .constant_sdram import ConstantSDRAM
from .variable_sdram import VariableSDRAM


def _ceil(value: Union[int, float, numpy.integer, numpy.floating]) -> int:
    return math.ceil(value)


class SharedSDRAM(AbstractSDRAM):
    """
    Represents an amount of SDRAM used on a chip in the machine.

    This is split into cost for each core and ones for each chip
    """

    __slots__ = (
        # The amount of SDRAM per core
        "_per_core",
        # Map of extra shared SDRAM per Chip
        "_shared"
        )

    def __init__(self, shared: Dict[str, AbstractSDRAM],
                 per_core: Optional[AbstractSDRAM] = None) -> None:
        """
        Creates an SDRAM of both per_core and shared requirements.

        .. note::
            Each key must map GLOBALLY to the same SDRAM (or an equal one)
            It is recommended that a vertex use its label at the start the key

        :param shared:
            The sdram that will be allocated ONCE per Chip
            This is a dict of keys to sdram
        :param per_core:
            The amount of SDRAM that will be needed on every core.
        """
        # create a shallow copy
        self._shared = shared.copy()
        if per_core is None:
            self._per_core: AbstractSDRAM = ConstantSDRAM(0)
        else:
            self._per_core = per_core

    @overrides(AbstractSDRAM.get_total_sdram)
    def get_total_sdram(self, n_timesteps: Optional[int]) -> int:
        running = self._per_core.get_total_sdram(n_timesteps)
        for sdram in self._shared.values():
            running += sdram.get_total_sdram(n_timesteps)
        return running

    @property
    @overrides(AbstractSDRAM.fixed)
    def fixed(self) -> int:
        running = self._per_core.fixed
        for sdram in self._shared.values():
            running += sdram.fixed
        return running

    @property
    @overrides(AbstractSDRAM.per_timestep)
    def per_timestep(self) -> float:
        running = self._per_core.per_timestep
        for sdram in self._shared.values():
            running += sdram.per_timestep
        return running

    @overrides(AbstractSDRAM.__eq__)
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, SharedSDRAM):
            return False
        if self._per_core != other._per_core:
            return False
        return self._shared == other._shared

    @overrides(AbstractSDRAM.__add__)
    def __add__(self, other: AbstractSDRAM) -> AbstractSDRAM:
        if isinstance(other, (ConstantSDRAM, VariableSDRAM)):
            return SharedSDRAM(self._shared, self._per_core + other)
        elif isinstance(other, SharedSDRAM):
            shared = self._shared.copy()
            for key, value in other._shared.items():
                if key in shared:
                    if value != shared[key]:
                        raise PacmanConfigurationException(
                            f"Shared {key} has different values")
                else:
                    shared[key] = value
            return SharedSDRAM(shared, self._per_core + other._per_core)
        else:
            # MultiRegionSDRAM
            return other + self

    @overrides(AbstractSDRAM.report)
    def report(self, timesteps: Optional[int], indent: str = "",
               preamble: str = "", target: Optional[TextIO] = None) -> None:
        self._per_core.report(timesteps, indent, preamble, target)
        for key, sdram in self._shared.items():
            sdram.report(timesteps, indent+"    ", key+":", target)

    @property
    @overrides(AbstractSDRAM.short_str)
    def short_str(self) -> str:
        if self._per_core.fixed > 0 or self._per_core.per_timestep > 0:
            per_core = f"per-core: {self._per_core.short_str}"
        else:
            per_core = ""
        shared = ""
        for key, sdram in self._shared.items():
            if shared == "":
                shared = f" shared: {key}: {sdram.short_str}"
            else:
                shared += f", {key}: {sdram.short_str}"
        return per_core + shared
