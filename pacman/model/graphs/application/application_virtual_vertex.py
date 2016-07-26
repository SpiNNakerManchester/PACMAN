# pacman imports
from pacman.model.abstract_classes.simple_constrained_object \
    import SimpleConstrainedObject
from pacman.model.decorators.delegates_to import delegates_to
from pacman.model.decorators.overrides import overrides
from pacman.model.graphs.abstract_classes.abstract_virtual_application_vertex \
    import AbstractVirtualApplicationVertex
from pacman.model.graphs.machine.simple_virtual_machine_vertex \
    import SimpleVirtualMachineVertex


class ApplicationVirtualVertex(AbstractVirtualApplicationVertex):
    """ A simple implementation of the AbstractVirtualApplicationVertex
    """

    __slots__ = [

        # The number of atoms
        "_n_atoms",

        # The spinnaker link id
        "_spinnaker_link_id",

        # The label
        "_label",

        # The constraints delegate
        "_constraints"
    ]

    def __init__(
            self, n_atoms, spinnaker_link_id, label=None, constraints=None):

        self._n_atoms = n_atoms
        self._spinnaker_link_id = spinnaker_link_id
        self._label = label

        self._constraints = SimpleConstrainedObject(constraints)

    @delegates_to("_constraints", SimpleConstrainedObject.add_constraint)
    def add_constraint(self, constraint):
        pass

    @delegates_to("_constraints", SimpleConstrainedObject.add_constraints)
    def add_constraints(self, constraints):
        pass

    @delegates_to("_constraints", SimpleConstrainedObject.constraints)
    def constraints(self):
        pass

    @property
    @overrides(AbstractVirtualApplicationVertex.label)
    def label(self):
        return self._label

    @overrides(AbstractVirtualApplicationVertex.create_machine_vertex)
    def create_machine_vertex(self, vertex_slice, constraints=None):
        machine_vertex = SimpleVirtualMachineVertex(
            self._spinnaker_link_id, constraints=constraints)
        return machine_vertex

    @property
    @overrides(AbstractVirtualApplicationVertex.spinnaker_link_id)
    def spinnaker_link_id(self):
        return self._spinnaker_link_id
