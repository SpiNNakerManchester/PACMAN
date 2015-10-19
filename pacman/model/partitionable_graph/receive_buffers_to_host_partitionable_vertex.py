from abc import abstractmethod, ABCMeta
from six import add_metaclass
from pacman.model.constraints.placer_constraints.\
    placer_radial_placement_from_chip_constraint import \
    PlacerRadialPlacementFromChipConstraint
from pacman.model.constraints.tag_allocator_constraints.\
    tag_allocator_require_iptag_constraint import \
    TagAllocatorRequireIptagConstraint


@add_metaclass(ABCMeta)
class ReceiveBuffersToHostPartitionableVertex(object):
    def __init__(self, buffering_output=False):
        self._buffering_output = buffering_output

    @property
    def buffering_output(self):
        return self._buffering_output

    def set_buffering_output(self):
        if not self._buffering_output:
            self._buffering_output = True

            # here I need to add the code to associate a tag to the vertex
            notification_ip_address = None
            notification_port = None
            board_address = None
            notification_tag = None
            notification_strip_sdp = False

            self.add_constraint(
                TagAllocatorRequireIptagConstraint(
                    notification_ip_address, notification_port,
                    notification_strip_sdp, board_address, notification_tag))

            # add placement constraint
            placement_constraint = PlacerRadialPlacementFromChipConstraint(0, 0)
            self.add_constraint(placement_constraint)

    @abstractmethod
    def get_buffered_regions_list(self):
        pass

    @abstractmethod
    def add_constraint(self, constraint):
        pass

    @staticmethod
    def is_buffering_recordable():
        return True
