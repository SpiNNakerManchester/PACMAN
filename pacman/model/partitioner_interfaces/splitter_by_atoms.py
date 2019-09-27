from six import add_metaclass
from spinn_utilities.abstract_base import (
    AbstractBase, abstractmethod, abstractproperty)


@add_metaclass(AbstractBase)
class SplitterByAtoms(object):

    @abstractmethod
    def get_resources_used_by_atoms(self, vertex_slice):
        """ Get the separate resource requirements for a range of atoms

        :param vertex_slice: the low value of atoms to calculate resources from
        :type vertex_slice: :py:class:`pacman.model.graphs.common.Slice`
        :return: a Resource container that contains a \
            CPUCyclesPerTickResource, DTCMResource and SDRAMResource
        :rtype: :py:class:`pacman.model.resources.ResourceContainer`
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
