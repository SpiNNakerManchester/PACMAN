from pacman.model.partitioned_graph.partitioned_vertex import PartitionedVertex
from pacman.model.constraints.placer_constraints\
    .placer_chip_and_core_constraint import PlacerChipAndCoreConstraint


class VirtualSataLinkPartitionedVertex(PartitionedVertex):

    def __init__(
            self, resources_required, label, fpga_link_id, fpga_id,
            board_address=None, constraints=None):
        PartitionedVertex.__init__(
            self, resources_required, label, constraints=constraints)

        self._fpga_link_id = fpga_link_id
        self._fpga_id = fpga_id
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
    def fpga_link_id(self):
        return self._fpga_link_id

    @property
    def fpga_id(self):
        return self._fpga_id

    @property
    def board_address(self):
        return self._board_address
