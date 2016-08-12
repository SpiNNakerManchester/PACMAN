from pacman.model.graphs.impl.outgoing_edge_partition \
    import OutgoingEdgePartition

from pacman.model.graphs.application.abstract_application_edge \
    import AbstractApplicationEdge


class ApplicationOutgoingEdgePartition(OutgoingEdgePartition):
    """ edge partition for the application graph.

    """

    __slots__ = ()

    def __init__(self, identifier, constraints=None, label=None):
        OutgoingEdgePartition.__init__(
            self, identifier, AbstractApplicationEdge, constraints, label)
