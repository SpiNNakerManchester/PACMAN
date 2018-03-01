from .machine_vertex import MachineVertex
from spinn_utilities.overrides import overrides


class SimpleMachineVertex(MachineVertex):
    """ A MachineVertex that stores its own resources
    """

    def __init__(self, resources, label=None, constraints=None):
        super(SimpleMachineVertex, self).__init__(
            label=label, constraints=constraints)
        self._resources = resources

    @property
    @overrides(MachineVertex.resources_required)
    def resources_required(self):
        return self._resources
