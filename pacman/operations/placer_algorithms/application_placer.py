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
from pacman.exceptions import (
    PacmanPlaceException, PacmanConfigurationException)
from pacman.utilities.utility_calls import locate_constraints_of_type
from pacman.model.constraints.placer_constraints import ChipAndCoreConstraint
from spinn_utilities.ordered_set import OrderedSet
from spinn_utilities.progress_bar import ProgressBar
from tempfile import mkstemp
from os import fdopen


def place_application_graph(
        machine, app_graph, plan_n_timesteps, system_placements):
    """ Perform placement of an application graph on the machine.
        NOTE: app_graph must have been partitioned
    """

    # Track the space
    spaces = _Spaces(machine, system_placements, plan_n_timesteps)

    # Keep placements
    placements = Placements(system_placements)

    # Keep track of how many times we had to retry placing (usually due to
    # odd chip space being left)
    retries = 0

    # Go through the application graph by application vertex
    progress = ProgressBar(app_graph.n_vertices, "Placing Vertices")
    for app_vertex in progress.over(app_graph.vertices):

        # Try placements from the next chip, but try again if fails
        placed = False
        while not placed:
            try:

                same_chip_groups = app_vertex.splitter.get_same_chip_groups()

                if not same_chip_groups:
                    placed = True
                    break

                # Always start each application vertex with a new chip.  If
                # this fails, it will be fatal i.e. out of space
                try:
                    next_chip, space = spaces.get_next_chip_and_space()
                except PacmanPlaceException as e:
                    _place_error(
                        app_graph, placements, system_placements, e, retries)

                placements_to_make = list()

                # Go through the groups
                for vertices, sdram in same_chip_groups:
                    vertices_to_place = list()
                    for vertex in vertices:
                        if not placements.is_vertex_placed(vertex):
                            vertices_to_place.append(vertex)
                    sdram = sdram.get_total_sdram(plan_n_timesteps)
                    n_cores = len(vertices_to_place)

                    if _do_constraints(vertices_to_place, placements):
                        continue

                    # Try to find a chip with space; this might result in a
                    # SpaceExceededException
                    while not next_chip.is_space(n_cores, sdram):
                        next_chip = spaces.get_next_chip(space)

                    # If this worked, store placements to be made
                    _store_on_chip(
                        placements_to_make, vertices_to_place, sdram,
                        next_chip)

                # Now make the placements having confirmed all can be done
                placements.add_placements(placements_to_make)
                placed = True
            except _SpaceExceededException:
                # This might happen while exploring a space; this may not be
                # fatal since the last space might have just been bound by
                # existing placements, and there might be bigger spaces out
                # there to use
                retries += 1

    if retries > 0:
        print(f"Warning: Retried {retries} times")

    return placements


def _place_error(
        app_graph, placements, system_placements, exception, retries):
    app_vertex_count = 0
    vertex_count = 0
    n_vertices = 0
    for app_vertex in app_graph.vertices:
        same_chip_groups = app_vertex.splitter.get_same_chip_groups()
        app_vertex_placed = True
        found_placed_cores = False
        for vertices, _sdram in same_chip_groups:
            if placements.is_vertex_placed(vertices[0]):
                found_placed_cores = True
            elif found_placed_cores:
                vertex_count += len(vertices)
                n_vertices = len(same_chip_groups)
                app_vertex_placed = False
                break
            else:
                app_vertex_placed = False
                break
        if not app_vertex_placed and not found_placed_cores:
            app_vertex_count += 1

    fd, report_file = mkstemp(suffix=".rpt")
    with fdopen(fd, 'w') as f:
        f.write(f"{app_vertex_count} of {app_graph.n_vertices}"
                " application vertices placed.\n")
        f.write(f"    Could not place {vertex_count} of {n_vertices} in the"
                " last app vertex\n\n")
        for x, y in placements.chips_with_placements:
            first = True
            for placement in placements.placements_on_chip(x, y):
                if system_placements.is_vertex_placed(placement.vertex):
                    continue
                if first:
                    f.write(f"Chip ({x}, {y}):\n")
                    first = False
                f.write(f"    Processor {placement.p}:"
                        f" Vertex {placement.vertex}\n")
            if not first:
                f.write("\n")

    raise PacmanPlaceException(
        f" {exception}."
        f" Retried {retries} times."
        f" Report written to {report_file}.")


