from .application_edge import ApplicationEdge
from pacman.model.graphs.impl import OutgoingEdgePartition


class ApplicationOutgoingEdgePartition(OutgoingEdgePartition):
    """ edge partition for the application graph.

    """

    __slots__ = ()

    def __init__(self, identifier, constraints=None, label=None):
        super(ApplicationOutgoingEdgePartition, self).__init__(
            identifier, ApplicationEdge, constraints, label)
