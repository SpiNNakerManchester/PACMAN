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
from pacman.utilities.constants import SARK_PER_MALLOC_SDRAM_USAGE
from .with_malloc_sdram import WithMallocSdram


class RecordingSDRAM(WithMallocSdram):
    """ A resource for SDRAM that comes in Data Recording regions and\
        have malloc costs. The SpiNNaker tools assume that the data written\
        into this space will form a stream of information (events or recorded\
        values) and will concatenate them into a single stream for processing\
        at higher levels of the code. Non-streamed data should not use this\
        resource.

        Handles all the recording regions for a single core.
        Currently malloc cost is added for each region as all regions are
        malloced separately.

        The malloc cost will be automatically added to the total costs,
        but is not part of any of the regions and reported after a subtotal.

        .. note::
            Adding or subtracting two :py:class:`MultiRegionSDRAM` objects will
            be assumed to be an operation over multiple cores/placements so
            these functions return a :py:class:`VariableSDRAM` object without
            the regions data.

            To add extra SDRAM costs for the same core/placement use the method
            :py:meth:`add_cost`, :py:meth:`~.MultiRegionSDRAM.merge` (but only
            of another :py:class:`RecordingSDRAM`), or :py:meth:`nest` (but
            only of a :py:class:`MultiRegionSDRAM` without malloc).
    """

    @property
    @overrides(WithMallocSdram.malloc_cost)
    def malloc_cost(self):
        return SARK_PER_MALLOC_SDRAM_USAGE * len(self.regions)

    @overrides(WithMallocSdram.add_cost)
    def add_cost(self, region, fixed_sdram, per_timestep_sdram=0):
        super(RecordingSDRAM, self).add_cost(
            region, fixed_sdram, per_timestep_sdram)
        self._fixed_sdram += SARK_PER_MALLOC_SDRAM_USAGE

    @overrides(WithMallocSdram.nest)
    def nest(self, region, other):
        super(RecordingSDRAM, self).nest(region, other)
        self._fixed_sdram += SARK_PER_MALLOC_SDRAM_USAGE
