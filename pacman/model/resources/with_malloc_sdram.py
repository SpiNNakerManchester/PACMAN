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
from six import add_metaclass, print_
from .abstract_sdram import AbstractSDRAM
from .multi_region_sdram import MultiRegionSDRAM
from spinn_utilities.overrides import overrides
from spinn_utilities.abstract_base import (
    AbstractBase, abstractproperty)
from pacman.exceptions import PacmanInvalidParameterException


@add_metaclass(AbstractBase)
class WithMallocSdram(MultiRegionSDRAM):
    """ A resource for SDRAM that comes in regions and has malloc costs

        .. note:
        Adding or Subtracting two MultiRegionSDRAM objects will be assumed to
        be an operation over multiple cores/placements so these functions
        return a VariableSDRAM object without the regions data.

        To add extra SDRAM costs for the same core/placement use the method
        add_cost
        merge
    """

    @abstractproperty
    def malloc_cost(self):
        """
        The malloc cost which is included in the total and in the regions
        property, but not in the _reg
        :return: The cost to malloc for these regions
        """

    def nest(self, region, other):
        # Only nest if other a simple MultiRegionSDRAM
         if other.__class__ != MultiRegionSDRAM:
            raise PacmanInvalidParameterException(
                "other", other,
                "You can not nest a {} into a {}".format(
                    other.__class__.__name__, MultiRegionSDRAM.__name__));
         super(WithMallocSdram, self).nest(region, other)

    @overrides(AbstractSDRAM.report)
    def report(self, timesteps, indent="", preamble="", target=None):
        super(WithMallocSdram, self).report(
            timesteps, indent, preamble, target)
        print_(indent+"    ", preamble,
               "Malloc cost {} bytes".format(self._malloc), file=target)
        print_(indent+"    ", preamble,
               "Regions Fixed {} bytes Per_timestep {} bytes for a total of {}"
               "".format(
                   self._fixed_sdram - self.malloc_cost,
                   self._per_timestep_sdram,
                   self.get_total_sdram(timesteps) - self.malloc_cost),
               file=target)
        for region in self.__regions:
            self.__regions[region].report(
                timesteps, indent+"        ", str(region)+":", target)
