class Allocation(object):
    """ The allocation of a range of a continuous resource to a vertex
    """

    __slots__ = [

        # The resource allocated
        "_resource",

        # The x-coordinate of the chip that the resource is allocated on
        "_x",

        # The y-coordinate of the chip that the resource is allocated on
        "_y",

        # The vertex allocated to
        "_vertex",
    ]

    def __init__(self, resource, x, y, vertex):
        """

        :param resource: The resource allocated
        :type resource_type:\
            :py:class:`pacman.model.resources.resource.Resource`
        :param x:\
            The x-coordinate of the chip that the resource is allocated on
        :type x: int
        :param y:\
            The y-coordinate of the chip that the resource is allocated on
        :type y: int
        :param vertex: The vertex allocated to
        :type vertex:\
            :py:class:`pacman.model.graph.machine.abstract_machine_vertex.AbstractMachineVertex`
        """
        self._resource = resource
        self._x = x
        self._y = y
        self._vertex = vertex

    @property
    def resource_type(self):
        """ The type of resource allocated
        """
        return self._resource_type

    @property
    def x(self):
        return self._x

    @property
    def y(self):
        return self._y

    @property
    def vertex(self):
        """ The vertex allocated to
        """
        return self._vertex
