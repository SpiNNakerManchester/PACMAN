from .application_edge import ApplicationEdge
from .application_vertex import ApplicationVertex
from pacman.model.graphs import AbstractOutgoingEdgePartition
from pacman.model.graphs.impl import Graph


class ApplicationGraph(Graph):
    """ An application-level abstraction of a graph
    """

    __slots__ = []

    def __init__(self, label):
        super(ApplicationGraph, self).__init__(
            ApplicationVertex, ApplicationEdge, AbstractOutgoingEdgePartition,
            label)
