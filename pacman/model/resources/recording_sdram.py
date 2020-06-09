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
from .with_malloc_sdram import WithMallocSdram
from spinn_utilities.overrides import overrides
from pacman.utilities.constants import SARK_PER_MALLOC_SDRAM_USAGE


class RecordingSDRAM(WithMallocSdram):

    @property
    @overrides(WithMallocSdram.malloc_cost)
    def malloc_cost(self):
        return SARK_PER_MALLOC_SDRAM_USAGE * len(self.regions)

    def add_cost(self, region, fixed_sdram, per_timestep_sdram=0):
        super(RecordingSDRAM, self).add_cost(
            region, fixed_sdram, per_timestep_sdram)
        self._fixed_sdram += SARK_PER_MALLOC_SDRAM_USAGE

    def nest(self, region, other):
        super(RecordingSDRAM, self).nest(region, other)
        self._fixed_sdram += SARK_PER_MALLOC_SDRAM_USAGE
