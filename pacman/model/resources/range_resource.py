from pacman.model.resources.abstract_resource import AbstractResource
from pacman.model.decorators.overrides import overrides


class RangeResource(AbstractResource):
    """ A range of a continuous resource
    """

    __slots__ = [

        # The type of resource allocated
        "_resource_type",

        # The start of the range of the allocation - the first item
        "_start",

        # The end of the range of the allocation - the last item
        "_end",

        # The step of the range of the allocation
        "_step"
    ]

    def __init__(self, resource_type, start, end=None, step=None):
        """

        :param resource_type: The type of the resource
        :type resource_type: str
        :param start:\
            The first item in the range of the resource or the last item in\
            the range if no end is specified (in which case start=0)
        :type start: int
        :param end: The optional last item in the range of the resource
        :type end: int
        :param step: The optional step through the range of the resource
        :type step: int
        """
        self._resource_type = resource_type
        self._start = start
        self._end = end
        if end is None:
            self._start = 0
            self._end = start
        self._step = step

    @property
    @overrides(AbstractResource.resource_type)
    def resource_type(self):
        return self._resource_type

    @property
    @overrides(AbstractResource.size)
    def size(self):
        return (self._end - self._start) + 1

    @overrides(AbstractResource.__len__)
    def __len__(self):
        return self.size

    @property
    @overrides(AbstractResource.as_slice)
    def as_slice(self):
        return slice(self._start, self._end + 1, self._step)
