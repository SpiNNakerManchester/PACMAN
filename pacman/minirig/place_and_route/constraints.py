"""Specifications of constraints for placement, allocation and routing.

All constraints defined in this module should be respected by any placement and
routing algorithm. Individual algorithms are permitted to define their own
implementation-specific constraints seperately.
"""


class LocationConstraint(object):
    """Unconditionally place a vertex on a specific chip.

    Attributes
    ----------
    vertex : object
        The user-supplied object representing the vertex.
    location : (x, y)
        The x- and y-coordinates of the chip the vertex must be placed on.
    """

    def __init__(self, vertex, location):
        self.vertex = vertex
        self.location = location


class SameChipConstraint(object):
    """Ensure that a group of vertices is always placed on the same chip.

    Attributes
    ----------
    vertices : [object, ...]
        The list of user-supplied objects representing the vertices to be
        placed together.
    """

    def __init__(self, vertices):
        self.vertices = vertices


class ReserveResourceConstraint(object):
    """Reserve a range of a resource on all or a specific chip.

    For example, this can be used to reserve areas of SDRAM used by the system
    software to prevent allocations occurring there.

    Note: Reserved ranges must *not* be be partly or fully outside the
    available resources for a chip nor may they overlap with one another.
    Violation of these rules will result in undefined behaviour.

    Note: placers are obliged by this constraint to subtract the reserved
    resource from the total available resource but *not* to determine whether
    the remaining resources include sufficient continuous ranges of resource
    for their placement. Users should thus be extremely careful reserving
    resources which are not immediately at the beginning or end of a resource
    range.

    Attributes
    ----------
    resource : object
        A resource identifier for the resource being reserved.
    reservation : :py:class:`slice`
        The range over that resource which must not be used.
    location : (x, y) or None
        The chip to which this reservation applies. If None then the
        reservation applies globally.
    """

    def __init__(self, resource, reservation, location=None):
        self.resource = resource
        self.reservation = reservation
        self.location = location


class AlignResourceConstraint(object):
    """Force alignment of start-indices of resource ranges.

    For example, this can be used to ensure assignments into SDRAM are word
    aligned.

    Note: placers are not obliged to be aware of or compensate for wastage of a
    resource due to this constraint and so may produce impossible placements in
    the event of large numbers of individual items using a non-aligned width
    block of resource.

    Attributes
    ----------
    resource : object
        A resource identifier for the resource to align.
    alignment : int
        The number of which all assigned start-indices must be a multiple.
    """

    def __init__(self, resource, alignment):
        self.resource = resource
        self.alignment = alignment


class RouteEndpointConstraint(object):
    """Force the endpoint of a path through the network to be a particular
    route.

    This constraint forces routes to/from the constrained vertex to terminate
    on the route specified in the constraint. For example, this could be used
    with a vertex representing an external device to force packets sent to the
    vertex to be absorbed.

    Note: This constraint does not check for dead links. This is useful since
    links attached to external devices will not typically respond to
    nearest-neighbour PEEK/POKE requests used by the SpiNNaker software to
    detect link liveness.

    **Example Usage**

    If a silicon retina is attached to the north link of chip (1,1) in a 2x2
    SpiNNaker machine, the following pair of constraints will ensure traffic
    destined for the device vertex is routed to the appropriate link::

        my_device_vertex = ...
        constraints = [LocationConstraint(my_device_vertex, (1, 1)),
                       RouteEndpointConstraint(my_device_vertex, Routes.north)]

    Attributes
    ----------
    vertex : object
        The user-supplied object representing the vertex.
    route : :py:class:`~rig.routing_table.Routes`
        The route to which paths will be directed.
    """

    def __init__(self, vertex, route):
        self.vertex = vertex
        self.route = route
