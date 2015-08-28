"""
MallocBasedChipIdAllocator
"""

# pacman imports
from pacman.model.abstract_classes.abstract_virtual_vertex import \
    AbstractVirtualVertex
from pacman.operations.abstract_algorithms.\
    abstract_element_allocator_algorithm import \
    AbstractElementAllocatorAlgorithm
from pacman.utilities.progress_bar import ProgressBar

# general imports
import logging
import math
logger = logging.getLogger(__name__)


class MallocBasedChipIdAllocator(AbstractElementAllocatorAlgorithm):
    """ A Chip id Allocation Allocator algorithm that keeps track of
        chip ids and attempts to allocate them as requested
    """

    def __init__(self):
        AbstractElementAllocatorAlgorithm.__init__(self, 0, math.pow(2, 32))

    def allocate_chip_ids(self, partitionable_graph, machine):
        """

        :param partitionable_graph:
        :param machine:
        :return:
        """
        # Go through the groups and allocate keys
        progress_bar = ProgressBar(
            (len(partitionable_graph.vertices) + len(list(machine.chips))),
            "Allocating virtual identifiers")

        # allocate standard ids for real chips
        for chip in machine.chips:
            expected_chip_id = (chip.x << 8) + chip.y
            self._allocate_elements(expected_chip_id, 1)
            progress_bar.update()

        # allocate ids for virtual chips
        for vertex in partitionable_graph.vertices:
            if isinstance(vertex, AbstractVirtualVertex):
                chip_id_x, chip_id_y = self._allocate_id()
                vertex.virtual_chip_x = chip_id_x
                vertex.virtual_chip_y = chip_id_y
            progress_bar.update()
        progress_bar.end()

    def _allocate_id(self):
        """
        allocate a chip id from the free space
        :return:
        """
        # can always asssume theres at least one element in the free space,
        # otherwise it will have already been deleted already.
        free_space_chunk = self._free_space_tracker[0]
        chip_id = free_space_chunk.start_address
        self._allocate_elements(chip_id, 1)
        return (chip_id >> 8), (chip_id & 0xFFFF)
