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

from pacman.model.placements import Placements, Placement
from pacman.exceptions import PacmanPlaceException
from pacman.operations.placer_algorithms.radial_placer import RadialPlacer
from spinn_utilities.ordered_set import OrderedSet


def place_application_graph(machine, app_graph, plan_n_timesteps):
    """ Perform placement of an application graph on the machine.
        NOTE: app_graph must have been partitioned
    """

    # Track the space
    spaces = _Spaces(machine)

    # Keep placements
    placements = Placements()

    # Go through the application graph by application vertex
    for app_vertex in app_graph.vertices:

        # Always start each application vertex with a new chip
        next_chip, space = spaces.get_next_chip_and_space()

        same_chip_groups = app_vertex.splitter.get_same_chip_groups()

        # Go through the groups
        for vertices, sdram in same_chip_groups:
            sdram = sdram.get_total_sdram(plan_n_timesteps)
            n_cores = len(vertices)

            # If we can't use the next chip, use the next one after
            if not next_chip.is_space(n_cores, sdram):
                try:
                    next_chip = spaces.get_next_chip(space)
                except StopIteration:
                    raise PacmanPlaceException(
                        "Not enough space to place graph")

            # If we can't place now, it is an error
            if not next_chip.is_space(n_cores, sdram):
                raise PacmanPlaceException(
                    f"{n_cores} cores is too many, or SDRAM of {sdram}"
                    " is too much")

            # Otherwise place
            _place_on_chip(placements, vertices, sdram, next_chip)

    return placements


def _place_on_chip(placements, vertices, sdram, chip):
    for vertex in vertices:
        core = chip.use_next_core()
        placements.add_placement(Placement(vertex, chip.x, chip.y, core))
    chip.use_sdram(sdram)


class _ChipWithSpace(object):

    __slots__ = ["chip", "n_cores", "sdram"]

    def __init__(self, chip):
        self.chip = chip
        self.n_cores = chip.n_user_processors
        self.sdram = chip.sdram.size

    @property
    def x(self):
        return self.chip.x

    @property
    def y(self):
        return self.chip.y

    def is_space(self, n_cores, sdram):
        return self.n_cores >= n_cores and self.sdram >= sdram

    def use_sdram(self, sdram):
        self.sdram -= sdram

    def use_next_core(self):
        self.n_cores -= 1
        return self.chip.n_user_processors - self.n_cores


class _Spaces(object):

    __slots__ = ["__machine", "__chips", "__next_chip", "__used_chips"]

    def __init__(self, machine):
        self.__machine = machine
        self.__chips = iter(RadialPlacer._generate_radial_chips(machine))
        self.__next_chip = next(self.__chips)
        self.__used_chips = set()

    def get_next_chip_and_space(self):
        try:
            # Find an unused chip based radially from the boot chip
            while self.__next_chip in self.__used_chips:
                self.__next_chip = next(self.__chips)

            # Start a new space by finding all the chips that can be reached
            # from the start chip but have not been used
            self.__used_chips.add(self.__next_chip)
            chip = self.__machine.get_chip_at(*self.__next_chip)
            return _ChipWithSpace(chip), self.__usable_from_chip(chip)

        except StopIteration:
            raise PacmanPlaceException("No more chips to place on")

    def get_next_chip(self, space):
        next_x, next_y = space.pop()
        self.__used_chips.add((next_x, next_y))
        chip = self.__machine.get_chip_at(next_x, next_y)
        space.update(self.__usable_from_chip(chip))
        return _ChipWithSpace(chip)

    def __usable_from_chip(self, chip):
        chips = OrderedSet()
        for link in chip.router.links:
            chip_coords = (link.destination_x, link.destination_y)
            if chip_coords not in self.__used_chips:
                chips.add(chip_coords)
        return chips
