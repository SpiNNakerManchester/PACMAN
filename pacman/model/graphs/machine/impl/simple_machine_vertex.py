from pacman.model.graphs.machine.impl.machine_vertex import MachineVertex
from pacman.model.decorators.overrides import overrides
from pacman.model.graphs.machine.abstract_machine_vertex \
    import AbstractMachineVertex


class SimpleMachineVertex(MachineVertex):
    """ A MachineVertex that stores its own resources
    """

    def __init__(self, resources, label=None, constraints=None):
        MachineVertex.__init__(self, label=label, constraints=constraints)
        self._resources = resources

    @property
    @overrides(AbstractMachineVertex.resources_required)
    def resources_required(self):
        return self._resources
