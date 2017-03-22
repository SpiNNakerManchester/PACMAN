from abc import ABCMeta
from abc import abstractmethod
from six import add_metaclass


@add_metaclass(ABCMeta)
class AbstractResource(object):
    """ Represents some finite resource
    """

    __slots__ = []

    @abstractmethod
    def get_value(self):
        """ Get the amount of the resource used or available

        :return: The amount of the resource
        :rtype: int
        """
        pass
