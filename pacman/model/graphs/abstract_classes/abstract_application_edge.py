from abc import abstractmethod

from pacman.model.graphs.abstract_classes.abstract_edge import AbstractEdge


class AbstractApplicationEdge(AbstractEdge):

    __slots__ = ()

    @abstractmethod
    def create_machine_edge(self, pre_vertex, post_vertex):
        """ Create a machine edge between two machine vertices

        :param pre_vertex: The machine vertex at the start of the edge
        :type pre_vertex:\
            :py:class:`pacman.model.graph.machine.abstract_machine_vertex.AbstractMachineVertex`
        :param post_vertex: The machine vertex at the end of the edge
        :type post_vertex:\
            :py:class:`pacman.model.graph.machine.abstract_machine_vertex.AbstractMachineVertex`
        :return: The created machine edge
        :rtype:\
            :py:class:`pacman.model.graph.machine.abstract_machine_edge.AbstractMachineEdge`
        """
