# Copyright (c) 2021 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import numpy
import os

from spinn_utilities.config_holder import get_config_bool, get_config_str
from spinn_utilities.log import FormatAdapter
from spinn_utilities.ordered_set import OrderedSet
from spinn_utilities.progress_bar import ProgressBar

from pacman.data import PacmanDataView
from pacman.model.placements import Placements, Placement
from pacman.model.graphs import AbstractVirtual
from pacman.exceptions import (
    PacmanPlaceException, PacmanConfigurationException)

logger = FormatAdapter(logging.getLogger(__name__))


def place_application_graph(system_placements):
    """
    Perform placement of an application graph on the machine.

    .. note:

        app_graph must have been partitioned
    """

    # Track the placements and  space
    placements = Placements(system_placements)
    # board_colours = dict()

    machine = PacmanDataView.get_machine()
    plan_n_timesteps = PacmanDataView.get_plan_n_timestep()
    spaces = _Spaces(machine, placements, plan_n_timesteps)

    # Go through the application graph by application vertex
    progress = ProgressBar(
        PacmanDataView.get_n_vertices(), "Placing Vertices")
    for app_vertex in progress.over(PacmanDataView.iterate_vertices()):
        spaces.restore_chips()

        # Try placements from the next chip, but try again if fails
        placed = False
        while not placed:
            chips_attempted = list()
            try:

                same_chip_groups = app_vertex.splitter.get_same_chip_groups()

                if not same_chip_groups:
                    placed = True
                    break

                # Start a new space
                try:
                    next_chip_space, space = spaces.get_next_chip_and_space()
                except PacmanPlaceException as e:
                    _place_error(
                        placements, system_placements, e,  plan_n_timesteps,
                        machine)
                logger.debug(f"Starting placement from {next_chip_space}")

                placements_to_make = list()

                # Go through the groups
                last_chip_space = None
                for vertices, sdram in same_chip_groups:
                    vertices_to_place = list()
                    for vertex in vertices:
                        # No need to place virtual vertices
                        if isinstance(vertex, AbstractVirtual):
                            continue
                        if not placements.is_vertex_placed(vertex):
                            vertices_to_place.append(vertex)
                    sdram = sdram.get_total_sdram(plan_n_timesteps)
                    n_cores = len(vertices_to_place)

                    if _do_fixed_location(vertices_to_place, sdram, placements,
                                          machine, next_chip_space):
                        continue

                    # Try to find a chip with space; this might result in a
                    # SpaceExceededException
                    while not next_chip_space.is_space(n_cores, sdram):
                        next_chip_space = spaces.get_next_chip_space(
                            space, last_chip_space)
                        last_chip_space = None

                    # If this worked, store placements to be made
                    last_chip_space = next_chip_space
                    chips_attempted.append(next_chip_space.chip)
                    _store_on_chip(
                        placements_to_make, vertices_to_place, sdram,
                        next_chip_space)

                # Now make the placements having confirmed all can be done
                placements.add_placements(placements_to_make)
                placed = True
                logger.debug(f"Used {chips_attempted}")
            except _SpaceExceededException:
                # This might happen while exploring a space; this may not be
                # fatal since the last space might have just been bound by
                # existing placements, and there might be bigger spaces out
                # there to use
                logger.debug(f"Failed, saving {chips_attempted}")
                spaces.save_chips(chips_attempted)
                chips_attempted.clear()

    if get_config_bool("Reports", "draw_placements"):
        _draw_placements(placements, system_placements)

    return placements


