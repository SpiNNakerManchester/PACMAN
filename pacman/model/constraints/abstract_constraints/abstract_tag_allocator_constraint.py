from abc import ABCMeta
from abc import abstractmethod
from six import add_metaclass


from pacman.model.constraints.abstract_constraints.abstract_placer_constraint \
    import AbstractPlacerConstraint


@add_metaclass(ABCMeta)
class AbstractTagAllocatorConstraint(AbstractPlacerConstraint):
    """ An abstract constraint for (ip or reverse ip) tag allocation
    """

    def __init__(self, board_address, tag, port):
        """
        :param board_address: A fixed board address required for the tag, or\
                    None if any address is OK
        :type board_address: str
        :param port: The target port of the tag
        :type port: int
        :param tag: A fixed tag id to assign, or None if any tag is OK
        :type tag: int
        """
        AbstractPlacerConstraint.__init__(self, "tag allocator constraint")
        self._board_address = board_address
        self._tag = tag
        self._port = port

    def is_placer_constraint(self):
        return True

    @abstractmethod
    def is_tag_allocator_constraint(self):
        """ helper method for is_instance
        :return: True
        """

    @property
    def board_address(self):
        """ The board address required, or None if any board is OK

        :return: The board address or None
        :rtype: str
        """
        return self._board_address

    @property
    def port(self):
        """ The port of the tag

        :return: The port of the tag
        :rtype: int
        """
        return self._port

    @property
    def tag(self):
        """ The tag required, or None if any tag is OK

        :return: The tag or None
        :rtype: int
        """
        return self._tag
