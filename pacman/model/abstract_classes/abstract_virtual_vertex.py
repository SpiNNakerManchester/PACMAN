
# pacman imports
from pacman.model.partitionable_graph.abstract_partitionable_vertex import \
    AbstractPartitionableVertex
from pacman.model.constraints.placer_constraints\
    .placer_chip_and_core_constraint import PlacerChipAndCoreConstraint

# general imports
from abc import ABCMeta
from six import add_metaclass
from abc import abstractmethod


@add_metaclass(ABCMeta)
class AbstractVirtualVertex(AbstractPartitionableVertex):
    """ A class that allows models to define that they are virtual
    """

    def __init__(self, n_atoms, spinnaker_link_id, label, max_atoms_per_core):

        AbstractPartitionableVertex.__init__(self, n_atoms, label,
                                             max_atoms_per_core)
        # set up virtual data structures
        self._virtual_chip_x = None
        self._virtual_chip_y = None
        self._spinnaker_link_id = spinnaker_link_id

    @property
    def virtual_chip_x(self):
        return self._virtual_chip_x

    @property
    def virtual_chip_y(self):
        return self._virtual_chip_y

    def set_virtual_chip_coordinates(self, virtual_chip_x, virtual_chip_y):
        self._virtual_chip_x = virtual_chip_x
        self._virtual_chip_y = virtual_chip_y
        placement_constaint = \
            PlacerChipAndCoreConstraint(self._virtual_chip_x,
                                        self._virtual_chip_y)
        self.add_constraint(placement_constaint)

    @property
    def spinnaker_link_id(self):
        """ property for returning the spinnaker link being used
        :return:
        """
        return self._spinnaker_link_id

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