def _place_error(
        placements, system_placements, exception, plan_n_timesteps,
        machine):
    unplaceable = list()
    vertex_count = 0
    n_vertices = 0
    for app_vertex in PacmanDataView.iterate_vertices():
        same_chip_groups = app_vertex.splitter.get_same_chip_groups()
        app_vertex_placed = True
        found_placed_cores = False
        for vertices, _sdram in same_chip_groups:
            if isinstance(vertices[0], AbstractVirtual):
                break
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
        if not app_vertex_placed:
            unplaceable.append(app_vertex)

    report_file = os.path.join(
        PacmanDataView.get_run_dir_path(), "placements_error.txt")
    with open(report_file, 'w', encoding="utf-8") as f:
        f.write(f"Could not place {len(unplaceable)} of "
                f"{PacmanDataView.get_n_vertices()} application vertices.\n")
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
        f.write("\n")
        f.write("Not placed:\n")
        for app_vertex in unplaceable:
            f.write(f"Vertex: {app_vertex}\n")
            same_chip_groups = app_vertex.splitter.get_same_chip_groups()
            for vertices, sdram in same_chip_groups:
                f.write(f"    Group of {len(vertices)} vertices uses "
                        f"{sdram.get_total_sdram(plan_n_timesteps)} "
                        "bytes of SDRAM:\n")
                for vertex in vertices:
                    f.write(f"        Vertex {vertex}")
                    if placements.is_vertex_placed(vertex):
                        plce = placements.get_placement_of_vertex(vertex)
                        f.write(f" (placed at {plce.x}, {plce.y}, {plce.p})")
                    f.write("\n")

        f.write("\n")
        f.write("Unused chips:\n")
        for x, y in machine.chip_coordinates:
            n_placed = placements.n_placements_on_chip(x, y)
            system_placed = system_placements.n_placements_on_chip(x, y)
            if n_placed - system_placed == 0:
                n_procs = machine.get_chip_at(x, y).n_user_processors
                f.write(f"    {x}, {y} ({n_procs - system_placed}"
                        " free cores)\n")

    if get_config_bool("Reports", "draw_placements_on_error"):
        _draw_placements(placements, system_placements)

    raise PacmanPlaceException(
        f" {exception}."
        f" Report written to {report_file}.")


def _next_colour():
    """
    Get the next (random) RGB colour to use for a vertex for placement drawings

    :rtype: tuple(int, int, int)
    """
    return tuple(numpy.concatenate(
        (numpy.random.choice(range(256), size=3) / 256, [1.0])))


def _draw_placements(placements, system_placements):
    try:
        # spinner as graphical library so
        # pylint: disable=import-error
        from spinner.scripts.contexts import PNGContextManager
        from spinner.diagrams.machine_map import (
            get_machine_map_aspect_ratio, draw_machine_map)
        from spinner import board
        from collections import defaultdict
        import math
    except ImportError:
        logger.exception(
            "Unable to draw placements as no spinner install found")
        return

    report_file = os.path.join(
        PacmanDataView.get_run_dir_path(), "placements_error.png")

    # Colour the boards by placements
    unused = (0.5, 0.5, 0.5, 1.0)
    vertex_colours = defaultdict(_next_colour)
    board_colours = dict()
    machine = PacmanDataView.get_machine()
    for x, y in machine.chip_coordinates:
        if (placements.n_placements_on_chip(x, y) ==
                system_placements.n_placements_on_chip(x, y)):
            board_colours[x, y] = unused
        else:
            vertex = None
            for placement in placements.placements_on_chip(x, y):
                if not system_placements.is_vertex_placed(placement.vertex):
                    vertex = placement.vertex
                    break
            if vertex is not None:
                board_colours[x, y] = vertex_colours[vertex.app_vertex]
    include_boards = [
        (chip.x, chip.y) for chip in machine.ethernet_connected_chips]
    w = math.ceil(machine.width / 12)
    h = math.ceil(machine.height / 12)
    aspect_ratio = get_machine_map_aspect_ratio(w, h)
    image_width = 10000
    image_height = int(image_width * aspect_ratio)
    output_filename = report_file
    hex_boards = board.create_torus(w, h)
    with PNGContextManager(
            output_filename, image_width, image_height) as ctx:
        draw_machine_map(
            ctx, image_width, image_height, machine.width, machine.height,
            hex_boards, dict(), board_colours, include_boards)


class _SpaceExceededException(Exception):
    pass


