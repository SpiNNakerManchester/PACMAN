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
from typing import Any
from spinn_utilities.typing.coords import XY, XYP
from spinn_machine import Chip
from pacman.data.pacman_data_view import PacmanDataView
from pacman.model.graphs.machine import MachineVertex


class Placement(object):
    """
    The placement of a vertex on to a machine chip and core.
    """

    __slots__ = (
        # the machine vertex that is placed on the core represented
        "_vertex",

        # the chip coordinates in the SpiNNaker machine to which the machine
        # vertex is placed
        "_x", "_y",
        # The processor ID on chip (x,y) that this vertex is placed on within
        # the SpiNNaker machine
        "_p")

    def __init__(self, vertex: MachineVertex, x: int, y: int, p: int):
        """
        :param vertex: The vertex that has been placed
        :param x:
            the x-coordinate of the chip on which the vertex is placed
        :param y:
            the y-coordinate of the chip on which the vertex is placed
        :param p: the ID of the processor on which the vertex is placed
        """
        self._vertex = vertex
        self._x = x
        self._y = y
        self._p = p

    @property
    def vertex(self) -> MachineVertex:
        """
        The vertex that was placed.
        """
        return self._vertex

    @property
    def x(self) -> int:
        """
        The X-coordinate of the chip where the vertex is placed.
        """
        return self._x

    @property
    def y(self) -> int:
        """
        The Y-coordinate of the chip where the vertex is placed.
        """
        return self._y

    @property
    def p(self) -> int:
        """
        The ID of the processor of the chip where the vertex is placed.
        """
        return self._p

    @property
    def location(self) -> XYP:
        """
        The (x,y,p) tuple that represents the location of this placement.
        """
        return (self._x, self._y, self._p)

    @property
    def xy(self) -> XY:
        """
        The (x,y) tuple that represents the chip of this placement.
        """
        return (self._x, self._y)

    @property
    def chip(self) -> Chip:
        """
        The chip of this placement.
        """
        return PacmanDataView.get_chip_at(self._x, self._y)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Placement):
            return False
        return (self._x == other.x and self._y == other.y and
                self._p == other.p and self._vertex == other.vertex)

    def __hash__(self) -> int:
        return hash((self._x, self._y, self._p, self._vertex))

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)

    def __repr__(self) -> str:
        return (f"Placement(vertex={self._vertex}, "
                f"x={self._x}, y={self._y}, p={self._p})")
