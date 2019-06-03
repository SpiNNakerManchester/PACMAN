import sys
from six import add_metaclass
from spinn_utilities.overrides import overrides
from spinn_utilities.abstract_base import (
    abstractmethod, abstractproperty, AbstractBase)
from pacman.model.constraints.partitioner_constraints import (
    MaxVertexAtomsConstraint)
from pacman.model.graphs import AbstractVertex
from pacman.model.graphs.common import ConstrainedObject


@add_metaclass(AbstractBase)
class ApplicationVertex(ConstrainedObject, AbstractVertex):
    """ A vertex that can be broken down into a number of smaller vertices
        based on the resources that the vertex requires.
    """

    __slots__ = ["_label"]

    def __init__(self, label=None, constraints=None,
                 max_atoms_per_core=sys.maxsize):
        """
        :param label: The optional name of the vertex
        :type label: str
        :param constraints: The optional initial constraints of the vertex
        :type constraints: \
            iterable(:py:class:`pacman.model.constraints.AbstractConstraint`)
        :param max_atoms_per_core: the max number of atoms that can be\
            placed on a core, used in partitioning
        :type max_atoms_per_core: int
        :raise pacman.exceptions.PacmanInvalidParameterException:\
            * If one of the constraints is not valid
        """

        super(ApplicationVertex, self).__init__(constraints)
        self._label = label

        # add a constraint for max partitioning
        self.add_constraint(
            MaxVertexAtomsConstraint(max_atoms_per_core))

    @property
    @overrides(AbstractVertex.label)
    def label(self):
        return self._label

    def __str__(self):
        return self.label

    def __repr__(self):
        return "ApplicationVertex(label={}, constraints={}".format(
            self.label, self.constraints)

    @abstractproperty
    def n_atoms(self):
        """ The number of atoms in the vertex

        :return: The number of atoms
        :rtype: int
        """

    def get_max_atoms_per_core(self):
        for constraint in self.constraints:
            if isinstance(constraint, MaxVertexAtomsConstraint):
                return constraint.size
        return self.n_atoms
