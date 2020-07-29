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
from spinn_utilities.overrides import overrides
from spinn_utilities.abstract_base import (
    AbstractBase, abstractproperty)
from pacman.exceptions import PacmanInvalidParameterException
from .abstract_sdram import AbstractSDRAM
from .multi_region_sdram import MultiRegionSDRAM


@add_metaclass(AbstractBase)
class WithMallocSdram(MultiRegionSDRAM):
    """ A resource for SDRAM that comes in regions and has malloc costs

        The malloc cost will be automatically added to the total costs,
        but is not part of any of the regions and reported after a subtotal.

        .. note::
            Adding or subtracting two :py:class:`MultiRegionSDRAM` objects will
            be assumed to be an operation over multiple cores/placements so
            these functions return a :py:class:`VariableSDRAM` object without
            the regions data.

            To add extra SDRAM costs for the same core/placement use the
            methods :py:meth:`~.MultiRegionSDRAM.add_cost`,
            :py:meth:`~.MultiRegionSDRAM.merge` (but only for a
            :py:class:`MultiRegionSDRAM` of the same type/malloc), or
            :py:meth:`nest` (but only of a :py:class:`MultiRegionSDRAM` without
            malloc)
    """

    @abstractproperty
    def malloc_cost(self):
        """ The malloc cost which is included in the total and in the regions\
            property, but not in the regions.

        :return: The automatically added cost to malloc for these regions,
            in bytes
        :rtype: int
        """

    @overrides(MultiRegionSDRAM.nest)
    def nest(self, region, other):
        # Only nest if other is simple MultiRegionSDRAM
        if other.__class__ != MultiRegionSDRAM:
            raise PacmanInvalidParameterException(
                "other", other,
                "You can not nest a {} into a {}".format(
                    other.__class__.__name__, MultiRegionSDRAM.__name__))
        super(WithMallocSdram, self).nest(region, other)

    @overrides(AbstractSDRAM.report)
    def report(self, timesteps, indent="", preamble="", target=None):
        super(WithMallocSdram, self).report(
            timesteps, indent, preamble, target)
        print_(indent+"   ", preamble,
               "Malloc cost {} bytes".format(self.malloc_cost), file=target)
        print_(indent+"   ", preamble,
               "Regions subtotal: Fixed {} bytes Per_timestep {} "
               "bytes for a total of {}".format(
                   self._fixed_sdram - self.malloc_cost,
                   self._per_timestep_sdram,
                   self.get_total_sdram(timesteps) - self.malloc_cost),
               file=target)
