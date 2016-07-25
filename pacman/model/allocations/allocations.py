from collections import defaultdict
from pacman.exceptions import PacmanAlreadyExistsException


class Allocations(object):
    """ A set of allocations to a graph
    """

    __slots__ = [

        # A list of all allocations
        "_allocations",

        # A dictionary of vertex and resource type -> list of allocations
        "_allocations_by_vertex_and_type"

        # A dictionary of resource type -> list of allocations
        "_allocations_by_type"
    ]

    def __init__(self, allocations=None):
        """

        :param allocations: The initial set of allocations
        """
        self._allocations = list()
        self._allocations_by_vertex_and_type = defaultdict(list)
        self._allocations_by_type = defaultdict(list)
        if allocations is not None:
            self.add_allocations(allocations)

    def add_allocation(self, allocation):
        """ Add an allocation

        :param allocation: The allocation to add
        :type allocation:\
            :py:class:`pacman.model.allocations.allocation.Allocation`
        """
        key = (allocation.vertex, allocation.resource.resource_type)
        if key in self._allocations_by_vertex_and_type:
            raise PacmanAlreadyExistsException(
                "vertex and type",
                "{} and {}".format(
                    allocation.vertex, allocation.resource.resource_type))
        self._allocations_by_vertex_and_type[key].append(allocation)
        self._allocations_by_type[allocation.resource.resource_type].append(
            allocation)
        self._allocations.append(allocation)

    def add_allocations(self, allocations):
        """ Add a set of allocations

        :param allocations: An iterable of allocations to add
        :type allocations:\
            list of :py:class:`pacman.model.allocations.allocation.Allocation`
        """
        for allocation in allocations:
            self.add_allocation(allocation)

    @property
    def allocations(self):
        """ All allocations

        :rtype:\
            list of :py:class:`pacman.model.allocations.allocation.Allocation`
        """
        return self._allocations

    def get_allocations_by_vertex(self, vertex, resource_type):
        """ Get the allocations of a resource to a vertex

        :param vertex: The vertex of the allocation to find
        :type vertex:\
            :py:class:`pacman.model.graph.machine.abstract_machine_vertex.AbstractMachineVertex`
        :param resource_type: The resource type of the allocations to find
        :type resource_type:\
            :py:class:`pacman.model.resources.resource_type.ResourceType`
        :rtype:\
            list of :py:class:`pacman.model.allocations.allocation.Allocation`
        """
        return self._allocations_by_vertex_and_type[vertex, resource_type]

    def get_allocations_by_type(self, resource_type):
        """ Get the allocations of a resource

        :param resource_type: The resource type of the allocations to find
        :type resource_type:\
            :py:class:`pacman.model.resources.resource_type.ResourceType`
        :rtype:\
            list of :py:class:`pacman.model.allocations.allocation.Allocation`
        """
        return self._allocations_by_type[resource_type]
