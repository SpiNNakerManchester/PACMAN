from six import add_metaclass
import sys

from pacman.model.constraints.partitioner_constraints.\
    partitioner_maximum_size_constraint import \
    PartitionerMaximumSizeConstraint
from pacman.model.graphs import AbstractVertex
from spinn_utilities.abstract_base import abstractmethod, abstractproperty, AbstractBase


@add_metaclass(AbstractBase)
class ApplicationVertex(AbstractVertex):
    """ A vertex that can be broken down into a number of smaller vertices
        based on the resources that the vertex requires
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
        :param max_atoms_per_core: the max number of atoms that can be\
            placed on a core, used in partitioning
        :type max_atoms_per_core: int
        :raise pacman.exceptions.PacmanInvalidParameterException:\
                    * If one of the constraints is not valid
        """
        AbstractVertex.__init__(self, label, constraints)

        # add a constraint for max partitioning
        self.add_constraint(
            PartitionerMaximumSizeConstraint(max_atoms_per_core))

    def __str__(self):
        return self.label

    def __repr__(self):
        return "ApplicationVertex(label={}, constraints={}".format(
            self.label, self.constraints)

    @abstractmethod
    def get_resources_used_by_atoms(self, vertex_slice):
        """ Get the separate resource requirements for a range of atoms

        :param vertex_slice: the low value of atoms to calculate resources from
        :type vertex_slice: :py:class:`pacman.model.graph.slice.Slice`
        :return: a Resource container that contains a \
                    CPUCyclesPerTickResource, DTCMResource and SDRAMResource
        :rtype: ResourceContainer
        :raise None: this method does not raise any known exception
        """

    @abstractmethod
    def create_machine_vertex(
            self, vertex_slice, resources_required, label=None,
            constraints=None):
        """ Create a machine vertex from this application vertex

        :param vertex_slice:\
            The slice of atoms that the machine vertex will cover
        :param resources_required: the resources used by the machine vertex
        :param constraints: Constraints to be passed on to the machine vertex
        """

    @abstractproperty
    def n_atoms(self):
        """ The number of atoms in the vertex

        :return: The number of atoms
        :rtype: int
        """
