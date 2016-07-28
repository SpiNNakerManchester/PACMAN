from abc import ABCMeta
from six import add_metaclass
from abc import abstractproperty


@add_metaclass(ABCMeta)
class AbstractHasLabel(object):
    """ Represents an item with a label
    """

    __slots__ = ()

    @abstractproperty
    def label(self):
        """ The label of the item

        :return: The label
        :rtype: str
        :raise None: Raises no known exceptions
        """

    @abstractproperty
    def model_name(self):
        """ the report model name of the item

        :return: the model name
        :rtype: str
        :raises: None: Raises no known exceptions
        """
