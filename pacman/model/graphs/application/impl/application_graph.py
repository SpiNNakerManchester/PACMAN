from pacman.model.abstract_classes.abstract_has_label import AbstractHasLabel
from pacman.model.decorators.overrides import overrides

from pacman.model.graphs.abstract_outgoing_edge_partition import \
    AbstractOutgoingEdgePartition
from pacman.model.graphs.impl.graph import Graph
from pacman.model.graphs.application.abstract_application_edge \
    import AbstractApplicationEdge
from pacman.model.graphs.application.abstract_application_vertex \
    import AbstractApplicationVertex


class ApplicationGraph(Graph, AbstractHasLabel):
    """ An application-level abstraction of a graph
    """

    __slots__ = (
        # the label for this application graph
        "_label"
    )

    def __init__(self, label):
        Graph.__init__(
            self, [AbstractApplicationVertex], [AbstractApplicationEdge],
            [AbstractOutgoingEdgePartition])
        AbstractHasLabel.__init__(self)

        self._label = label

    @overrides(AbstractHasLabel.label())
    def label(self):
        return self._label
