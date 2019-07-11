from pacman.model.graphs.impl import OutgoingEdgePartition
from six import add_metaclass

from spinn_utilities.abstract_base import AbstractBase
from spinn_utilities.overrides import overrides


@add_metaclass(AbstractBase)
class AbstractTrafficTypeSecureOutgoingPartition(OutgoingEdgePartition):

    __slots__ = [
        "_traffic_type"
    ]

    def __init__(self, identifier, allowed_edge_types, label, traffic_type):
        OutgoingEdgePartition.__init__(
            self, identifier=identifier, label=label,
            allowed_edge_types=allowed_edge_types)
        self._traffic_type = traffic_type

    @property
    def traffic_type(self):
        return self._traffic_type

    @overrides(OutgoingEdgePartition.add_edge)
    def add_edge(self, edge):
        if self._traffic_type == edge.traffic_type:
            super(
                AbstractTrafficTypeSecureOutgoingPartition, self).add_edge(edge)
        else:
            raise Exception(
                "Not support edge traffic type was attempted to be added to "
                "the connection partition with identifier {}".format(
                    self._identifier))