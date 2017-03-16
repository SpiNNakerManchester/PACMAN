from six import add_metaclass

from spinn_utilities.abstract_base import AbstractBase, abstractmethod

@add_metaclass(AbstractBase)
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
