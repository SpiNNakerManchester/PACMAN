from pacman.model.constraints.tag_allocator_constraints.\
    abstract_tag_allocator_constraint import AbstractTagAllocatorConstraint
import sys


class TagAllocatorRequireIptagConstraint(AbstractTagAllocatorConstraint):

    def __init__(self, tag_id, board_address, address, strip_sdp, port):
        AbstractTagAllocatorConstraint.__init__(self, board_address, port,
                                                tag_id)
        self._address = address
        self._stripe_sdp = strip_sdp

    @property
    def address(self):
        """property method for the address this constraint is linked to
        (part of a iptag)

        :return:
        """
        return self._address

    @property
    def strip_sdp(self):
        """"property method for telling a monitor if it is to strip the SDP
        header off it when going out of spinnaker with the iptag
        this constraint is linked to
        (part of a iptag)


        :return:
        """
        return self._stripe_sdp

    def is_placer_constraint(self):
        """ helper method for is_instance

        :return:
        """
        return True

    def is_tag_allocator_constraint(self):
        """ helper method for is_instance

        :return:
        """
        return True

    def rank(self):
        """ the level to which this constraint should be considered during
        ordering of constraints

        :return:
        """
        return sys.maxint - 4