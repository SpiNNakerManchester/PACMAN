from pacman.model.abstract_classes.simple_constrained_object \
    import SimpleConstrainedObject
from pacman.model.decorators.delegates_to import delegates_to
from pacman.model.decorators.overrides import overrides
from pacman.model.graphs.machine.abstract_machine_virutal_vertex  \
    import AbstractMachineVirtualVertex


class MachineVirtualVertex(AbstractMachineVirtualVertex):
    """ A simple implementation of a Virtual Machine vertex
    """

    __slots__ = [

        # The spinnaker link id
        "_spinnaker_link_id",

        # The label
        "_label",

        # The constraints delegate
        "_constraints"
    ]

    def __init__(self, spinnaker_link_id, label=None, constraints=None):
        self._spinnaker_link_id = spinnaker_link_id
        self._label = label

        self._constraints = SimpleConstrainedObject(constraints)
        AbstractMachineVirtualVertex.__init__(self)

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
    @overrides(AbstractMachineVirtualVertex.label)
    def label(self):
        return self._label

    @property
    @overrides(AbstractMachineVirtualVertex.spinnaker_link_id)
    def spinnaker_link_id(self):
        return self._spinnaker_link_id
