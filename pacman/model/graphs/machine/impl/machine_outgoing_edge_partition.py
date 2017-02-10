from pacman.model.graphs.impl.outgoing_edge_partition\
    import OutgoingEdgePartition
from pacman.model.decorators.overrides import overrides
from pacman.model.graphs.machine.abstract_machine_edge \
    import AbstractMachineEdge


class MachineOutgoingEdgePartition(OutgoingEdgePartition):
    """ An outgoing edge partition for a Machine Graph
    """

    __slots__ = [

        # The weight of traffic on this partition
        "_traffic_weight"
    ]

    def __init__(self, identifier, constraints=None, label=None,
                 traffic_weight=1):
        """

        :param identifier: The identifier of the partition
        :param constraints: Any initial constraints
        :param label: An optional label of the partition
        :param traffic_weight: the weight of this partition in relation
            to other partitions
        """
        OutgoingEdgePartition.__init__(
            self, identifier, AbstractMachineEdge, constraints, label)
        self._traffic_weight = traffic_weight

    @property
    @overrides(OutgoingEdgePartition.traffic_weight)
    def traffic_weight(self):
        return self._traffic_type
