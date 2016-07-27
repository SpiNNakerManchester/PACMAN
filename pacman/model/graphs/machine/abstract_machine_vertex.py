from abc import abstractproperty
from abc import abstractmethod

from pacman.model.graphs.abstract_vertex import AbstractVertex


class AbstractMachineVertex(AbstractVertex):
    """ A vertex of a graph which has certain resource requirements
    """

    __slots__ = ()

    @abstractproperty
    def resources_required(self):
        """ The resources required by the vertex

        :rtype:\
            :py:class:`pacman.model.resources.resource_container.ResourceContainer`
        """

    @abstractmethod
    def set_resources_required(self, resource_required):
        """ sets the reosurces required for a given vertex

        :return:  None
        """