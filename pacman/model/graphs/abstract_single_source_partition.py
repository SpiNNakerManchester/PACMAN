from pacman.exceptions import PacmanConfigurationException


class AbstractSingleSourcePartition(object):

    def __init__(self, pre_vertex):
        self._pre_vertex = pre_vertex

    def add_edge(self, edge):
        if edge.pre_vertex != self._pre_vertex:
            raise PacmanConfigurationException(
                "A partition can only contain edges with the same pre_vertex")

    @property
    def pre_vertex(self):
        return self._pre_vertex
