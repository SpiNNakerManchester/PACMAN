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
from .abstract_sdram import AbstractSDRAM
from .constant_sdram import ConstantSDRAM
from .variable_sdram import VariableSDRAM
from spinn_utilities.overrides import overrides


class MultiRegionSDRAM(VariableSDRAM):
    """
    A resource for SDRAM that comes in regions.

    .. note::
        Adding or subtracting two MultiRegionSDRAM objects will be assumed to
        be an operation over multiple cores/placements so these functions
        return a VariableSDRAM object without the regions data.

        To add extra SDRAM costs for the same core/placement use the methods
        :py:meth:`add_cost` and :py:meth:`merge`
    """

    __slots__ = [
        # The regions of SDRAM, each of which is an AbstractSDRAM
        "__regions"
    ]

    def __init__(self):
        super().__init__(0, 0)
        self.__regions = {}

    @property
    def regions(self):
        """
        The map from region identifiers to the to the amount of SDRAM required.

        :rtype: dict(int or str or enum, AbstractSDRAM)
        """
        return self.__regions

    def add_cost(self, region, fixed_sdram, per_timestep_sdram=0):
        """
        Adds the cost for the specified region.

        :param region: Key to identify the region
        :type region: int or str or enum
        :param fixed_sdram: The fixed cost for this region.
        :type fixed_sdram: int or numpy.integer
        :param per_timestep_sdram: The variable cost for this region is any
        :type per_timestep_sdram: int or numpy.integer
        """
        self._fixed_sdram += fixed_sdram
        self._per_timestep_sdram += per_timestep_sdram
        if per_timestep_sdram:
            sdram = VariableSDRAM(int(fixed_sdram), int(per_timestep_sdram))
        else:
            sdram = ConstantSDRAM(int(fixed_sdram))
        if region in self.__regions:
            self.__regions[region] += sdram
        else:
            self.__regions[region] = sdram

    def nest(self, region, other):
        """
        Combines the other SDRAM cost, in a nested fashion.

        The totals for the new region are added to the total of this one.
        A new region is created summarising the cost of others.
        If other contains a regions which is the same as one in self they are
        *not* combined, but kept separate.

        :param region: Key to identify the summary region
        :type region: int or str or enum
        :param AbstractSDRAM other:
            Another SDRAM model to make combine by nesting
        """
        self._fixed_sdram += other.fixed
        self._per_timestep_sdram += other.per_timestep
        if region in self.__regions:
            if isinstance(other, MultiRegionSDRAM):
                if isinstance(self.__regions[region], MultiRegionSDRAM):
                    self.__regions[region].merge(other)
                else:
                    old = self.__regions[region]
                    other.add_cost(region, old.fixed, old.per_timestep)
                    self.__regions[region] = other
            else:
                self.__regions[region] += other
        else:
            self.__regions[region] = other

    def merge(self, other):
        """
        Combines the other SDRAM costs keeping the region mappings.

        .. note::
            This method should only be called when combining cost for the same
            core/ placement. Use + to combine for different cores

        :param MultiRegionSDRAM other: Another mapping of costs by region
        """
        self._fixed_sdram += other.fixed
        self._per_timestep_sdram += other.per_timestep
        for region in other.regions:
            if region in self.regions:
                self.__regions[region] += other.regions[region]
            else:
                self.__regions[region] = other.regions[region]

    @overrides(AbstractSDRAM.report)
    def report(self, timesteps, indent="", preamble="", target=None):
        super().report(timesteps, indent, preamble, target)
        for region in self.__regions:
            self.__regions[region].report(
                timesteps, indent+"    ", str(region)+":", target)
