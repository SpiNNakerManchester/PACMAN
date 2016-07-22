from pacman.model.graph.abstract_vertex import AbstractVertex

from abc import ABCMeta
from six import add_metaclass
from abc import abstractmethod
from abc import abstractproperty


@add_metaclass(ABCMeta)
class AbstractApplicationVertex(AbstractVertex):
    """ A vertex that can be broken down into a number of smaller vertices\
        based on the resources that the vertex requires
    """

    __slots__ = ()

    @abstractmethod
    def get_resources_used_by_atoms(self, vertex_slice):
        """ Get the separate resource requirements for a range of atoms

        :param vertex_slice: the low value of atoms to calculate resources from
        :param graph: A reference to the graph containing this vertex.
        :type vertex_slice: :py:class:`pacman.model.graph.slice.Slice`
        :return: a Resource container that contains a \
                    CPUCyclesPerTickResource, DTCMResource and SDRAMResource
        :rtype: ResourceContainer
        :raise None: this method does not raise any known exception
        """

    @abstractproperty
    def max_atoms_per_core(self):
        """ Get the maximum number of atoms that can be run on a single core \
            given the constraints set on this vertex

        :rtype: int
        """

    @abstractmethod
    def create_machine_vertex(
            self, vertex_slice, constraints=None):
        """ Create a machine vertex from this application vertex

        :param vertex_slice:\
            The slice of atoms that the machine vertex will cover
        :param constraints: Constraints to be passed on to the machine vertex
        """

    @abstractproperty
    def n_atoms(self):
        """ The number of atoms in the vertex

        :return: The number of atoms
        :rtype: int
        """
