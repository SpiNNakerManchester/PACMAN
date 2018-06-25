from spinn_utilities.overrides import overrides
from pacman.model.graphs import AbstractFPGAVertex, AbstractVirtualVertex
from pacman.model.resources import ResourceContainer
from .machine_vertex import MachineVertex


class MachineFPGAVertex(MachineVertex, AbstractFPGAVertex):
    """ A virtual vertex on an FPGA link.
    """

    __slots__ = [
        "_fpga_id",
        "_fpga_link_id",
        "_board_address",
        "_virtual_chip_x",
        "_virtual_chip_y"]

    def __init__(
            self, fpga_id, fpga_link_id, board_address=None, label=None,
            constraints=None):
        super(MachineFPGAVertex, self).__init__(
            label=label, constraints=constraints)

        self._fpga_id = fpga_id
        self._fpga_link_id = fpga_link_id
        self._board_address = board_address
        self._virtual_chip_x = None
        self._virtual_chip_y = None

    @property
    @overrides(MachineVertex.resources_required)
    def resources_required(self):
        return ResourceContainer()

    @property
    @overrides(AbstractFPGAVertex.fpga_id)
    def fpga_id(self):
        return self._fpga_id

    @property
    @overrides(AbstractFPGAVertex.fpga_link_id)
    def fpga_link_id(self):
        return self._fpga_link_id

    @property
    @overrides(AbstractVirtualVertex.board_address)
    def board_address(self):
        return self._board_address

    @property
    @overrides(AbstractVirtualVertex.virtual_chip_x)
    def virtual_chip_x(self):
        return self._virtual_chip_x

    @property
    @overrides(AbstractVirtualVertex.virtual_chip_y)
    def virtual_chip_y(self):
        return self._virtual_chip_y

    @overrides(AbstractVirtualVertex.set_virtual_chip_coordinates)
    def set_virtual_chip_coordinates(self, virtual_chip_x, virtual_chip_y):
        self._virtual_chip_x = virtual_chip_x
        self._virtual_chip_y = virtual_chip_y
