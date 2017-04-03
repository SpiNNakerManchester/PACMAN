from pacman.model.graphs.impl.outgoing_edge_partition\
    import OutgoingEdgePartition
from pacman.model.graphs.machine.machine_edge import MachineEdge


class MachineOutgoingEdgePartition(OutgoingEdgePartition):
    """ An outgoing edge partition for a Machine Graph
    """

    __slots__ = []

    def __init__(self, identifier, constraints=None, label=None,
                 traffic_weight=1):
        """

        :param identifier: The identifier of the partition
        :param constraints: Any initial constraints
        :param label: An optional label of the partition
        :param traffic_weight: the weight of this partition in relation\
            to other partitions
        """
        OutgoingEdgePartition.__init__(
            self, identifier, MachineEdge, constraints, label,
            traffic_weight=traffic_weight)
