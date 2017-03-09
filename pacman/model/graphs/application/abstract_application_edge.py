from abc import abstractmethod

from pacman.model.graphs.abstract_edge import AbstractEdge


class AbstractApplicationEdge(AbstractEdge):
    """ a application edge between two application vertices

    """

    __slots__ = ()

    def __init__(self, label):
        AbstractEdge.__init__(self, label)

    @abstractmethod
    def create_machine_edge(self, pre_vertex, post_vertex, label):
        """ Create a machine edge between two machine vertices

        :param pre_vertex: The machine vertex at the start of the edge
        :type pre_vertex:\
            :py:class:`pacman.model.graph.machine.abstract_machine_vertex.AbstractMachineVertex`
        :param post_vertex: The machine vertex at the end of the edge
        :type post_vertex:\
            :py:class:`pacman.model.graph.machine.abstract_machine_vertex.AbstractMachineVertex`
        :param label: label of the edge
        :type label: str
        :return: The created machine edge
        :rtype:\
            :py:class:`pacman.model.graph.machine.abstract_machine_edge.AbstractMachineEdge`
        """
