from pacman.model.graphs.application.application_edge import ApplicationEdge
from pacman.model.graphs.application.application_vertex \
    import ApplicationVertex
from pacman.model.graphs import AbstractOutgoingEdgePartition
from pacman.model.graphs.impl.graph import Graph


class ApplicationGraph(Graph):
    """ An application-level abstraction of a graph
    """

    __slots__ = []

    def __init__(self, label):
        Graph.__init__(self, ApplicationVertex, ApplicationEdge,
                       AbstractOutgoingEdgePartition, label)
