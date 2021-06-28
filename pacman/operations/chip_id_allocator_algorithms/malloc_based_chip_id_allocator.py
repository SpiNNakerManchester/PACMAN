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

import logging
from spinn_utilities.log import FormatAdapter
from spinn_utilities.progress_bar import ProgressBar
from pacman.exceptions import PacmanConfigurationException
from pacman.model.graphs import (
    AbstractFPGA, AbstractSpiNNakerLink, AbstractVirtual)
from pacman.utilities.algorithm_utilities import machine_algorithm_utilities

logger = FormatAdapter(logging.getLogger(__name__))
_LOWER_16_BITS = 0xFFFF


class NoFPGALink(PacmanConfigurationException):
    def __init__(self, vertex):
        super().__init__(
            "No FPGA Link {} on FPGA {} found on board {}. This would be "
            "true if another chip was found connected at this point".format(
                vertex.fpga_link_id, vertex.fpga_id, vertex.board_address))


class NoSpiNNakerLink(PacmanConfigurationException):
    def __init__(self, vertex):
        super().__init__(
            "No SpiNNaker Link {} found on board {}. This would be true if "
            "another chip was found connected at this point".format(
                vertex.spinnaker_link_id, vertex.board_address))


class MallocBasedChipIdAllocator(object):
    """ A Chip ID Allocation Allocator algorithm that keeps track of\
        chip IDs and attempts to allocate them as requested
    """

    __slots__ = [
        # dict of [virtual chip data] = (x,y)
        "_virtual_chips",
        "__next_id"
    ]

    def __init__(self):

        # we only want one virtual chip per 'link'
        self._virtual_chips = dict()

        # Start allocating and -2, -2 and go down
        self.__next_id = -2

    def __call__(self, machine, machine_graph):
        """
        :param ~spinn_machine.Machine machine:
        :param MachineGraph graph:
        :rtype: ~spinn_machine.Machine
        :raises PacmanConfigurationException:
            If a virtual chip is in an impossible position.
        """
        progress = ProgressBar(
            machine_graph.n_vertices + machine.n_chips,
            "Allocating virtual identifiers")

        # allocate IDs for virtual chips
        for vertex in progress.over(machine_graph.vertices):
            if isinstance(vertex, AbstractVirtual):
                x, y = self._assign_virtual_chip_info(
                    machine, self._get_link_data(machine, vertex))
                vertex.set_virtual_chip_coordinates(x, y)

        return machine

    @staticmethod
    def _get_link_data(machine, vertex):
        if isinstance(vertex, AbstractFPGA):
            link_data = machine.get_fpga_link_with_id(
                vertex.fpga_id, vertex.fpga_link_id, vertex.board_address)
            if link_data is None:
                raise NoFPGALink(vertex)
            return link_data
        elif isinstance(vertex, AbstractSpiNNakerLink):
            link_data = machine.get_spinnaker_link_with_id(
                vertex.spinnaker_link_id, vertex.board_address)
            if link_data is None:
                raise NoSpiNNakerLink(vertex)
            return link_data
        else:
            # Ugh; this means we can't handle link data for arbitrary classes
            raise PacmanConfigurationException(
                "Unknown virtual vertex type {}".format(vertex.__class__))

    def _assign_virtual_chip_info(self, machine, link_data):
        # If we've seen the link data before, return the allocated ID we have
        if link_data in self._virtual_chips:
            return self._virtual_chips[link_data]

        # Allocate a new ID and cache it for later
        (chip_id_x, chip_id_y) = self.__next_id, self.__next_id
        self.__next_id -= 1
        machine_algorithm_utilities.create_virtual_chip(
            machine, link_data, chip_id_x, chip_id_y)
        self._virtual_chips[link_data] = (chip_id_x, chip_id_y)
        return chip_id_x, chip_id_y
