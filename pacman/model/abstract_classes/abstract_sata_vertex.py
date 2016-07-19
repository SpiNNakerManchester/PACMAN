from pacman.model.abstract_classes.abstract_virtual_vertex import \
    AbstractVirtualVertex
from pacman import exceptions

# general imports
from abc import ABCMeta
from six import add_metaclass

from pacman.model.partitioned_graph.virtual_sata_partitioned_vertex import \
    VirtualSataLinkPartitionedVertex


@add_metaclass(ABCMeta)
class AbstractSATAVertex(AbstractVirtualVertex):

    def __init__(
            self, n_neurons, fpga_link_id, fpga_id, machine_time_step,
            timescale_factor, board_address=None, label=None):
        AbstractVirtualVertex.__init__(
            self, n_atoms=n_neurons, board_address=board_address, label=label,
            max_atoms_per_core=n_neurons)

        self._fpga_link_id = fpga_link_id
        self._fpga_id = fpga_id

        if self._fpga_id is None or self._fpga_link_id is None:
            raise exceptions.PacmanConfigurationException(
                "The sata vertex needs to connec to a fpga via a link and "
                "fpga id. Please refer to spin4-5.pdf found here for more "
                "details. https://drive.google.com/drive/folders/"
                "0B9312BuJXntlb2w0OGx1OVU5cmc")

    @property
    def model_name(self):
        return "SATAVertex:{}".format(self.label)

    def is_virtual_vertex(self):
        return True

    @property
    def fpga_link_id(self):
        return self._fpga_link_id

    @property
    def fpga_id(self):
        return self._fpga_id

    def create_subvertex(
            self, vertex_slice, resources_required, label=None,
            constraints=None):
        subvertex = VirtualSataLinkPartitionedVertex(
            resources_required=resources_required, label=label,
            fpga_link_id=self._fpga_link_id, fpga_id=self._fpga_id,
            constraints=constraints)

        subvertex.set_virtual_chip_coordinates(
            self._virtual_chip_x, self._virtual_chip_y, self._real_chip_x,
            self._real_chip_y, self._real_link)
        return subvertex
