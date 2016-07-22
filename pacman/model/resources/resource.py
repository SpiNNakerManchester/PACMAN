class Resource(object):
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

    def __init__(self, resource_type, start, end, step=None):
        """

        :param resource_type: The type of the resource
        :type resource_type: str
        :param start: The first item in the range of the resource
        :type start: int
        :param end: The last item in the range of the resource
        :type end: int
        :param step: The optional step through the range of the resource
        :type step: int
        """
        self._resource_type = resource_type
        self._start = start
        self._end = end
        self._step = step

    @property
    def resource_type(self):
        return self._resource_type

    @property
    def start(self):
        return self._start

    @property
    def end(self):
        return self._end

    @property
    def step(self):
        return self._step

    @property
    def size(self):
        return (self._end - self._start) + 1

    def __len__(self):
        return self.size

    @property
    def as_slice(self):
        return slice(self._start, self._end + 1, self._step)
