from pacman.model.resources.abstract_resource import AbstractResource
from pacman.model.decorators.overrides import overrides


class SingleResource(AbstractResource):
    """ A single value of a continuous resource
    """

    __slots__ = [

        # The type of resource allocated
        "_resource_type",

        # The value of the allocation
        "_value"
    ]

    def __init__(self, resource_type, value):
        """

        :param resource_type: The type of the resource
        :type resource_type: str
        :param value: The value of the allocation
        """
        self._resource_type = resource_type
        self._value = value

    @property
    @overrides(AbstractResource.resource_type)
    def resource_type(self):
        return self._resource_type

    @property
    @overrides(AbstractResource.size)
    def size(self):
        return 1

    @overrides(AbstractResource.__len__)
    def __len__(self):
        return self.size

    @property
    @overrides(AbstractResource.as_slice)
    def as_slice(self):
        return slice(self._value, self._value + 1)
