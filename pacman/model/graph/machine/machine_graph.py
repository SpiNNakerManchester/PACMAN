from pacman.model.graph.simple_graph import SimpleGraph
from pacman.model.graph.machine.abstract_machine_vertex import AbstractMachineVertex
from pacman.model.graph.machine.abstract_machine_edge import AbstractMachineEdge


class MachineGraph(SimpleGraph):
    """ A graph whose vertices can fit on the chips of a machine
    """

    def __init__(self):
        SimpleGraph.__init__(
            self, [AbstractMachineVertex], [AbstractMachineEdge])
