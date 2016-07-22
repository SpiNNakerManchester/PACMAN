from pacman.model.graph.abstract_edge import AbstractEdge
from abc import abstractproperty


class AbstractMachineEdge(AbstractEdge):
    """ An edge of a machine graph
    """

    @abstractproperty
    def traffic_weight(self):
        """ The amount of traffic expected to go down this edge relative to\
            other edges
        """
