from pacman.model.graphs.application.impl.application_edge \
    import ApplicationEdge


class TestEdge(ApplicationEdge):
    """
    test class for creating edges
    """

    def __init__(self, pre_vertex, post_vertex, label=None):
        ApplicationEdge.__init__(
            self, pre_vertex, post_vertex, label=label)
