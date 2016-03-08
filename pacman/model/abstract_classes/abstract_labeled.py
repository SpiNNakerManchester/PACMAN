from abc import ABCMeta
from six import add_metaclass


@add_metaclass(ABCMeta)
class AbstractLabeled(object):
    """ Represents an item with a label
    """

    def __init__(self, label):
        self._label = label

    @property
    def label(self):
        """ The label of the item

        :return: The label
        :rtype: str
        :raise None: Raises no known exceptions
        """
        return self._label
