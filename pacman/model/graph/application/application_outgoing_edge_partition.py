from pacman.model.graph.application.abstract_application_edge\
    import AbstractApplicationEdge
from pacman.model.graph.simple_outgoing_edge_partition \
    import SimpleOutgoingEdgePartition


class ApplicationOutgoingEdgePartition(SimpleOutgoingEdgePartition):

    __slots__ = ()

    def __init__(self, identifier, constraints=None, label=None):
        SimpleOutgoingEdgePartition.__init__(
            self, identifier, AbstractApplicationEdge, constraints, label)
