class BasicResourceAllocator(object):
    """ A simple allocation of chip resources
    """

    def __call__(self, placements, machine):
        """

        :param placements: The placements of vertices of the graph
        :param machine: The machine from which to allocate resources
        :return: Allocations of resources
        :rtype: :py:class:`pacman.model.allocations.allocations.Allocations`
        """
        for placement in placements:
            x = placement.x
            y = placement.y
            resources = placement.vertex.resources

            for resource in resources:
