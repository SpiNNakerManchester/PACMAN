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
from .constant_sdram import ConstantSDRAM
from .variable_sdram import VariableSDRAM


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
        """

        :param regions: A dict of AbstractSDRAM, one per "region" of SDRAM.

        """
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
        :param int fixed_sdram: The fixed cost for this region
        :param int per_timestep_sdram: The vaariable cost for this region is any
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

    def merge(self, other):
        """
        Combines the other sdram costs keeping the region mappings

        .. note:
            This method should only be called when combining cost for the same
            core/ placement. Use + to combine for different cores

        :param MultiRegionSDRAM other: Another mapping of costs by region
        """
        for region in other.__regions:
            previous = other.__regions[region]
            if region in self.__regions:
                self.__regions[region] += previous
            else:
                self.__regions[region] = previous
            self._fixed_sdram = self._fixed_sdram + previous.fixed
            self._per_timestep_sdram = \
                self._per_timestep_sdram + previous.per_timestep
