from pacman.model.graphs.simple_graph import SimpleGraph

from pacman.model.graphs.machine.abstract_machine_edge \
    import AbstractMachineEdge
from pacman.model.graphs.machine.abstract_machine_vertex \
    import AbstractMachineVertex


class MachineGraph(SimpleGraph):
    """ A graph whose vertices can fit on the chips of a machine
    """

    __slots__ = ()

    def __init__(self):
        SimpleGraph.__init__(
            self, [AbstractMachineVertex], [AbstractMachineEdge])
