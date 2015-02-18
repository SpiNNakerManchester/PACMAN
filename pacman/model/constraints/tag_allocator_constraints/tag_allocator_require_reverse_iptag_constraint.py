import sys
from pacman.model.constraints.tag_allocator_constraints.\
    abstract_tag_allocator_constraint import \
    AbstractTagAllocatorConstraint


class TagAllocatorRequireReverseIptagConstraint(AbstractTagAllocatorConstraint):

    def __init__(self, tag_id, board_address, port_num, port, placement_x=None,
                 placement_y=None, placement_p=None):
        AbstractTagAllocatorConstraint.__init__(self, board_address, port,
                                                tag_id)
        self._placement_x = placement_x
        self._placement_y = placement_y
        self._placement_p = placement_p
        self._port_num = port_num

    @property
    def port_num(self):
        """property method for the port_num this constraint is linked to
        (part of a reverse iptag which tells the core what udp port it was sent
         by)

        :return:
        """
        return self._port_num

    @property
    def placement_x(self):
        """property method for the placement_x this constraint is linked to
        (part of a reverse iptag which tells the monitor core which core to
        send packets to which come into spinnaker via the reverse iptag
        linked to this constraint)

        :return:
        """
        return self._placement_x

    @property
    def placement_y(self):
        """property method for the placement_y this constraint is linked to
        (part of a reverse iptag which tells the monitor core which core to
        send packets to which come into spinnaker via the reverse iptag
        linked to this constraint)

        :return:
        """
        return self._placement_y

    @property
    def placement_p(self):
        """property method for the placement_p this constraint is linked to
        (part of a reverse iptag which tells the monitor core which core to
        send packets to which come into spinnaker via the reverse iptag
        linked to this constraint)

        :return:
        """
        return self._placement_p

    @placement_p.setter
    def placement_p(self, new_value):
        """ setter method for the placement_p this constraint is linked to
        (part of a reverse iptag which tells the monitor core which core to
        send packets to which come into spinnaker via the reverse iptag
        linked to this constraint)

        :param new_value: the new value for the p coord of the core to which
        packets are sent when they come into spinnaker via the reverse iptag
        linked to this constraint)
        :return:
        """
        self._placement_p = new_value

    @placement_x.setter
    def placement_x(self, new_value):
        """setter method for the placement_x this constraint is linked to
        (part of a reverse iptag which tells the monitor core which core to
        send packets to which come into spinnaker via the reverse iptag
        linked to this constraint)

        :param new_value: the new value for the x coord of the core to which
        packets are sent when they come into spinnaker via the reverse iptag
        linked to this constraint)
        :return:
        """
        self._placement_x = new_value

    @placement_y.setter
    def placement_y(self, new_value):
        """setter method for the placement_y this constraint is linked to
        (part of a reverse iptag which tells the monitor core which core to
        send packets to which come into spinnaker via the reverse iptag
        linked to this constraint)

        :param new_value: the new value for the y coord of the core to which
        packets are sent when they come into spinnaker via the reverse iptag
        linked to this constraint)
        :return:
        """
        self._placement_y = new_value

    def is_placer_constraint(self):
        """ helper method for is_instance

        :return:
        """
        return True

    def is_tag_allocator_constraint(self):
        """helper method for is_instance

        :return:
        """
        return True

    def rank(self):
        """the level to which this constraint should be considered during
        ordering of constraints

        :return:
        """
        return sys.maxint - 4