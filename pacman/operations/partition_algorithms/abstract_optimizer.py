
class AbstractPartitioner(object):
    __slots__ = (
        # an application graph
        "application_graph"
        )

    def __init__(self, application_graph: Optional[str] = None):
        self._application_graph = application_graph

    def application_graph(self):
        return self._application_graph
