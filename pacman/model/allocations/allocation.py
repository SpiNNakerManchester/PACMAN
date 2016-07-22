class Allocation(object):
    """ The allocation of a range of a continuous resource to a vertex
    """

    __slots__ = [

        # The resource allocated
        "_resource",

        # The vertex allocated to
        "_vertex",
    ]

    def __init__(self, resource, vertex):
        """

        :param resource: The resource allocated
        :type resource_type:\
            :py:class:`pacman.model.resources.resource.Resource`
        :param vertex: The vertex allocated to
        :type vertex:\
            :py:class:`pacman.model.graph.machine.abstract_machine_vertex.AbstractMachineVertex`
        """
        self._resource = resource
        self._vertex = vertex

    @property
    def resource_type(self):
        return self._resource_type

    @property
    def vertex(self):
        return self._vertex
