from pacman.model.graphs.machine.machine_vertex import MachineVertex
from pacman.model.graphs.machine.machine_edge import MachineEdge
from pacman.model.graphs import AbstractOutgoingEdgePartition
from pacman.model.graphs.impl.graph import Graph


class MachineGraph(Graph):
    """ A graph whose vertices can fit on the chips of a machine
    """

    __slots__ = []

    def __init__(self, label):
        Graph.__init__(
            self, MachineVertex, MachineEdge,
            AbstractOutgoingEdgePartition, label)
