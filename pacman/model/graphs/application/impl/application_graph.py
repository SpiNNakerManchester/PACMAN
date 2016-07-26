from pacman.model.graphs.impl.graph import Graph

from pacman.model.graphs.application.abstract_application_edge \
    import AbstractApplicationEdge
from pacman.model.graphs.application.abstract_application_vertex \
    import AbstractApplicationVertex


class ApplicationGraph(Graph):
    """ An application-level abstraction of a graph
    """

    __slots__ = ()

    def __init__(self):
        Graph.__init__(
            self, AbstractApplicationVertex, AbstractApplicationEdge,
        )
