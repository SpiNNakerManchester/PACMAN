from pacman.model.partitioned_graph.abstract_virtual_partitioned_vertex import \
    AbstractVirtualPartitionedVertex


class VirtualSataLinkPartitionedVertex(AbstractVirtualPartitionedVertex):

    def __init__(
            self, resources_required, label, fpga_link_id, fpga_id,
            board_address=None, constraints=None):
        AbstractVirtualPartitionedVertex.__init__(
            self, resources_required, label, board_address, constraints)

        self._fpga_link_id = fpga_link_id
        self._fpga_id = fpga_id

    @property
    def fpga_link_id(self):
        return self._fpga_link_id

    @property
    def fpga_id(self):
        return self._fpga_id
