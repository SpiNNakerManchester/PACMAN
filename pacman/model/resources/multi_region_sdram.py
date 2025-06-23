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
from __future__ import annotations
from enum import Enum
import math
from typing import Any, Dict, Optional, TextIO, Union

import numpy
from typing_extensions import TypeAlias

from spinn_utilities.overrides import overrides

from .abstract_sdram import AbstractSDRAM
from .constant_sdram import ConstantSDRAM
from .variable_sdram import VariableSDRAM

_RegionKey: TypeAlias = Union[int, str, Enum]
_Value: TypeAlias = Union[int, float, numpy.integer, numpy.floating]


def _ceil(value: _Value) -> int:
    return math.ceil(value)


class MultiRegionSDRAM(AbstractSDRAM):
    """
    A resource for SDRAM that comes in regions.

    .. note::
        Adding or subtracting two MultiRegionSDRAM objects will be assumed to
        be an operation over multiple cores/placements so these functions
        return a VariableSDRAM object without the regions data.

        To add extra SDRAM costs for the same core/placement use the methods
        :py:meth:`add_cost` and :py:meth:`merge`.
    """

    __slots__ = (
        # The regions of SDRAM, each of which is an AbstractSDRAM
        "__regions",
        # The total cost of all the regions
        "_total")

    def __init__(self) -> None:
        self.__regions: Dict[_RegionKey, AbstractSDRAM] = {}
        self._total: AbstractSDRAM = ConstantSDRAM(0)

    @property
    def regions(self) -> dict[_RegionKey, AbstractSDRAM]:
        """
        The map from region identifiers to the amount of SDRAM required.
        """
        return self.__regions

    def add_cost(self, region: _RegionKey, fixed_sdram: _Value,
                 per_timestep_sdram: _Value = 0) -> None:
        """
        Adds the cost for the specified region.

        :param region: Key to identify the region
        :param fixed_sdram: The fixed cost for this region.
        :param per_timestep_sdram: The variable cost for this region is any
        """
        if per_timestep_sdram:
            self.nest(region, VariableSDRAM(
                _ceil(fixed_sdram), _ceil(per_timestep_sdram)))
        else:
            self.nest(region, ConstantSDRAM(_ceil(fixed_sdram)))

    def nest(self, region: _RegionKey, other: AbstractSDRAM) -> None:
        """
        Combines the other SDRAM cost, in a nested fashion.

        The totals for the new region are added to the total of this one.
        A new region is created summarising the cost of others.
        If other contains a regions which is the same as one in self they are
        *not* combined, but kept separate.

        :param region: Key to identify the summary region
        :param other:
            Another SDRAM model to make combine by nesting
        """
        self._total += other
        if region in self.__regions:
            if isinstance(other, MultiRegionSDRAM):
                r = self.__regions[region]
                if isinstance(r, MultiRegionSDRAM):
                    r.merge(other)
                else:
                    other.nest(region, r)
                    self.__regions[region] = other
            else:
                self.__regions[region] += other
        else:
            self.__regions[region] = other

    def merge(self, other: MultiRegionSDRAM) -> None:
        """
        Combines the other SDRAM costs keeping the region mappings.

        .. note::
            This method should only be called when combining cost for the same
            core/ placement. Use + to combine for different cores

        :param other: Another mapping of costs by region
        """
        self._total += other
        for region in other.regions:
            if region in self.regions:
                self.__regions[region] += other.regions[region]
            else:
                self.__regions[region] = other.regions[region]

    @overrides(AbstractSDRAM.report)
    def report(self, timesteps: Optional[int], indent: str = "",
               preamble: str = "", target: Optional[TextIO] = None) -> None:
        self._total.report(timesteps, indent, preamble, target)
        for region in self.__regions:
            self.__regions[region].report(
                timesteps, indent+"    ", str(region)+":", target)

    def get_total_sdram(self, n_timesteps: Optional[int]) -> int:
        """
        The total SDRAM.

        :param n_timesteps: number of timesteps to cost for
        :return:
        """
        return self._total.get_total_sdram(n_timesteps)

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, MultiRegionSDRAM):
            return self._total == other._total
        return self._total == other

    def __add__(self, other: AbstractSDRAM) -> AbstractSDRAM:
        """
        Combines this SDRAM resource with the other one and creates a new one.

        :param other: another SDRAM resource
        :return: a New AbstractSDRAM
        """
        return self._total + other

    @property
    def fixed(self) -> int:
        """
        The fixed SDRAM cost.
        """
        return self._total.fixed

    @property
    def per_timestep(self) -> float:
        """
        The extra SDRAM cost for each additional timestep.

        .. warning::
            May well be zero.
        """
        return self._total.per_timestep

    @property
    @overrides(AbstractSDRAM.short_str)
    def short_str(self) -> str:
        return f"Multi:{self._total.short_str}"
