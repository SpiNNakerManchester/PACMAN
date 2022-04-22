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


class ChipWithSpace(object):
    """ A chip with space for placement
    """

    __slots__ = ["chip", "cores", "sdram"]

    def __init__(self, chip, used_processors, used_sdram):
        self.chip = chip
        self.cores = set(p.processor_id for p in chip.processors
                         if not p.is_monitor)
        self.cores -= used_processors
        self.sdram = chip.sdram.size - used_sdram

    @property
    def x(self):
        return self.chip.x

    @property
    def y(self):
        return self.chip.y

    def is_space(self, n_cores, sdram):
        return len(self.cores) >= n_cores and self.sdram >= sdram

    def use_sdram(self, sdram):
        self.sdram -= sdram

    def use_next_core(self):
        core = next(iter(self.cores))
        self.cores.remove(core)
        return core
