# pacman imports
from pacman import exceptions
from pacman.model.graphs.abstract_fpga_vertex import AbstractFPGAVertex
from pacman.model.graphs.abstract_spinnaker_link_vertex\
    import AbstractSpiNNakerLinkVertex
from pacman.model.graphs.abstract_virtual_vertex import AbstractVirtualVertex
from pacman.utilities.algorithm_utilities import machine_algorithm_utilities
from pacman.utilities.algorithm_utilities.element_allocator_algorithm \
    import ElementAllocatorAlgorithm
from spinn_machine.utilities.progress_bar import ProgressBar

# general imports
import logging
import math
logger = logging.getLogger(__name__)


class MallocBasedChipIdAllocator(ElementAllocatorAlgorithm):
    """ A Chip id Allocation Allocator algorithm that keeps track of
        chip ids and attempts to allocate them as requested
    """

    __slots__ = [
        # dict of [spinnaker link data] = (x,y, link data)
        "_virtual_chips"
    ]

    def __init__(self):
        ElementAllocatorAlgorithm.__init__(self, 0, math.pow(2, 32))

        # we only want one virtual chip per 'link'
        self._virtual_chips = dict()

    def __call__(self, machine, graph=None):
        """

        :param graph:
        :param machine:
        :return:
        """

        if graph is not None:

            # Go through the groups and allocate keys
            progress_bar = ProgressBar(
                graph.n_vertices + machine.n_chips,
                "Allocating virtual identifiers")

            # allocate standard ids for real chips
            for x, y in machine.chip_coordinates:
                expected_chip_id = (x << 8) + y
                self._allocate_elements(expected_chip_id, 1)
                progress_bar.update()

            # allocate ids for virtual chips
            for vertex in graph.vertices:
                if isinstance(vertex, AbstractVirtualVertex):
                    link_data = None
                    if isinstance(vertex, AbstractFPGAVertex):
                        link_data = machine.get_fpga_link_with_id(
                            vertex.fpga_id, vertex.fpga_link_id,
                            vertex.board_address)
                        if link_data is None:
                            raise exceptions.PacmanConfigurationException(
                                "No FPGA Link {} on FPGA {} found on board "
                                "{}.  This would be true if another chip was "
                                "found connected at this point".format(
                                    vertex.fpga_link_id, vertex.fpga_id,
                                    vertex.board_address))
                    elif isinstance(vertex, AbstractSpiNNakerLinkVertex):
                        link_data = machine.get_spinnaker_link_with_id(
                            vertex.spinnaker_link_id, vertex.board_address)
                        if link_data is None:
                            raise exceptions.PacmanConfigurationException(
                                "No SpiNNaker Link {} found on board "
                                "{}.  This would be true if another chip was "
                                "found connected at this point".format(
                                    vertex.spinnaker_link_id,
                                    vertex.board_address))
                    else:
                        raise exceptions.PacmanConfigurationException(
                            "Unknown virtual vertex type {}".format(
                                vertex.__class__))
                    virtual_x, virtual_y = self._assign_virtual_chip_info(
                        machine, link_data)
                    vertex.set_virtual_chip_coordinates(virtual_x, virtual_y)
                progress_bar.update()
            progress_bar.end()

        return machine

    def _assign_virtual_chip_info(self, machine, link_data):
        if link_data not in self._virtual_chips:
            chip_id_x, chip_id_y = self._allocate_id()
            machine_algorithm_utilities.create_virtual_chip(
                machine, link_data, chip_id_x, chip_id_y)
            self._virtual_chips[link_data] = (chip_id_x, chip_id_y)

            return chip_id_x, chip_id_y

        chip_id_x, chip_id_y = self._virtual_chips[link_data]
        return chip_id_x, chip_id_y

    def _allocate_id(self):
        """ Allocate a chip id from the free space
        """

        # can always assume there's at least one element in the free space,
        # otherwise it will have already been deleted already.
        free_space_chunk = self._free_space_tracker[0]
        chip_id = free_space_chunk.start_address
        self._allocate_elements(chip_id, 1)
        return (chip_id >> 8), (chip_id & 0xFFFF)
