from pacman.model.graphs.impl import OutgoingEdgePartition
from .machine_edge import MachineEdge


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
        super(MachineOutgoingEdgePartition, self).__init__(
            identifier, MachineEdge, constraints, label, traffic_weight)
