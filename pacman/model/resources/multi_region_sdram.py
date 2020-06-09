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
from .variable_sdram import VariableSDRAM
from spinn_utilities.overrides import overrides
from pacman.exceptions import PacmanInvalidParameterException


class MultiRegionSDRAM(VariableSDRAM):
    """ A resource for SDRAM that comes in regions

        .. note:
        Adding or Subtracting two MultiRegionSDRAM objects will be assumed to
        be an operation over multiple cores/placements so these functions
        return a VariableSDRAM object without the regions data.

        To add extra SDRAM costs for the same core/placement use the method
        add_cost
        merge
    """

    __slots__ = [
        # The regions of SDRAM, each of which is an AbstractSDRAM
        "__regions"
    ]

    def __init__(self):
        super(MultiRegionSDRAM, self).__init__(0, 0)
        self.__regions = {}

    @property
    def regions(self):
        return self.__regions

    def add_cost(self, region, fixed_sdram, per_timestep_sdram=0):
        """
        Adds the cost for the specified region

        :param region: Key to identify the region
        :type region: int or String or enum
        :param int fixed_sdram: The fixed cost for this region.
        :param int per_timestep_sdram: The variable cost for this region is any
        """
        self._fixed_sdram = self._fixed_sdram + fixed_sdram
        self._per_timestep_sdram = \
            self._per_timestep_sdram + per_timestep_sdram
        if per_timestep_sdram:
            sdram = VariableSDRAM(fixed_sdram, per_timestep_sdram)
        else:
            sdram = ConstantSDRAM(fixed_sdram)
        if region in self.__regions:
            self.__regions[region] += sdram
        else:
            self.__regions[region] = sdram

    def nest(self, region, other):
        """
        Combines the other sdram cost, in a nested fashion.

        The totals for the new region are added to the total of this one.
        A new region is created summerizing the cost of others.
        If other contains a regions which is the same as one in self they are
            NOT combined, but kept seperate.

        :param region: Key to identify the summary region
        :param AbstractSDRAM other: Another sdram model to make combine by
            nesting
        """
        self._fixed_sdram = self._fixed_sdram + other.fixed
        self._per_timestep_sdram = \
            self._per_timestep_sdram + other.per_timestep
        if region in self.__regions:
            if isinstance(other, MultiRegionSDRAM):
                self.__regions[region].merge(other)
            else:
                self.__regions[region] += other
        else:
            self.__regions[region] = other

    def _check_mergable(self, other):
         if type(other) != type(self):
            raise PacmanInvalidParameterException(
                "other", other,
                "You can not nest a {} into a {}".format(
                    type(other), type(self)));

    def merge(self, other):
        """
        Combines the other sdram costs keeping the region mappings

        .. note:
            This method should only be called when combining cost for the same
            core/ placement. Use + to combine for different cores

        :param MultiRegionSDRAM other: Another mapping of costs by region
        """
        self._check_mergable(other)
        self._fixed_sdram = self._fixed_sdram + other.fixed
        self._per_timestep_sdram = \
            self._per_timestep_sdram + other.per_timestep
        for region in other.__regions:
            if region in self.__regions:
                self.__regions[region] += other.__regions[region]
            else:
                self.__regions[region] = other.__regions[region]

    @overrides(AbstractSDRAM.report)
    def report(self, timesteps, indent="", preamble="", target=None):
        super(MultiRegionSDRAM, self).report(
            timesteps, indent, preamble, target)
        for region in self.__regions:
            self.__regions[region].report(
                timesteps, indent+"    ", str(region)+":", target)
