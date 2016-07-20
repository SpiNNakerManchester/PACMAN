
# pacman imports
from pacman.model.partitioned_graph.partitioned_vertex import PartitionedVertex
from pacman.model.constraints.placer_constraints\
    .placer_chip_and_core_constraint import PlacerChipAndCoreConstraint
from pacman import exceptions

# general imports
from abc import ABCMeta
from six import add_metaclass


@add_metaclass(ABCMeta)
class AbstractVirtualPartitionedVertex(PartitionedVertex):

    def __init__(
            self, resources_required, label, board_address=None,
            constraints=None):
        PartitionedVertex.__init__(
            self, resources_required, label, constraints=constraints)

        self._board_address = board_address
        self._virtual_chip_x = None
        self._virtual_chip_y = None
        self._real_chip_x = None
        self._real_chip_y = None
        self._real_link = None

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

    def set_virtual_chip_coordinates(
            self, virtual_chip_x, virtual_chip_y, real_chip_x, real_chip_y,
            real_link):
        self._virtual_chip_x = virtual_chip_x
        self._virtual_chip_y = virtual_chip_y
        self._real_chip_x = real_chip_x
        self._real_chip_y = real_chip_y
        self._real_link = real_link
        placement_constaint = PlacerChipAndCoreConstraint(
            self._virtual_chip_x, self._virtual_chip_y)
        self.add_constraint(placement_constaint)

    @property
    def board_address(self):
        return self._board_address

    @board_address.setter
    def board_address(self, new_value):
        if self._board_address is None:
            self._board_address = new_value
        else:
            raise exceptions.PacmanConfigurationException(
                "The board address of the virutal vertex has already been "
                "configured. Overiding at this point is deemed an error.")
