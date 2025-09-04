# Copyright (c) 2014 The University of Manchester
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

from collections import defaultdict
from typing import Collection, Dict, Iterable, Iterator, Tuple, Union

from spinn_utilities.typing.coords import XY

from pacman.exceptions import (
    PacmanAlreadyPlacedError, PacmanNotPlacedError,
    PacmanProcessorAlreadyOccupiedError, PacmanProcessorNotOccupiedError)
from pacman.model.graphs.machine.machine_vertex import MachineVertex

from .placement import Placement


class Placements(object):
    """
    The placements of vertices on the chips of the machine.
    """

    __slots__ = (
        # dict of [(x,y)] -> dict of p->placement object. used for fast lookup
        # of a vertex given a set of coordinates
        "_placements",

        # dict of [machine_vertex] -> placement object. used for fast lookup of
        # the placement of a machine vertex.
        "_machine_vertices")

    def __init__(self, placements: Iterable[Placement] = ()):
        """
        :param placements: Any initial placements
        :raise PacmanAlreadyPlacedError:
            If there is any vertex with more than one placement.
        :raise PacmanProcessorAlreadyOccupiedError:
            If two placements are made to the same processor.
        """
        self._placements: Dict[XY, Dict[int, Placement]] = defaultdict(dict)
        self._machine_vertices: Dict[MachineVertex, Placement] = dict()
        if placements:
            self.add_placements(placements)

    @property
    def n_placements(self) -> int:
        """
        The number of placements.
        """
        return len(self._machine_vertices)

    def add_placements(self, placements: Iterable[Placement]) -> None:
        """
        Add some placements.

        :param placements: The placements to add
        """
        for placement in placements:
            self.add_placement(placement)

    def add_placement(self, placement: Placement) -> None:
        """
        Add a placement.

        :param placement: The placement to add
        :raise PacmanAlreadyPlacedError:
            If there is any vertex with more than one placement.
        :raise PacmanProcessorAlreadyOccupiedError:
            If two placements are made to the same processor.
        """
        x, y, p = placement.location
        if (x, y) in self._placements:
            if p in self._placements[(x, y)]:
                raise PacmanProcessorAlreadyOccupiedError((x, y, p))
        if placement.vertex in self._machine_vertices:
            raise PacmanAlreadyPlacedError(placement.vertex)

        self._placements[x, y][p] = placement
        self._machine_vertices[placement.vertex] = placement

    def get_placement_on_processor(self, x: int, y: int, p: int) -> Placement:
        """
        Get the placement on a specific processor, or raises an exception
        if the processor has not been allocated.

        :param x: the x coordinate of the chip
        :param y: the y coordinate of the chip
        :param p: the processor on the chip
        :return: the placement on the given processor
        :raise PacmanProcessorNotOccupiedError:
            If the processor is not occupied
        """
        try:
            return self._placements[x, y][p]
        except KeyError as e:
            raise PacmanProcessorNotOccupiedError((x, y, p)) from e

    def is_vertex_placed(self, vertex: MachineVertex) -> bool:
        """
        :param vertex: The vertex to determine the status of
        :returns: True if this vertex has already been placed
        """
        return vertex in self._machine_vertices

    def get_placement_of_vertex(self, vertex: MachineVertex) -> Placement:
        """
        Return the placement information for a vertex.

        :param vertex: The vertex to find the placement of
        :return: The placement
        :raise PacmanNotPlacedError: If the vertex has not been placed.
        """
        try:
            return self._machine_vertices[vertex]
        except KeyError as e:
            raise PacmanNotPlacedError(vertex) from e

    def is_processor_occupied(self, x: int, y: int, p: int) -> bool:
        """
        Determine if a processor has a vertex on it.

        :param x: x coordinate of processor.
        :param y: y coordinate of processor.
        :param p: Index of processor.
        :return bool: Whether the processor has an assigned vertex.
        """
        return (pr := self._placements.get((x, y))) is not None and p in pr

    def iterate_placements_on_core(self, xy: XY) -> Iterable[Placement]:
        """
        :param xy: x and y coordinates to find placements for.
        :returns: Iterator over placements with this x and y.
        """
        return self._placements[xy].values()

    def iterate_placements_by_xy_and_type(
            self, xy: XY, vertex_type: Union[
                type, Tuple[type, ...]]) -> Iterable[Placement]:
        """
        :param xy: x and y coordinate to find placements for.
        :param vertex_type: Class of vertex to find
        :returns: Placements with this x, y and this vertex_type.
        """
        for placement in self._placements[xy].values():
            if isinstance(placement.vertex, vertex_type):
                yield placement

    def iterate_placements_by_vertex_type(
            self, vertex_type: Union[
                type, Tuple[type, ...]]) -> Iterable[Placement]:
        """
        :param vertex_type: Class of vertex to find
        :returns: Placements on any chip with this vertex_type.
        """
        for placement in self._machine_vertices.values():
            if isinstance(placement.vertex, vertex_type):
                yield placement

    def n_placements_on_chip(self, xy: XY) -> int:
        """
        :param xy: x and y coordinate of chip.
        :returns: The number of placements on the given chip.
        """
        if xy not in self._placements:
            return 0
        return len(self._placements[xy])

    @property
    def placements(self) -> Iterable[Placement]:
        """
        All of the placements.
        """
        return iter(self._machine_vertices.values())

    def placements_on_chip(self, xy: XY) -> Collection[Placement]:
        """
        :param xy: The x and y coordinates of the chip
        :returns: The placements on a specific chip.
        """
        return self._placements[xy].values()

    @property
    def chips_with_placements(self) -> Iterable[XY]:
        """
        The chips with placements on them.
        """
        return self._placements.keys()

    def __repr__(self) -> str:
        return "".join(repr(placement) for placement in self._placements)

    def __iter__(self) -> Iterator[Placement]:
        """
        An iterator for the placements object within.
        """
        return iter(self._machine_vertices.values())

    def __len__(self) -> int:
        return len(self._machine_vertices)
