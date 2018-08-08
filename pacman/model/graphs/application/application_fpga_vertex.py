from spinn_utilities.overrides import overrides
from pacman.model.constraints.placer_constraints\
    import ChipAndCoreConstraint
from .application_vertex import ApplicationVertex
from pacman.model.graphs import AbstractFPGAVertex, AbstractVirtualVertex
from pacman.model.resources import ResourceContainer
from pacman.model.graphs.machine.machine_fpga_vertex \
    import MachineFPGAVertex

import sys


class ApplicationFPGAVertex(ApplicationVertex, AbstractFPGAVertex):
    """ A virtual vertex on an FPGA link.
    """

    __slots__ = [
        "_fpga_id",
        "_fpga_link_id",
        "_board_address",
        "_virtual_chip_x",
        "_virtual_chip_y",
        "_n_atoms"]

    def __init__(
            self, n_atoms, fpga_id, fpga_link_id, board_address=None,
            label=None, constraints=None, max_atoms_per_core=sys.maxsize):
        super(ApplicationFPGAVertex, self).__init__(
            label=label, constraints=constraints,
            max_atoms_per_core=max_atoms_per_core)

        self._n_atoms = n_atoms
        self._fpga_id = fpga_id
        self._fpga_link_id = fpga_link_id
        self._board_address = board_address
        self._virtual_chip_x = None
        self._virtual_chip_y = None

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
        self.add_constraint(ChipAndCoreConstraint(
            self._virtual_chip_x, self._virtual_chip_y))

    @property
    @overrides(ApplicationVertex.n_atoms)
    def n_atoms(self):
        return self._n_atoms

    @overrides(ApplicationVertex.get_resources_used_by_atoms)
    def get_resources_used_by_atoms(self, vertex_slice):
        return ResourceContainer()

    @overrides(ApplicationVertex.create_machine_vertex)
    def create_machine_vertex(
            self, vertex_slice, resources_required, label=None,
            constraints=None):
        vertex = MachineFPGAVertex(
            self._fpga_id, self._fpga_link_id, self._board_address,
            label, constraints)
        vertex.set_virtual_chip_coordinates(
            self._virtual_chip_x, self._virtual_chip_y)
        return vertex
