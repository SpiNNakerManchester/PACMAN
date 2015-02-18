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
        return True

    @abstractmethod
    def is_tag_allocator_constraint(self):
        """
        helper method for is_instance
        :return:
        """

    @property
    def board_address(self):
        return self._board_address

    @property
    def port(self):
        return self._port

    @property
    def tag_id(self):
        return self._tag_id

    @board_address.setter
    def board_address(self, new_value):
        self._board_address = new_value

    @tag_id.setter
    def tag_id(self, new_value):
        self._tag_id = new_value