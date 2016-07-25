from abc import ABCMeta
from six import add_metaclass
from abc import abstractproperty
from abc import abstractmethod


@add_metaclass(ABCMeta)
class AbstractResource(object):
    """ Represents some finite resource
    """

    __slots__ = ()

    @abstractproperty
    def resource_type(self):
        """ The type of the resource

        :rtype: :py:class:`pacman.model.resources.resource_type.ResourceType`
        """

    @abstractproperty
    def size(self):
        """ The total amount of the resource

        :rtype: int
        """

    @abstractmethod
    def __len__(self):
        """ The total amount of the resource

        :rtype: int
        """

    @abstractproperty
    def as_slice(self):
        """ The slice of the resource, as a Python slice object

        :rtype: slice
        """
