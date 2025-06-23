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
from __future__ import annotations
import logging
from typing import Dict, Iterator, List, Optional, Tuple, Sequence, Set

from spinn_utilities.config_holder import get_config_bool, get_report_path
from spinn_utilities.log import FormatAdapter
from spinn_utilities.progress_bar import ProgressBar

from spinn_machine import Chip

from pacman.data import PacmanDataView
from pacman.model.placements import Placements, Placement
from pacman.model.graphs import AbstractVirtual
from pacman.model.graphs.machine import MachineVertex
from pacman.model.graphs.application import ApplicationVertex
from pacman.model.resources import AbstractSDRAM, ConstantSDRAM
from pacman.exceptions import (
    PacmanPlaceException, PacmanConfigurationException, PacmanTooBigToPlace)
from .draw_placements import draw_placements as dp

logger = FormatAdapter(logging.getLogger(__name__))


def place_application_graph(system_placements: Placements) -> Placements:
    """
    Perform placement of an application graph on the machine.

    .. note::
        app_graph must have been partitioned

    :param system_placements:
        The placements of cores doing system tasks. This is what we start from.
    :return: Placements for the application. *Includes the system placements.*
    """
    placer = ApplicationPlacer(system_placements)
    return placer.do_placements(system_placements)


class ApplicationPlacer(object):
    """
    Places the Vertices keeping ones for an ApplicationVertex together.

    """
    __slots__ = (
        # Values from PacmanDataView cached for speed
        # PacmanDataView.get_machine()
        "__machine",
        # PacmanDataView.get_plan_n_timestep()
        "__plan_n_timesteps",
        # Sdram available on perfect none Ethernet Chip after Monitors placed
        "__max_sdram",
        # Maximum sdram that should be used for a Chip to not be full
        "__cap_sdram",
        # N Cores free on perfect none Ethernet Chip after Monitors placed
        "__max_cores",

        # Pointer to the placements including all previous Application Vertices
        "__placements",
        # A Function to yield the Chips in a consistent order
        "__chips",
        # Chips that have been fully placed by previous Application Vertices
        "__full_chips",
        # Chips that have already been used by this ApplicationVertex
        "__prepared_chips",
        # Start Chips from previous ApplicationVertices not yet marked as full
        "__restored_chips",
        # Start Chips tried for this ApplicationVertex
        "__starts_tried",
        # Label of the current ApplicationVertex for (error) reporting
        "__app_vertex_label",

        # Data for the last Chip offered to place on
        # May be full after current group placed
        "__current_chip",
        # List of cores available. Included ones for current group until used
        "__current_cores_free",
        # Used sdram after the current group is placed
        "__current_sdram_used",

        # Data about the neighbouring Chips to ones used
        # Current board being placed on
        "__ethernet_x",
        "__ethernet_y",
        # List of available neighbours on the current board
        "__same_board_chips",
        # List of available neighbours not on the current board
        "__other_board_chips")

    def __init__(self, placements: Placements):
        """
        :param placements:
        """
        # Data cached for speed
        self.__machine = PacmanDataView.get_machine()
        self.__plan_n_timesteps = PacmanDataView.get_plan_n_timestep()
        version = PacmanDataView.get_machine_version()
        self.__max_sdram = (
                version.max_sdram_per_chip -
                PacmanDataView.get_all_monitor_sdram().get_total_sdram(
                    PacmanDataView.get_plan_n_timestep()))
        self.__max_cores = (
                version.max_cores_per_chip - version.n_scamp_cores -
                PacmanDataView.get_all_monitor_cores())
        self.__cap_sdram = self.__max_sdram - (
                self.__max_sdram // self.__max_cores)

        self.__placements = placements
        self.__chips = self._chip_order()

        self.__full_chips: Set[Chip] = set()
        self.__prepared_chips: Set[Chip] = set()
        self.__restored_chips: List[Chip] = list()
        self.__starts_tried: List[Chip] = list()

        self.__current_chip: Optional[Chip] = None
        self.__current_cores_free: List[int] = list()
        self.__current_sdram_used: AbstractSDRAM = ConstantSDRAM(0)
        self.__app_vertex_label: Optional[str] = None

        # Set some value so no Optional needed
        self.__ethernet_x = -1
        self.__ethernet_y = -1
        self.__same_board_chips: Dict[Chip, Chip] = dict()
        self.__other_board_chips:  Dict[Chip, Chip] = dict()

    def do_placements(self, system_placements: Placements) -> Placements:
        """
        Perform placement of an application graph on the machine.

        .. note::
            app_graph must have been partitioned

        :param system_placements:
            The placements of cores doing system tasks.
        :return: Placements for the application.
            *Includes the system placements.*
        :raises PacmanPlaceException: If no new start Chip is available
        :raises PacmanTooBigToPlace:
            If the requirements are too big for any chip
        """
        # Go through the application graph by application vertex
        progress = ProgressBar(
            PacmanDataView.get_n_vertices() * 2, "Placing Vertices")
        try:
            for app_vertex in progress.over(
                    PacmanDataView.iterate_vertices(), finish_at_end=False):
                if app_vertex.has_fixed_location():
                    self._place_fixed_vertex(app_vertex)

            for app_vertex in progress.over(PacmanDataView.iterate_vertices()):
                # as this checks if placed already not need to check if fixed
                self._place_vertex(app_vertex)
        except PacmanPlaceException as e:
            raise self._place_error(system_placements, e) from e

        if get_config_bool("Reports", "draw_placements"):
            report_file = get_report_path("path_placements")
            dp(self.__placements, system_placements, report_file)

        return self.__placements

    def _place_vertex(self, app_vertex: ApplicationVertex) -> None:
        """
        Place the next application vertex

        :param app_vertex:
        :raises PacmanPlaceException: If no new start Chip is available
        :raises PacmanTooBigToPlace:
            If the requirements are too big for any chip
        """
        same_chip_groups = app_vertex.splitter.get_same_chip_groups()
        if not same_chip_groups:
            # This vertex does not require placement or delegates
            return

        self.__app_vertex_label = app_vertex.label

        # Restore the starts tried last time.
        # Check if they are full comes later
        while len(self.__starts_tried) > 0:
            self.__restored_chips.append(self.__starts_tried.pop(0))

        # try to make placements with a different start Chip each time
        while True:
            placements_to_make = self._prepare_placements(same_chip_groups)
            if placements_to_make is not None:
                break

        # Now actually add the placements having confirmed all can be done
        self.__placements.add_placements(placements_to_make)

    def _prepare_placements(self, same_chip_groups:  Sequence[
            Tuple[Sequence[MachineVertex], AbstractSDRAM]]
            ) -> Optional[List[Placement]]:
        """
        Try to make the placements for this ApplicationVertex.

        This will make sure all placements are on linked Chips

        The next start Chip is tried.

        If successful a list of created but NOT added placements is returned

        If this start Chip fails it returns None.
        A start chip could fail either because it does not have enough space
        or because its neighbours do not have enough space


        :param same_chip_groups:
        :raises PacmanPlaceException: If no new start Chip is available
        :raises PacmanTooBigToPlace:
            If the requirements are too big for any chip
        """
        # Clear the Chips used in the last prepare
        self.__prepared_chips.clear()
        self.__current_chip = None

        placements_to_make: List = list()

        # Go through the groups
        for vertices, sdram in same_chip_groups:
            vertices_to_place = self._filter_vertices(vertices)
            if len(vertices_to_place) == 0:
                # Either placed (fixed) or virtual so skip group
                continue
            n_cores = len(vertices_to_place)

            # Try to find a chip with space
            chip = self._get_next_chip_with_space(n_cores, sdram)
            if chip is None:
                return None

            # If this worked, store placements to be made
            for vertex in vertices:
                core = self.__current_cores_free.pop(0)
                placements_to_make.append(Placement(
                    vertex, chip.x, chip.y, core))
        return placements_to_make

    def _filter_vertices(
            self, vertices: Sequence[MachineVertex]) -> List[MachineVertex]:
        """
        Removes an already placed or virtual vertices.

        Errors on groups that have both placed and unplaced vertices!

        :param vertices:
        """
        # Remove any already placed
        vertices_to_place = [
            vertex for vertex in vertices
            if not self.__placements.is_vertex_placed(vertex)]
        if len(vertices_to_place) != len(vertices) and len(
                vertices_to_place) > 0:
            # Putting the rest on a different chip is wrong
            # Putting them on the same chip is hard so will do if needed
            raise NotImplementedError(
                "Unexpected mix of placed and unplaced vertices")
        # No need to place virtual vertices
        return [vertex for vertex in vertices_to_place
                if not isinstance(vertex, AbstractVirtual)]

    def _place_error(self, system_placements: Placements,
                     exception: Exception) -> PacmanPlaceException:
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
                if self.__placements.is_vertex_placed(vertices[0]):
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

        report_file = get_report_path("path_placement_errors_report")
        with open(report_file, 'w', encoding="utf-8") as f:
            f.write(f"Could not place {len(unplaceable)} of "
                    f"{PacmanDataView.get_n_vertices()} "
                    f"application vertices.\n")
            f.write(
                f"    Could not place {vertex_count} of {n_vertices} in the"
                " last app vertex\n\n")
            for xy in self.__placements.chips_with_placements:
                first = True
                for placement in self.__placements.placements_on_chip(xy):
                    if system_placements.is_vertex_placed(placement.vertex):
                        continue
                    if first:
                        f.write(f"Chip ({xy}):\n")
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
                    p_sdram = sdram.get_total_sdram(self.__plan_n_timesteps)
                    f.write(f"    Group of {len(vertices)} vertices uses "
                            f"{p_sdram} bytes of SDRAM:\n")
                    for vertex in vertices:
                        f.write(f"        Vertex {vertex}")
                        if self.__placements.is_vertex_placed(vertex):
                            plce = self.__placements.get_placement_of_vertex(
                                vertex)
                            f.write(
                                f" (placed at {plce.x}, {plce.y}, {plce.p})")
                        f.write("\n")

            f.write("\n")
            f.write("Unused chips:\n")
            machine = PacmanDataView.get_machine()
            for xy in machine.chip_coordinates:
                n_placed = self.__placements.n_placements_on_chip(xy)
                system_placed = system_placements.n_placements_on_chip(xy)
                if n_placed - system_placed == 0:
                    n_procs = machine[xy].n_placable_processors
                    f.write(f"    {xy} ({n_procs - system_placed}"
                            " free cores)\n")

        if get_config_bool("Reports", "draw_placements_on_error"):
            report_file = get_report_path("path_placements_on_error")
            dp(self.__placements, system_placements, report_file)

        return PacmanPlaceException(
            f" {exception}."
            f" Report written to {report_file}.")

    def _place_fixed_vertex(self, app_vertex: ApplicationVertex) -> None:
        """
        Place all vertices for this Application Vertex

        Checks that all MachineVertices are fixed or errors
        """
        same_chip_groups = app_vertex.splitter.get_same_chip_groups()
        if not same_chip_groups:
            raise NotImplementedError("Unexpected mix of Fixed and no groups")

        for vertices, _ in same_chip_groups:
            vertices_to_place = self._filter_vertices(vertices)
            self._do_fixed_location(vertices_to_place)

    def _do_fixed_location(self, vertices: list[MachineVertex]) -> None:
        """
        Do fixed placing for one group.

        Errors if the group does not have a fixed location

        :raise PacmanConfigurationException:
            If the requested location is not available
        """
        for vertex in vertices:
            loc = vertex.get_fixed_location()
            if loc:
                x, y = loc.x, loc.y
                break
        else:
            # Mixing fixed and free allocations while still keeping the whole
            # App vertex together is hard so will only do is needed
            raise NotImplementedError(
                "Mixing fixed location and not fixed location groups "
                "within one vertex")

        chip = PacmanDataView.get_chip_at(x, y)
        if chip is None:
            raise PacmanConfigurationException(
                f"Constrained to chip {x, y} but no such chip")
        on_chip = self.__placements.placements_on_chip(chip)
        cores_used = {p.p for p in on_chip}
        cores = set(chip.placable_processors_ids) - cores_used
        next_cores = iter(cores)
        # first do the ones with a fixed p
        for vertex in vertices:
            fixed = vertex.get_fixed_location()
            if fixed and fixed.p is not None:
                if fixed.p not in next_cores:
                    raise PacmanConfigurationException(
                        f"Core {fixed.p} on {x}, {y} not available to "
                        f"place {vertex} on")
                self.__placements.add_placement(
                    Placement(vertex, x, y, fixed.p))
        # Then do the ones without a fixed p
        for vertex in vertices:
            fixed = vertex.get_fixed_location()
            if not fixed or fixed.p is None:
                try:
                    self.__placements.add_placement(
                        Placement(vertex, x, y, next(next_cores)))
                except StopIteration:
                    # pylint: disable=raise-missing-from
                    raise PacmanConfigurationException(
                        f"No more cores available on {x}, {y}: {on_chip}")

    def _chip_order(self) -> Iterator[Chip]:
        """
        Iterate the Chips in a guaranteed order
        """
        for x in range(self.__machine.width):
            for y in range(self.__machine.height):
                chip = self.__machine.get_chip_at(x, y)
                if chip:
                    yield chip

    def _space_on_chip(
            self, chip: Chip, n_cores: int, sdram: AbstractSDRAM) -> bool:
        """
        Checks if the Chip has enough space for this group, Cache if yes

        If the Chip has already full from other Application Vertices,
        the Chip is added to the full list and False is returned

        If the chip is not full but does not have the space,
        the Chip is added to the prepared_chips list and False is returned.
        As safety check is also done to make sure the group could fit on
        another Chip

        If there there is room on the Chip
        the Chip is cached and True is returned.
        The values Cached are the:
        current_chip Even if full to keep the code simpler
        current_cores_free Including the ones for this group
        current_sdram_free Excluding the sdram needed fit this group

        :param chip:
        :param n_cores: number of cores needed
        :param sdram:
        :raises PacmanTooBigToPlace:
            If the requirements are too big for any chip
        """
        cores_free = list(chip.placable_processors_ids)
        sdram_used: AbstractSDRAM = ConstantSDRAM(0)

        # remove the already placed for other Application Vertices
        on_chip = self.__placements.placements_on_chip(chip)
        if len(on_chip) == len(cores_free):
            self.__full_chips.add(chip)
            return False

        for placement in on_chip:
            cores_free.remove(placement.p)
            sdram_used += placement.vertex.sdram_required

        if sdram_used.get_total_sdram(
                self.__plan_n_timesteps) > self.__cap_sdram:
            self.__full_chips.add(chip)
            return False

        # Remember this chip so it is not tried again in this preparation
        # This assumes all groups are the same size so even if too small
        self.__prepared_chips.add(chip)

        total_sdram = sdram_used + sdram
        plan_sdram = total_sdram.get_total_sdram(self.__plan_n_timesteps)
        if len(cores_free) < n_cores or plan_sdram > chip.sdram:
            self._check_could_fit(n_cores, sdram)
            return False

        # record the current Chip
        self.__current_chip = chip
        # cores are popped out later to keep them here for now
        self.__current_cores_free = cores_free
        # sdram is the whole group so can be removed now
        self.__current_sdram_used = total_sdram

        # adds the neighbours
        self._add_neighbours(chip)

        return True

    def _check_could_fit(self, n_cores: int, sdram: AbstractSDRAM) -> None:
        """
        Checks that the cores/SDRAM would fit on a empty perfect Chip

        :param n_cores: number of cores needs
        :param sdram: minimum amount of SDRAM needed
        :raises PacmanTooBigToPlace:
            If the requirements are too big for any chip
        """
        plan_sdram = sdram.get_total_sdram(self.__plan_n_timesteps)
        if plan_sdram <= self.__max_sdram and n_cores <= self.__max_cores:
            # should fit somewhere
            return
        message = \
            f"{self.__app_vertex_label} will not fit on any possible Chip "
        if n_cores > 1:
            message += f" group has {n_cores=} "
        version = PacmanDataView.get_machine_version()
        if plan_sdram > self.__max_sdram:
            message += f"requires {plan_sdram} bytes but "
            if plan_sdram > version.max_sdram_per_chip:
                message += f"a Chip only has {version.max_sdram_per_chip} " \
                           f"bytes "
            else:
                message += f"after monitors only {self.__max_sdram} " \
                           f"bytes are available "
            message += "Lowering max_core_per_chip may resolve this."
            raise PacmanTooBigToPlace(message)

        if n_cores > version.max_cores_per_chip:
            message += " is more vertices than the number of cores on a chip."
            raise PacmanTooBigToPlace(message)
        user_cores = version.max_cores_per_chip - version.n_scamp_cores
        if n_cores > user_cores:
            message += (
                f"is more vertices than the user cores ({user_cores}) "
                "available on a Chip")
        else:
            message += (
                f"is more vertices than the {self.__max_cores} cores "
                f"available on a Chip once "
                f"{PacmanDataView.get_all_monitor_cores()} "
                f"are reserved for monitors")
        raise PacmanTooBigToPlace(message)

    def _get_next_start(self, n_cores: int, sdram: AbstractSDRAM) -> Chip:
        """
        Gets the next start Chip

        Also sets up the current_chip and starts a new neighbourhood

        :param n_cores: number of cores needs
        :param sdram: minimum amount of SDRAM needed
        :raises PacmanPlaceException: If no new start Chip is available
        :raises PacmanTooBigToPlace:
            If the requirements are too big for any chip
        """
        # reset the neighbour chip info
        self.__same_board_chips.clear()
        self.__other_board_chips.clear()

        # Find the next start chip
        while True:
            start = self._pop_start_chip()
            # Save as tried as not full even if toO small
            self.__starts_tried.append(start)
            # Set the Ethernet x and y in case space_on_chip adds neighbours
            self.__ethernet_x = start.nearest_ethernet_x
            self.__ethernet_y = start.nearest_ethernet_y
            if self._space_on_chip(start, n_cores, sdram):
                break

        logger.debug("Starting placement from {}", start)
        return start

    def _pop_start_chip(self) -> Chip:
        """
        Gets the next start Chip from either restored or if none the Machine

        Ignores any Chip that are already full

        :raises PacmanPlaceException: If no new start Chip is available
        """
        while self.__restored_chips:
            chip = self.__restored_chips.pop(0)
            if chip not in self.__full_chips:
                return chip
        try:
            start = next(self.__chips)
            while start in self.__full_chips:
                start = next(self.__chips)
            return start
        except StopIteration:
            raise PacmanPlaceException(  # pylint: disable=raise-missing-from
                f"No more chips to start with for {self.__app_vertex_label} "
                f"Out of {self.__machine.n_chips} "
                f"{len(self.__full_chips)} already full "
                f"and {len(self.__starts_tried)} tried"
                f"{PacmanDataView.get_chips_boards_required_str()}")

    def _get_next_neighbour(
            self, n_cores: int, sdram: AbstractSDRAM) -> Optional[Chip]:
        """
        Gets the next neighbour Chip

        Also changes the current_chip and updates the neighbourhood

        This will return None if there are no more neighbouring Chip big enough

        :param n_cores: number of cores needs
        :param sdram: minimum amount of SDRAM needed
        :raises PacmanTooBigToPlace:
            If the requirements are too big for any chip
        """
        # Do while Chip with space not found
        while True:
            chip = self._pop_neighbour()
            if chip is None:
                # Sign to consider preparation with this start a failure
                return None
            if self._space_on_chip(chip, n_cores, sdram):
                return chip

    def _get_next_chip_with_space(
            self, n_cores: int, sdram: AbstractSDRAM) -> Optional[Chip]:
        """
        Gets the next Chip with space

        If no start Chip is available raise an Exception
        If no neighbouring more Chips available returns None

        :param n_cores: number of cores needs
        :param sdram: minimum amount of SDRAM needed
        :raises PacmanPlaceException: If no new start Chip is available
        :raises PacmanTooBigToPlace:
            If the requirements are too big for any chip
        """
        if self.__current_chip is None:
            return self._get_next_start(n_cores, sdram)

        total_sdram = sdram + self.__current_sdram_used
        plan_sdram = total_sdram.get_total_sdram(
            self.__plan_n_timesteps)
        if (len(self.__current_cores_free) >= n_cores and
                plan_sdram <= self.__current_chip.sdram):
            # Cores are popped out later
            self.__current_sdram_used = total_sdram
            return self.__current_chip
        else:
            return self._get_next_neighbour(n_cores, sdram)

    def _add_neighbours(self, chip: Chip) -> None:
        """
        Adds the neighbours for this Chip to be used as the next chips.
        """
        for link in chip.router.links:
            target = self.__machine[link.destination_x, link.destination_y]
            if (target not in self.__full_chips
                    and target not in self.__prepared_chips):
                if (target.nearest_ethernet_x == self.__ethernet_x and
                        target.nearest_ethernet_y == self.__ethernet_y):
                    self.__same_board_chips[target] = target
                else:
                    self.__other_board_chips[target] = target

    def _pop_neighbour(self) -> Optional[Chip]:
        """
        Pops the next neighbour Chip with preference to ones on current board

        :return: A neighbour Chip or None if there are no More
        """
        if self.__same_board_chips:
            k = next(iter(self.__same_board_chips))
            del self.__same_board_chips[k]
            return k
        if self.__other_board_chips:
            next_chip = next(iter(self.__other_board_chips))
            del self.__other_board_chips[next_chip]
            self.__ethernet_x = next_chip.nearest_ethernet_x
            self.__ethernet_y = next_chip.nearest_ethernet_y
            to_check = list(self.__other_board_chips)
            self.__other_board_chips.clear()
            for chip in to_check:
                if (chip.nearest_ethernet_x == self.__ethernet_x and
                        chip.nearest_ethernet_y == self.__ethernet_y):
                    self.__same_board_chips[chip] = chip
                else:
                    self.__other_board_chips[chip] = chip
            return next_chip

        # Signal that there are no more Chips with a None
        return None
