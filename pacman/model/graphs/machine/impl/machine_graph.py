from pacman.model.abstract_classes.abstract_has_label import AbstractHasLabel
from pacman.model.decorators.overrides import overrides

from pacman.model.graphs.abstract_outgoing_edge_partition import \
    AbstractOutgoingEdgePartition
from pacman.model.graphs.impl.graph import Graph
from pacman.model.graphs.machine.abstract_machine_edge \
    import AbstractMachineEdge
from pacman.model.graphs.machine.abstract_machine_vertex \
    import AbstractMachineVertex


class MachineGraph(Graph, AbstractHasLabel):
    """ A graph whose vertices can fit on the chips of a machine
    """

    __slots__ = (
        # the label for this machine graph
        "_label"
    )

    def __init__(self, label):
        Graph.__init__(
            self, AbstractMachineVertex, AbstractMachineEdge,
            AbstractOutgoingEdgePartition)
        AbstractHasLabel.__init__(self)
        self._label = label

    @overrides(AbstractHasLabel.label)
    def label(self):
        return self._label

    @property
    @overrides(AbstractHasLabel.model_name)
    def model_name(self):
        return "MachineGraph"
