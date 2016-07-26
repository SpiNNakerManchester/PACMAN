from pacman.model.graphs.simple_outgoing_edge_partition\
    import SimpleOutgoingEdgePartition

from pacman.model.graphs.machine.abstract_machine_edge \
    import AbstractMachineEdge


class MachineOutgoingEdgePartition(SimpleOutgoingEdgePartition):
    """ An outgoing edge partition for a Machine Graph
    """

    __slots__ = ()

    def __init__(self, identifier, constraints=None, label=None):
        """

        :param identifier: The identifier of the partition
        :param constraints: Any initial constraints
        :param label: An optional label of the partition
        """
        SimpleOutgoingEdgePartition.__init__(
            self, identifier, AbstractMachineEdge, constraints, label)