class _SpaceExceededException(Exception):
    pass


def _do_constraints(vertices, placements):
    x = None
    y = None
    for vertex in vertices:
        constraints = locate_constraints_of_type(
            vertex.constraints, ChipAndCoreConstraint)
        for constraint in constraints:
            if ((x is not None and constraint.x != x) or
                    (y is not None and constraint.y != y)):
                raise PacmanConfigurationException(
                    "Multiple conflicting constraints!")
            if constraint.p is not None:
                raise PacmanConfigurationException(
                    "This placer cannot handle core constraints")
            x = constraint.x
            y = constraint.y
    if x is not None or y is not None:
        next_core = placements.n_placements_on_chip(x, y) + 1
        for vertex in vertices:
            placements.add_placement(Placement(vertex, x, y, next_core))
            next_core += 1
        return True
    return False


def _store_on_chip(placements_to_make, vertices, sdram, chip):
    for vertex in vertices:
        core = chip.use_next_core()
        placements_to_make.append(Placement(vertex, chip.x, chip.y, core))
    chip.use_sdram(sdram)


class _ChipWithSpace(object):

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


class _Spaces(object):

    __slots__ = ["__machine", "__chips", "__next_chip", "__used_chips",
                 "__system_placements", "__plan_n_timesteps"]

    def __init__(self, machine, system_placements, plan_n_timesteps):
        self.__machine = machine
        self.__system_placements = system_placements
        self.__plan_n_timesteps = plan_n_timesteps
        self.__chips = iter(_chip_order(machine))
        self.__next_chip = next(self.__chips)
        self.__used_chips = set()

    def __cores_and_sdram(self, x, y):
        on_chip = self.__system_placements.placements_on_chip(x, y)
        cores_used = {p.p for p in on_chip}
        sdram_used = sum(
            p.vertex.resources_required.sdram.get_total_sdram(
                self.__plan_n_timesteps) for p in on_chip)
        return cores_used, sdram_used

    def get_next_chip_and_space(self):
        try:
            # Find an unused chip based radially from the boot chip
            while self.__next_chip in self.__used_chips:
                self.__next_chip = next(self.__chips)

            # Start a new space by finding all the chips that can be reached
            # from the start chip but have not been used
            self.__used_chips.add(self.__next_chip)
            chip = self.__machine.get_chip_at(*self.__next_chip)
            cores_used, sdram_used = self.__cores_and_sdram(chip.x, chip.y)
            return (_ChipWithSpace(chip, cores_used, sdram_used),
                    self.__usable_from_chip(chip))

        except StopIteration:
            raise PacmanPlaceException(
                f"No more chips to place on; {self.n_chips_used} of "
                f"{self.__machine.n_chips} used")

    def get_next_chip(self, space):
        if not space:
            raise _SpaceExceededException(
                "No more chips to place on in this space; "
                f"{self.n_chips_used} of {self.__machine.n_chips} used")
        next_x, next_y = space.pop(last=False)
        self.__used_chips.add((next_x, next_y))
        chip = self.__machine.get_chip_at(next_x, next_y)
        space.update(self.__usable_from_chip(chip))
        cores_used, sdram_used = self.__cores_and_sdram(chip.x, chip.y)
        return _ChipWithSpace(chip, cores_used, sdram_used)

    @property
    def n_chips_used(self):
        return len(self.__used_chips)

    def __usable_from_chip(self, chip):
        chips = OrderedSet()
        for link in chip.router.links:
            chip_coords = (link.destination_x, link.destination_y)
            if chip_coords not in self.__used_chips:
                chips.add(chip_coords)
        return chips


def _chip_order(machine):
    for x in range(machine.max_chip_x + 1):
        for y in range(machine.max_chip_y + 1):
            if machine.is_chip_at(x, y):
                yield((x, y))
