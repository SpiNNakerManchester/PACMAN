from pacman.model.decorators.overrides import overrides
from pacman.model.graphs.abstract_virtual_vertex \
    import AbstractVirtualVertex
from pacman.model.graphs.machine.abstract_machine_vertex \
    import AbstractMachineVertex
from pacman.model.resources.resource_container import ResourceContainer


class AbstractMachineVirtualVertex(
        AbstractVirtualVertex, AbstractMachineVertex):
    """ A machine vertex that is virtual
    """

    __slots__ = ()

    @property
    @overrides(AbstractMachineVertex.resources_required)
    def resources_required(self):
        return ResourceContainer()
