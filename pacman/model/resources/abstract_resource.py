from abc import ABCMeta
from six import add_metaclass
from abc import abstractproperty


@add_metaclass(ABCMeta)
class AbstractResource(object):
    """ Represents some finite resource
    """

    @abstractproperty
    def value(self):
        """ Get the amount of the resource used or available

        :rtype: float
        """
        pass
