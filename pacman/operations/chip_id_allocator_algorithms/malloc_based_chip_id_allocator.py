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
from spinn_utilities.progress_bar import ProgressBar
from pacman.exceptions import PacmanConfigurationException
from pacman.model.graphs import (
    AbstractFPGAVertex, AbstractSpiNNakerLinkVertex, AbstractVirtual)
from pacman.utilities.algorithm_utilities import (
    machine_algorithm_utilities, ElementAllocatorAlgorithm)

logger = logging.getLogger(__name__)
_LOWER_16_BITS = 0xFFFF


class NoFPGALink(PacmanConfigurationException):
    def __init__(self, vertex):
        super(NoFPGALink, self).__init__(
            "No FPGA Link {} on FPGA {} found on board {}. This would be "
            "true if another chip was found connected at this point".format(
                vertex.fpga_link_id, vertex.fpga_id, vertex.board_address))


class NoSpiNNakerLink(PacmanConfigurationException):
    def __init__(self, vertex):
        super(NoSpiNNakerLink, self).__init__(
            "No SpiNNaker Link {} found on board {}. This would be true if "
            "another chip was found connected at this point".format(
                vertex.spinnaker_link_id, vertex.board_address))


class MallocBasedChipIdAllocator(ElementAllocatorAlgorithm):
    """ A Chip ID Allocation Allocator algorithm that keeps track of\
        chip IDs and attempts to allocate them as requested
    """

    __slots__ = [
        # dict of [virtual chip data] = (x,y)
        "_virtual_chips"
    ]

    def __init__(self):
        super(MallocBasedChipIdAllocator, self).__init__(0, 2 ** 32)

        # we only want one virtual chip per 'link'
        self._virtual_chips = dict()

    def __call__(self, machine, graph=None):
        if graph is not None:
            self.allocate_chip_ids(machine, graph)
        return machine

    def allocate_chip_ids(self, machine, graph):
        """ Go through the chips (real and virtual) and allocate keys for each
        """
        progress = ProgressBar(
            graph.n_vertices + machine.n_chips,
            "Allocating virtual identifiers")

        # allocate standard IDs for real chips
        for x, y in progress.over(machine.chip_coordinates, False):
            expected_chip_id = (x << 8) + y
            self._allocate_elements(expected_chip_id, 1)

        # allocate IDs for virtual chips
        for vertex in progress.over(graph.vertices):
            if isinstance(vertex, AbstractVirtual):
                x, y = self._assign_virtual_chip_info(
                    machine, self._get_link_data(machine, vertex))
                vertex.set_virtual_chip_coordinates(x, y)

    @staticmethod
    def _get_link_data(machine, vertex):
        if isinstance(vertex, AbstractFPGAVertex):
            link_data = machine.get_fpga_link_with_id(
                vertex.fpga_id, vertex.fpga_link_id, vertex.board_address)
            if link_data is None:
                raise NoFPGALink(vertex)
            return link_data
        elif isinstance(vertex, AbstractSpiNNakerLinkVertex):
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
        chip_id_x, chip_id_y = self._allocate_id()
        machine_algorithm_utilities.create_virtual_chip(
            machine, link_data, chip_id_x, chip_id_y)
        self._virtual_chips[link_data] = (chip_id_x, chip_id_y)
        return chip_id_x, chip_id_y

    def _allocate_id(self):
        """ Allocate a chip ID from the free space
        """

        # can always assume there's at least one element in the free space,
        # otherwise it will have already been deleted already.
        free_space_chunk = self._free_space_tracker[0]
        chip_id = free_space_chunk.start_address
        self._allocate_elements(chip_id, 1)
        return (chip_id >> 8), (chip_id & _LOWER_16_BITS)
