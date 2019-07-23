from pacman.model.graphs.application import ApplicationEdge


class SimpleTestEdge(ApplicationEdge):
    """
    test class for creating edges
    """

    def __init__(self, pre_vertex, post_vertex, label=None):
        super(SimpleTestEdge, self).__init__(
            pre_vertex, post_vertex, label=label)
