from pacman.model.graphs.simple_outgoing_edge_partition \
    import SimpleOutgoingEdgePartition

from pacman.model.graphs.application.abstract_application_edge \
    import AbstractApplicationEdge


class ApplicationOutgoingEdgePartition(SimpleOutgoingEdgePartition):

    __slots__ = ()

    def __init__(self, identifier, constraints=None, label=None):
        SimpleOutgoingEdgePartition.__init__(
            self, identifier, AbstractApplicationEdge, constraints, label)
