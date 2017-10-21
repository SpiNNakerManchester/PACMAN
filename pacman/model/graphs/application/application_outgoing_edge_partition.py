from .application_edge import ApplicationEdge
from pacman.model.graphs.impl import OutgoingEdgePartition


class ApplicationOutgoingEdgePartition(OutgoingEdgePartition):
    """ edge partition for the application graph.

    """

    __slots__ = ()

    def __init__(self, identifier, constraints=None, label=None):
        OutgoingEdgePartition.__init__(
            self, identifier, ApplicationEdge, constraints, label)