def _do_fixed_location(vertices, sdram, placements, machine, next_chip_space):
    """
    :param vertices:
    :param sdram:
    :param placements:
    :param machine:
    :param _ChipWithSpace next_chip_space:
    :return:
    """
    x = None
    y = None
    constrained = False
    for vertex in vertices:
        if vertex.get_fixed_location():
            x = vertex.get_fixed_location().x
            y = vertex.get_fixed_location().y
            constrained = True
    if constrained:
        chip = machine.get_chip_at(x, y)
        if chip is None:
            raise PacmanConfigurationException(
                f"Constrained to chip {x, y} but no such chip")
        on_chip = placements.placements_on_chip(x, y)
        cores_used = {p.p for p in on_chip}
        cores = set(p.processor_id for p in chip.processors
                    if not p.is_monitor) - cores_used
        next_cores = iter(cores)
        for vertex in vertices:
            next_core = None
            if vertex.get_fixed_location():
                fixed = vertex.get_fixed_location()
                if fixed.p is not None:
                    if fixed.p not in next_cores:
                        raise PacmanConfigurationException(
                            f"Core {fixed.p} on {x}, {y} not available to "
                            f"place {vertex} on")
                    next_core = fixed.p
            if next_core is None:
                try:
                    next_core = next(next_cores)
                except StopIteration:
                    # pylint: disable=raise-missing-from
                    raise PacmanConfigurationException(
                        f"No more cores available on {x}, {y}: {on_chip}")
            placements.add_placement(Placement(vertex, x, y, next_core))
            if next_chip_space.x == x and next_chip_space.y == y:
                next_chip_space.cores.remove(next_core)
                next_chip_space.use_sdram(sdram)
        return True
    return False


def _store_on_chip(placements_to_make, vertices, sdram, next_chip_space):
    """
    :param placements_to_make:
    :param vertices:
    :param sdram:
    :param _ChipWithSpace next_chip_space:
    """
    for vertex in vertices:
        core = next_chip_space.use_next_core()
        placements_to_make.append(Placement(
            vertex, next_chip_space.x, next_chip_space.y, core))
    next_chip_space.use_sdram(sdram)


class _Spaces(object):
    __slots__ = ["__machine", "__chips", "__next_chip", "__used_chips",
                 "__system_placements", "__placements", "__plan_n_timesteps",
                 "__last_chip_space", "__saved_chips", "__restored_chips"]

    def __init__(self, machine, placements, plan_n_timesteps):
        self.__machine = machine
        self.__placements = placements
        self.__plan_n_timesteps = plan_n_timesteps
        self.__chips = iter(_chip_order(machine))
        self.__next_chip = next(self.__chips)
        self.__used_chips = set()
        self.__last_chip_space = None
        self.__saved_chips = OrderedSet()
        self.__restored_chips = OrderedSet()

    def __cores_and_sdram(self, chip):
        """
        :param Chip chip:
        :rtype: (int, int)
        :return:
        """
        on_chip = self.__placements.placements_on_chip(chip.x, chip.y)
        cores_used = {p.p for p in on_chip}
        sdram_used = sum(
            p.vertex.sdram_required.get_total_sdram(
                self.__plan_n_timesteps) for p in on_chip)
        return cores_used, sdram_used

    def get_next_chip_and_space(self):
        """
        :rtype: (_ChipWithSpace, _Space)
        """
        try:
            if self.__last_chip_space is None:
                chip = self.__get_next_chip()
                cores_used, sdram_used = self.__cores_and_sdram(chip)
                self.__last_chip_space = _ChipWithSpace(
                    chip, cores_used, sdram_used)
                self.__used_chips.add(chip)

            # Start a new space by finding all the chips that can be reached
            # from the start chip but have not been used
            return (self.__last_chip_space,
                    _Space(self.__last_chip_space.chip))

        except StopIteration:
            raise PacmanPlaceException(  # pylint: disable=raise-missing-from
                f"No more chips to place on; {self.n_chips_used} of "
                f"{self.__machine.n_chips} used")

    def __get_next_chip(self):
        """
        :rtype: Chip
        """
        while self.__restored_chips:
            chip = self.__restored_chips.pop(last=False)
            if chip not in self.__used_chips:
                return chip
        while (self.__next_chip in self.__used_chips):
            self.__next_chip = next(self.__chips)
        return self.__next_chip

    def get_next_chip_space(self, space, last_chip_space):
        """
        :param _Space space:
        :param _ChipWithSpace last_chip_space:
        :rtype: _ChipWithSpace
        """
        # If we are reporting a used chip, update with reachable chips
        if last_chip_space is not None:
            last_chip = last_chip_space.chip
            space.update(self.__usable_from_chip(last_chip))

        # If no space, error
        if not space:
            self.__last_chip_space = None
            raise _SpaceExceededException(
                "No more chips to place on in this space; "
                f"{self.n_chips_used} of {self.__machine.n_chips} used")
        chip = space.pop()
        self.__used_chips.add(chip)
        self.__restored_chips.discard(chip)
        cores_used, sdram_used = self.__cores_and_sdram(chip)
        self.__last_chip_space = _ChipWithSpace(chip, cores_used, sdram_used)
        return self.__last_chip_space

    @property
    def n_chips_used(self):
        """
        :rtype: int
        :return:
        """
        return len(self.__used_chips)

    def __usable_from_chip(self, chip):
        """
        :param Chip chip:
        :rtype set(Chip)
        """
        chips = OrderedSet()
        for link in chip.router.links:
            chip_coords = (link.destination_x, link.destination_y)
            target_chip = self.__machine.get_chip_at(*chip_coords)
            if target_chip not in self.__used_chips:
                chips.add(target_chip)
        return chips

    def save_chips(self, chips):
        """
        :param iter(Chip) chips:
        """
        self.__saved_chips.update(chips)

    def restore_chips(self):
        for chip in self.__saved_chips:
            self.__used_chips.remove(chip)
            self.__restored_chips.add(chip)
        self.__saved_chips.clear()


