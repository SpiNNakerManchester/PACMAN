
# pacman imports
from pacman.model.abstract_classes.abstract_virtual_vertex \
    import AbstractVirtualVertex
from pacman.utilities.algorithm_utilities.element_allocator_algorithm \
    import ElementAllocatorAlgorithm
from spinn_machine.utilities.progress_bar import ProgressBar
from pacman.utilities.algorithm_utilities import machine_algorithm_utilities
from pacman.model.abstract_classes.virtual_partitioned_vertex \
    import VirtualPartitionedVertex
from pacman import exceptions

# general imports
import logging
import math
logger = logging.getLogger(__name__)


class MallocBasedChipIdAllocator(ElementAllocatorAlgorithm):
    """ A Chip id Allocation Allocator algorithm that keeps track of
        chip ids and attempts to allocate them as requested
    """

    def __init__(self):
        ElementAllocatorAlgorithm.__init__(self, 0, math.pow(2, 32))

        # we only want one virtual chip per 'link'
        self._virtual_chips = dict()

    def __call__(
            self, machine, partitionable_graph=None, partitioned_graph=None):
        """

        :param partitionable_graph:
        :param partitioned_graph:
        :param machine:
        :return:
        """
        if partitionable_graph is not None:

            # Go through the groups and allocate keys
            progress_bar = ProgressBar(
                (len(partitionable_graph.vertices) + len(list(machine.chips))),
                "Allocating virtual identifiers")
        elif partitioned_graph is not None:

            # Go through the groups and allocate keys
            progress_bar = ProgressBar(
                (len(partitioned_graph.subvertices) +
                 len(list(machine.chips))),
                "Allocating virtual identifiers")
        else:
            progress_bar = ProgressBar(
                len(list(machine.chips)), "Allocating virtual identifiers")

        # allocate standard ids for real chips
        for chip in machine.chips:
            expected_chip_id = (chip.x << 8) + chip.y
            self._allocate_elements(expected_chip_id, 1)
            progress_bar.update()

        if partitionable_graph is not None:

            # allocate ids for virtual chips
            for vertex in partitionable_graph.vertices:
                if isinstance(vertex, AbstractVirtualVertex):
                    link = vertex.spinnaker_link_id
                    virtual_x, virtual_y, real_x, real_y, real_link = \
                        self._assign_virtual_chip_info(machine, link)
                    vertex.set_virtual_chip_coordinates(
                        virtual_x, virtual_y, real_x, real_y, real_link)
                progress_bar.update()
            progress_bar.end()
        elif partitioned_graph is not None:

            # allocate ids for virtual chips
            for vertex in partitioned_graph.subvertices:
                if isinstance(vertex, VirtualPartitionedVertex):
                    link = vertex.spinnaker_link_id
                    virtual_x, virtual_y, real_x, real_y, real_link = \
                        self._assign_virtual_chip_info(machine, link)
                    vertex.set_virtual_chip_coordinates(
                        virtual_x, virtual_y, real_x, real_y, real_link)
                progress_bar.update()
            progress_bar.end()

        return machine

    def _assign_virtual_chip_info(self, machine, link):
        if link not in self._virtual_chips:
            try:
                chip_id_x, chip_id_y = self._allocate_id()
                link_data = machine_algorithm_utilities.create_virtual_chip(
                    machine, link, chip_id_x, chip_id_y)
                self._virtual_chips[link] = (chip_id_x, chip_id_y, link_data)

                return (
                    chip_id_x, chip_id_y, link_data.connected_chip_x,
                    link_data.connected_chip_y, link_data.connected_link
                )
            except KeyError:
                raise exceptions.PacmanElementAllocationException(
                    "The machine in use does not have a spinnaker link"
                    " {}.  Please ensure that you are using a single physical"
                    " board.".format(link))

        chip_id_x, chip_id_y, link_data = self._virtual_chips[link]
        return (
            chip_id_x, chip_id_y, link_data.connected_chip_x,
            link_data.connected_chip_y, link_data.connected_link
        )

    def _allocate_id(self):
        """ Allocate a chip id from the free space
        """

        # can always assume there's at least one element in the free space,
        # otherwise it will have already been deleted already.
        free_space_chunk = self._free_space_tracker[0]
        chip_id = free_space_chunk.start_address
        self._allocate_elements(chip_id, 1)
        return (chip_id >> 8), (chip_id & 0xFFFF)
