from pacman.model.graph.simple_graph import SimpleGraph
from pacman.model.graph.application.abstract_application_vertex \
    import AbstractApplicationVertex
from pacman.model.graph.application.abstract_application_edge \
    import AbstractApplicationEdge


class ApplicationGraph(SimpleGraph):
    """ An application-level abstraction of a graph
    """

    __slots__ = ()

    def __init__(self):
        SimpleGraph.__init__(
            self, AbstractApplicationVertex, AbstractApplicationEdge)
