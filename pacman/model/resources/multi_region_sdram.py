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
from spinn_utilities.overrides import overrides
from pacman.exceptions import PacmanInvalidParameterException
from .abstract_sdram import AbstractSDRAM
from .constant_sdram import ConstantSDRAM
from .variable_sdram import VariableSDRAM


class MultiRegionSDRAM(VariableSDRAM):
    """ A resource for SDRAM that comes in regions.

        .. note:
            Adding or Subtracting two :py:class:`MultiRegionSDRAM` objects will
            be assumed to be an operation over multiple cores/placements so
            these functions return a :py:class:`VariableSDRAM` object without
            the regions data.

            To add extra SDRAM costs for the same core/placement use the
            methods :py:meth:`add_cost` and :py:meth:`merge`, or
            :py:meth:`nest`.
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
        """ The regions of SDRAM, and how much space is allocated for each.

        :rtype: dict(int or str or enum, AbstractSDRAM)
        """
        return self.__regions

    def add_cost(self, region, fixed_sdram, per_timestep_sdram=0):
        """ Adds the cost for the specified region

        :param region: Key to identify the region
        :type region: int or str or enum
        :param fixed_sdram: The fixed cost for this region.
        :type fixed_sdram: int or numpy.integer
        :param per_timestep_sdram: The variable cost for this region is any.
        :type per_timestep_sdram: int or numpy.integer
        """
        self._fixed_sdram = self._fixed_sdram + fixed_sdram
        self._per_timestep_sdram = \
            self._per_timestep_sdram + per_timestep_sdram
        if per_timestep_sdram:
            sdram = VariableSDRAM(int(fixed_sdram), int(per_timestep_sdram))
        else:
            sdram = ConstantSDRAM(int(fixed_sdram))
        if region in self.__regions:
            self.__regions[region] += sdram
        else:
            self.__regions[region] = sdram

    def nest(self, region, other):
        """ Combines the other SDRAM cost, in a nested fashion.

        The totals for the new region are added to the total of this one.
        A new region is created summarising the cost of others.
        If other contains a regions which is the same as one in self they are
        *not* combined, but kept separate.

        :param region: Key to identify the summary region
        :type region: int or str or enum
        :param AbstractSDRAM other:
            Another SDRAM model to make combine by nesting
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
        """ Check that the two types being merge are possible.

        Currently only multi-region SDRAM of the same type (or sub-type) of
        :py:class:`MultiRegionSDRAM` can be merged.

        :param MultiRegionSDRAM other: Another SDRAM of the same type
        :raises PacmanInvalidParameterException:
            If the types do not support merge
        """
        if type(other) != type(self):
            raise PacmanInvalidParameterException(
                "other", other,
                "You can not nest a {} into a {}".format(
                    type(other), type(self)))

    def merge(self, other):
        """ Combines the other SDRAM costs keeping the region mappings

        Merge is only guaranteed to be possible between the same type/subtype
        of :py:class:`MultiRegionSDRAM`.

        .. note::
            This method should only be called when combining cost for the same
            core/placement. Use `+` to combine for different cores

        :param MultiRegionSDRAM other: Another mapping of costs by region
        :raises PacmanInvalidParameterException:
            If the types do not support merge
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
