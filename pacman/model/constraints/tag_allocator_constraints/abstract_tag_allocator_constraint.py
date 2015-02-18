from abc import ABCMeta
from abc import abstractmethod
from six import add_metaclass


from pacman.model.constraints.abstract_constraints.abstract_placer_constraint \
    import AbstractPlacerConstraint


@add_metaclass(ABCMeta)
class AbstractTagAllocatorConstraint(AbstractPlacerConstraint):

    def __init__(self, board_address, port, tag_id):
        AbstractPlacerConstraint.__init__(self, "tag allocator constraint")
        self._board_address = board_address
        self._tag_id = tag_id
        self._port = port

    def is_placer_constraint(self):
        """
        helper method for is_instance
        :return:
        """
        return True

    @abstractmethod
    def is_tag_allocator_constraint(self):
        """
        helper method for is_instance
        :return:
        """

    @property
    def board_address(self):
        """ property method for the board address this constraint is linked to
        (part of a iptag and reverse_iptag)

        :return:
        """
        return self._board_address

    @property
    def port(self):
        """property method for the port this constraint is linked to
         (part of a iptag and reverse_iptag)

        :return:
        """
        return self._port

    @property
    def tag_id(self):
        """property method for the tag this constraint is linked to
        (part of a iptag and reverse_iptag)

        :return:
        """
        return self._tag_id

    @board_address.setter
    def board_address(self, new_value):
        """ setter method to set a new board address to link this constraint to
        (a tag has been assigned and therefore this is kept for ease)

        :param new_value: the new board address this constraitn is to be
        assigned to
        :return:
        """
        self._board_address = new_value

    @tag_id.setter
    def tag_id(self, new_value):
        """ setter method to set a new tag id to link this constraint to
        (a tag has been assigned and therefore this is kept for ease)

        :param new_value:
        :return:
        """
        self._tag_id = new_value