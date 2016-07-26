from abc import abstractproperty

from pacman.model.graphs.abstract_classes.abstract_edge import AbstractEdge


class AbstractMachineEdge(AbstractEdge):
    """ An edge of a machine graph
    """

    __slots__ = ()

    @abstractproperty
    def traffic_weight(self):
        """ The amount of traffic expected to go down this edge relative to\
            other edges
        """
