import sys

from pacman.model.constraints.partitioner_constraints.\
    partitioner_maximum_size_constraint import \
    PartitionerMaximumSizeConstraint
from pacman.model.graphs.application.abstract_application_vertex import \
    AbstractApplicationVertex


class ApplicationVertex(AbstractApplicationVertex):
    """ A simple implementation of a application vertex
    """

    __slots__ = []

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
        AbstractApplicationVertex.__init__(self, label, constraints)

        # add a constraint for max partitioning
        self.add_constraint(
            PartitionerMaximumSizeConstraint(max_atoms_per_core))

    def __str__(self):
        return self.label

    def __repr__(self):
        return "ApplicationVertex(label={}, constraints={}".format(
            self.label, self.constraints)
