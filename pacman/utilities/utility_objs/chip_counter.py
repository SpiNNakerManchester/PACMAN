# Copyright (c) 2021 The University of Manchester
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

from pacman.data import PacmanDataView


class ChipCounter(object):
    """ A counter of how many chips are needed to hold machine vertices.
        This does not look at the constraints of the vertices at all.
        The value produced will be a (hopefully) worst-case estimate and should
        not be used to decide failure in terms of space!
    """

    __slots__ = [
        # How many cores there are to be used on a chip
        "__n_cores_per_chip",

        # How much SDRAM there is to be used on a chip
        "__sdram_per_chip",

        # The number of cores free on the "current" chip
        "__cores_free",

        # The SDRAM free on the "current" chip
        "__sdram_free",

        # The number of chips used, including the current one
        "__n_chips"]

    def __init__(self, n_cores_per_chip=15, sdram_per_chip=100 * 1024 * 1024):
        self.__n_cores_per_chip = n_cores_per_chip
        self.__sdram_per_chip = sdram_per_chip
        self.__cores_free = 0
        self.__sdram_free = 0
        self.__n_chips = 0

    def add_core(self, resources):
        sdram = resources.get_total_sdram(
            PacmanDataView.get_plan_n_timestep())
        if self.__cores_free == 0 or self.__sdram_free < sdram:
            self.__n_chips += 1
            self.__cores_free = self.__n_cores_per_chip
            self.__sdram_free = self.__sdram_per_chip
        self.__cores_free -= 1
        self.__sdram_free -= sdram

    @property
    def n_chips(self):
        return self.__n_chips
