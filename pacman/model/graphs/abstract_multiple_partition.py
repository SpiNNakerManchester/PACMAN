from collections import OrderedDict

from pacman.exceptions import PacmanConfigurationException
from spinn_utilities.ordered_default_dict import DefaultOrderedDict
from spinn_utilities.ordered_set import OrderedSet


class AbstractMultiplePartition(object):

    def __init__(self, pre_vertices):
        self._pre_vertices = OrderedDict()
        self._destinations = DefaultOrderedDict(OrderedSet)

        # hard code dict of lists so that only these are acceptable.
        for pre_vertex in pre_vertices:
            self._pre_vertices[pre_vertex] = OrderedSet()

        # handle clones
        if len(self._pre_vertices.keys()) != len(pre_vertices):
            raise PacmanConfigurationException(
                "there were clones in your list of acceptable pre vertices")

    def add_edge(self, edge):
        # safety checks
        if edge.pre_vertex not in self._pre_vertices.keys():
            raise Exception(
                "th edge {} is not allowed in this outgoing partition".format(
                    edge))

        # update
        self._pre_vertices[edge.pre_vertex].add(edge)
        self._destinations[edge.post_vertex].add(edge)

    @property
    def pre_vertices(self):
        return self._pre_vertices.keys()
