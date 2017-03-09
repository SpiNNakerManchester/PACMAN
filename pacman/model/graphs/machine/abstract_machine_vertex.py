from abc import abstractproperty

from pacman.model.graphs.abstract_vertex import AbstractVertex


class AbstractMachineVertex(AbstractVertex):
    """ A vertex of a graph which has certain resource requirements
    """

    __slots__ = ()

    def __init__(self, label, constraints):
        AbstractVertex.__init__(self, label, constraints)

    @abstractproperty
    def resources_required(self):
        """ The resources required by the vertex

        :rtype:\
            :py:class:`pacman.model.resources.resource_container.ResourceContainer`
        """
