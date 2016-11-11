from pacman.model.decorators.overrides import overrides
from pacman.model.resources.resource_container import ResourceContainer
from pacman.model.resources.dtcm_resource import DTCMResource
from pacman.model.resources.sdram_resource import SDRAMResource
from pacman.model.graphs.machine.impl.machine_vertex import MachineVertex
from pacman.model.graphs.abstract_spinnaker_link_vertex \
    import AbstractSpiNNakerLinkVertex
from pacman.model.resources.cpu_cycles_per_tick_resource \
    import CPUCyclesPerTickResource


class MachineSpiNNakerLinkVertex(MachineVertex, AbstractSpiNNakerLinkVertex):
    """ A virtual vertex on a SpiNNaker Link
    """

    __slots__ = (
        "_spinnaker_link_id",
        "_board_address",
        "_virtual_chip_x",
        "_virtual_chip_y"
    )

    def __init__(
            self, spinnaker_link_id, board_address=None, label=None,
            constraints=None):
        MachineVertex.__init__(self, label=label, constraints=constraints)
        AbstractSpiNNakerLinkVertex.__init__(self)
        self._spinnaker_link_id = spinnaker_link_id
        self._board_address = board_address
        self._virtual_chip_x = None
        self._virtual_chip_y = None

    @property
    @overrides(MachineVertex.resources_required)
    def resources_required(self):
        return ResourceContainer(
            dtcm=DTCMResource(0), sdram=SDRAMResource(0),
            cpu_cycles=CPUCyclesPerTickResource(0))

    @property
    @overrides(AbstractSpiNNakerLinkVertex.spinnaker_link_id)
    def spinnaker_link_id(self):
        return self._spinnaker_link_id

    @property
    @overrides(AbstractSpiNNakerLinkVertex.board_address)
    def board_address(self):
        return self._board_address

    @property
    @overrides(AbstractSpiNNakerLinkVertex.virtual_chip_x)
    def virtual_chip_x(self):
        return self._virtual_chip_x

    @property
    @overrides(AbstractSpiNNakerLinkVertex.virtual_chip_y)
    def virtual_chip_y(self):
        return self._virtual_chip_y

    @overrides(AbstractSpiNNakerLinkVertex.set_virtual_chip_coordinates)
    def set_virtual_chip_coordinates(self, virtual_chip_x, virtual_chip_y):
        self._virtual_chip_x = virtual_chip_x
        self._virtual_chip_y = virtual_chip_y
