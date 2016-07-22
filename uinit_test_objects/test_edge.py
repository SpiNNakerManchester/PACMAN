from pacman.model.graph.application.simple_application_edge import \
    SimpleApplicationEdge
from pacman.model.graph.machine.simple_machine_edge import \
    SimpleMachineEdge


class TestEdge(SimpleApplicationEdge):
    """
    test class for creating edges
    """

    def __init__(self, pre_vertex, post_vertex, label=None, constraints=None):
        SimpleApplicationEdge.__init__(
            self, pre_vertex, post_vertex, constraints, label)

    def create_machine_edge(self, pre_vertex, post_vertex, constraints=None,
                       label=None):
        """ method to create edges

        :param pre_vertex:
        :param post_vertex:
        :param constraints:
        :param label:
        :return:
        """
        if constraints is not None:
            if self._constraints is not None:
                constraints.extend(self._constraints)
        else:
            constraints = self._constraints
            print constraints
        return SimpleMachineEdge(pre_vertex, post_vertex,
                                        label, constraints)
        :return:
        """
        return True