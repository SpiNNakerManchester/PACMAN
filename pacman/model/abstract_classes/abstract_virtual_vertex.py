
# pacman imports
from pacman.model.partitionable_graph.abstract_partitionable_vertex import \
    AbstractPartitionableVertex
from pacman import exceptions

# general imports
from abc import ABCMeta
from six import add_metaclass
from abc import abstractmethod


@add_metaclass(ABCMeta)
class AbstractVirtualVertex(AbstractPartitionableVertex):
    """ A class that allows models to define that they are virtual
    """

    def __init__(self, n_atoms, label, max_atoms_per_core, board_address=None,
                 constraints=None):

        AbstractPartitionableVertex.__init__(
            self, n_atoms, label, max_atoms_per_core, constraints)

        # set up virtual data structures
        self._virtual_chip_x = None
        self._virtual_chip_y = None
        self._real_chip_x = None
        self._real_chip_y = None
        self._real_link = None
        self._board_address = board_address

    @property
    def virtual_chip_x(self):
        return self._virtual_chip_x

    @property
    def virtual_chip_y(self):
        return self._virtual_chip_y

    @property
    def real_chip_x(self):
        return self._real_chip_x

    @property
    def real_chip_y(self):
        return self._real_chip_y

    @property
    def real_link(self):
        return self._real_link

    @property
    def board_address(self):
        return self._board_address

    @board_address.setter
    def board_address(self, new_value):
        if self._board_address is None:
            self._board_address = new_value
        else:
            raise exceptions.PacmanConfigurationException(
                "The board address of the virtual vertex has already been "
                "configured. Overriding at this point is deemed an error.")

    def set_virtual_chip_coordinates(
            self, virtual_chip_x, virtual_chip_y, real_chip_x, real_chip_y,
            real_link):
        self._virtual_chip_x = virtual_chip_x
        self._virtual_chip_y = virtual_chip_y
        self._real_chip_x = real_chip_x
        self._real_chip_y = real_chip_y
        self._real_link = real_link

    @abstractmethod
    def is_virtual_vertex(self):
        """ helper method for is instance

        :return:
        """

    # overloaded method from partitionable vertex
    def get_cpu_usage_for_atoms(self, vertex_slice, graph):
        return 0

    # overloaded method from partitionable vertex
    def get_dtcm_usage_for_atoms(self, vertex_slice, graph):
        return 0

    # overloaded method from partitionable vertex
    def get_sdram_usage_for_atoms(self, vertex_slice, graph):
        return 0
