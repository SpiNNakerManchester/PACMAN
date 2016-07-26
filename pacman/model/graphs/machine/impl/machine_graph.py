from pacman.model.graphs.abstract_outgoing_edge_partition import \
    AbstractOutgoingEdgePartition
from pacman.model.graphs.impl.graph import Graph
from pacman.model.graphs.machine.abstract_machine_edge \
    import AbstractMachineEdge
from pacman.model.graphs.machine.abstract_machine_vertex \
    import AbstractMachineVertex


class MachineGraph(Graph):
    """ A graph whose vertices can fit on the chips of a machine
    """

    __slots__ = ()

    def __init__(self):
        Graph.__init__(
            self, [AbstractMachineVertex], [AbstractMachineEdge],
            [AbstractOutgoingEdgePartition])
