import sys

from pacman.model.abstract_classes.impl.constrained_object \
    import ConstrainedObject
from pacman.model.constraints.partitioner_constraints.\
    partitioner_maximum_size_constraint import \
    PartitionerMaximumSizeConstraint
from pacman.model.decorators.delegates_to import delegates_to
from pacman.model.decorators.overrides import overrides
from pacman.model.graphs.application.abstract_application_vertex import \
    AbstractApplicationVertex


class ApplicationVertex(AbstractApplicationVertex):
    """ A simple implementation of a application vertex
    """

    __slots__ = [

        # The label
        "_label",

        # The constraints delegate
        "_constraints"
    ]

    def __init__(self, label=None, constraints=None,
                 max_atoms_per_core=sys.maxint):
        """
        :param label: The optional name of the vertex
        :type label: str
        :param constraints: The optional initial constraints of the vertex
        :type constraints: \
            iterable of\
            :py:class:`pacman.model.constraints.abstract_constraint.AbstractConstraint`
        :param max_atoms_per_core: the max number of atoms that can be
            placed on a core, used in partitioning
        :type max_atoms_per_core: int
        :raise pacman.exceptions.PacmanInvalidParameterException:
                    * If one of the constraints is not valid
        """
        self._label = label

        AbstractApplicationVertex.__init__(self)
        self._constraints = ConstrainedObject(constraints)

        # add a constraint for max partitioning
        self._constraints.add_constraint(
            PartitionerMaximumSizeConstraint(max_atoms_per_core))

    @delegates_to("_constraints", ConstrainedObject.add_constraint)
    def add_constraint(self, constraint):
        pass

    @delegates_to("_constraints", ConstrainedObject.add_constraints)
    def add_constraints(self, constraints):
        pass

    @delegates_to("_constraints", ConstrainedObject.constraints)
    def constraints(self):
        pass

    @property
    @overrides(AbstractApplicationVertex.label)
    def label(self):
        return self._label

    def __str__(self):
        return self._label

    def __repr__(self):
        return (
            "ApplicationVertex(label={}, constraints={}"
            .format(self.constraints, self._label))
