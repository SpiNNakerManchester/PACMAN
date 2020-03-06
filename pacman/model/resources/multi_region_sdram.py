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
from spinn_utilities.overrides import overrides


class MultiRegionSDRAM(AbstractSDRAM):
    """ A resource for SDRAM that comes in regions
    """

    __slots__ = [
        # The regions of SDRAM, each of which is an AbstractSDRAM
        "__regions"
    ]

    def __init__(self, regions):
        """

        :param regions: A list of AbstractSDRAM, one per "region" of SDRAM.
            The indices of the list are assumed to be the indices of the\
            regions; as such the list can include None objects, which are\
            assumed to be empty regions (regions with 0 SDRAM are also OK).
        """
        self.__regions = regions

    @property
    def regions(self):
        return self.__regions

    @overrides(AbstractSDRAM.get_total_sdram)
    def get_total_sdram(self, n_timesteps):
        return sum(r.get_total_sdram(n_timesteps) for r in self.__regions)

    @property
    @overrides(AbstractSDRAM.fixed)
    def fixed(self):
        return sum(r.fixed for r in self.__regions)

    @property
    @overrides(AbstractSDRAM.per_timestep)
    def per_timestep(self):
        return sum(r.per_timestep for r in self.__regions)

    @overrides(AbstractSDRAM.__add__)
    def __add__(self, other):
        if isinstance(other, MultiRegionSDRAM):
            self.__regions.extend(other.regions)
        else:
            self.__regions.append(other)

    @overrides(AbstractSDRAM.__sub__)
    def __sub__(self, other):
        raise NotImplementedError("Cannot subtract from a multi-region SDRAM")

    @overrides(AbstractSDRAM.sub_from)
    def sub_from(self, other):
        raise NotImplementedError("Cannot subtract from a multi-region SDRAM")
