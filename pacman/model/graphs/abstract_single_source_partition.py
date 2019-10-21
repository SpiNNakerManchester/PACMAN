from pacman.exceptions import PacmanConfigurationException


class AbstractSingleSourcePartition(object):

    def __init__(self):
        self._pre_vertex = None

    def add_edge(self, edge):
        # Check for an incompatible pre vertex
        if self._pre_vertex is None:
            self._pre_vertex = edge.pre_vertex

        elif edge.pre_vertex != self._pre_vertex:
            raise PacmanConfigurationException(
                "A partition can only contain edges with the same"
                "pre_vertex")

    @property
    def pre_vertex(self):
        return self._pre_vertex