class _Space(object):
    __slots__ = ["__same_board_chips", "__remaining_chips",
                 "__board_x", "__board_y", "__first_chip"]

    def __init__(self, chip):
        self.__board_x = chip.nearest_ethernet_x
        self.__board_y = chip.nearest_ethernet_y
        self.__same_board_chips = OrderedSet()
        self.__remaining_chips = OrderedSet()

    def __len__(self):
        return len(self.__same_board_chips) + len(self.__remaining_chips)

    def __on_same_board(self, chip):
        return (chip.nearest_ethernet_x == self.__board_x and
                chip.nearest_ethernet_y == self.__board_y)

    def pop(self):
        """
        :type: Chip
        :return:
        """
        if self.__same_board_chips:
            return self.__same_board_chips.pop(last=False)
        if self.__remaining_chips:
            next_chip = self.__remaining_chips.pop(last=False)
            self.__board_x = next_chip.nearest_ethernet_x
            self.__board_y = next_chip.nearest_ethernet_y
            to_remove = list()
            for chip in self.__remaining_chips:
                if self.__on_same_board(chip):
                    to_remove.append(chip)
                    self.__same_board_chips.add(chip)
            for chip in to_remove:
                self.__remaining_chips.remove(chip)
            return next_chip
        raise StopIteration

    def update(self, chips):
        """
        :param iter(Chip) chips:
        """
        for chip in chips:
            if self.__on_same_board(chip):
                self.__same_board_chips.add(chip)
            else:
                self.__remaining_chips.add(chip)


class _ChipWithSpace(object):
    """ A chip with space for placement.
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

    def __repr__(self):
        return f"({self.x}, {self.y})"


def _chip_order(machine):
    """
    :param machine:
    :rtype: Chip
    """
    s_x, s_y = get_config_str("Mapping", "placer_start_chip").split(",")
    s_x = int(s_x)
    s_y = int(s_y)

    for x in range(machine.width):
        for y in range(machine.height):
            c_x = (x + s_x) % machine.width
            c_y = (y + s_y) % machine.height
            chip = machine.get_chip_at(c_x, c_y)
            if chip:
                yield chip
