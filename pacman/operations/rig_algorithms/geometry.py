"""General-purpose SpiNNaker-related geometry functions.
"""

from math import sqrt

import numpy as np


def to_xyz(xy):
    """Convert a two-tuple (x, y) coordinate into an (x, y, 0) coordinate."""
    x, y = xy
    return (x, y, 0)


def minimise_xyz(xyz):
    """Minimise an (x, y, z) coordinate."""
    x, y, z = xyz
    m = max(min(x, y), min(max(x, y), z))
    return (x-m, y-m, z-m)


def shortest_mesh_path_length(source, destination):
    """Get the length of a shortest path from source to destination without
    using wrap-around links.

    Parameters
    ----------
    source : (x, y, z)
    destination : (x, y, z)

    Returns
    -------
    int
    """
    x = destination[0] - source[0]
    y = destination[1] - source[1]
    z = destination[2] - source[2]

    # When vectors are minimised, (1,1,1) is added or subtracted from them.
    # This process does not change the range of numbers in the vector. When a
    # vector is minimal, it is easy to see that the range of numbers gives the
    # magnitude since there are at most two non-zero numbers (with opposite
    # signs) and the sum of their magnitudes will also be their range.
    #
    # Though ideally this code would be written::
    #
    #     >>> return max(x, y, z) - min(x, y, z)
    #
    # Unfortunately the min/max functions are very slow (as of CPython 3.5) so
    # this expression is unrolled as IF/else statements.

    # max(x, y, z)
    maximum = x
    if y > maximum:
        maximum = y
    if z > maximum:
        maximum = z

    # min(x, y, z)
    minimum = x
    if y < minimum:
        minimum = y
    if z < minimum:
        minimum = z

    return maximum - minimum


def shortest_mesh_path(source, destination):
    """Calculate the shortest vector from source to destination without using
    wrap-around links.

    Parameters
    ----------
    source : (x, y, z)
    destination : (x, y, z)

    Returns
    -------
    (x, y, z)
    """
    return minimise_xyz(d - s for s, d in zip(source, destination))


def shortest_torus_path_length(source, destination, width, height):
    """Get the length of a shortest path from source to destination using
    wrap-around links.

    See http://jhnet.co.uk/articles/torus_paths for an explanation of how this
    method works.

    Parameters
    ----------
    source : (x, y, z)
    destination : (x, y, z)
    width : int
    height : int

    Returns
    -------
    int
    """
    # Aliases for convenience
    w, h = width, height

    # Get (non-wrapping) x, y vector from source to destination as if the
    # source was at (0, 0).
    x = destination[0] - source[0]
    y = destination[1] - source[1]
    z = destination[2] - source[2]
    x, y = x - z, y - z
    x %= w
    y %= h

    # Calculate the shortest path length.
    #
    # In an ideal world, the following code would be used::
    #
    #     >>> return min(max(x, y),      # No wrap
    #     ...            w - x + y,      # Wrap X
    #     ...            x + h - y,      # Wrap Y
    #     ...            max(w-x, h-y))  # Wrap X and Y
    #
    # Unfortunately, however, the min/max functions are shockingly slow as of
    # CPython 3.5. Since this function may appear in some hot code paths (e.g.
    # the router), the above statement is unwrapped as a series of
    # faster-executing IF statements for performance.

    # No wrap
    length = x if x > y else y

    # Wrap X
    wrap_x = w - x + y
    if wrap_x < length:
        length = wrap_x

    # Wrap Y
    wrap_y = x + h - y
    if wrap_y < length:
        length = wrap_y

    # Wrap X and Y
    dx = w - x
    dy = h - y
    wrap_xy = dx if dx > dy else dy
    if wrap_xy < length:
        return wrap_xy
    else:
        return length


def shortest_torus_path(source, destination, width, height):
    """Calculate the shortest vector from source to destination using
    wrap-around links.

    See http://jhnet.co.uk/articles/torus_paths for an explanation of how this
    method works.

    Parameters
    ----------
    source : (x, y, z)
    destination : (x, y, z)
    width : int
    height : int

    Returns
    -------
    (x, y, z)
    """
    # Aliases for convenience
    w, h = width, height

    # Convert to (x,y,0) form
    sx, sy, sz = source
    sx, sy = sx - sz, sy - sz

    # Translate destination as if source was at (0,0,0) and convert to (x,y,0)
    # form where both x and y are not -ve.
    dx, dy, dz = destination
    dx, dy = (dx - dz - sx) % w, (dy - dz - sy) % h

    # The four possible vectors: [(distance, vector), ...]
    approaches = [(max(dx, dy), (dx, dy, 0)),                # No wrap
                  (w-dx+dy, (-(w-dx), dy, 0)),               # Wrap X only
                  (dx+h-dy, (dx, -(h-dy), 0)),               # Wrap Y only
                  (max(w-dx, h-dy), (-(w-dx), -(h-dy), 0))]  # Wrap X and Y

    # Select a minimal approach
    _, vector = min(approaches, key=(lambda a: a[0]))
    x, y, z = minimise_xyz(vector)

    return (x, y, z)


def concentric_hexagons(radius, start=(0, 0)):
    """A generator which produces coordinates of concentric rings of hexagons.

    Parameters
    ----------
    radius : int
        Number of layers to produce (0 is just one hexagon)
    start : (x, y)
        The coordinate of the central hexagon.
    """
    x, y = start
    yield (x, y)
    for r in range(1, radius + 1):
        # Move to the next layer
        y -= 1
        # Walk around the hexagon of this radius
        for dx, dy in [(1, 1), (0, 1), (-1, 0), (-1, -1), (0, -1), (1, 0)]:
            for _ in range(r):
                yield (x, y)
                x += dx
                y += dy


def standard_system_dimensions(num_boards):
    """Calculate the standard network dimensions (in chips) for a full torus
    system with the specified number of SpiNN-5 boards.

    Returns
    -------
    (w, h)
        Width and height of the network in chips.

        Standard SpiNNaker systems are constructed as squarely as possible
        given the number of boards available. When a square system cannot be
        made, the function prefers wider systems over taller systems.

      Raises
      ------
      ValueError
        If the number of boards is not a multiple of three.
    """
    # Special case to avoid division by 0
    if num_boards == 0:
        return (0, 0)

    # Special case: meaningful systems with 1 board can exist
    if num_boards == 1:
        return (8, 8)

    if num_boards % 3 != 0:
        raise ValueError("{} is not a multiple of 3".format(num_boards))

    # Find the largest pair of factors to discover the squarest system in terms
    # of triads of boards.
    for h in reversed(  # pragma: no branch
            range(1, int(sqrt(num_boards // 3)) + 1)):
        if (num_boards // 3) % h == 0:
            break

    w = (num_boards // 3) // h

    # Convert the number of triads into numbers of chips (each triad of boards
    # contributes as 12x12 block of chips).
    return (w * 12, h * 12)


def spinn5_eth_coords(width, height, root_x=0, root_y=0):
    """Generate a list of board coordinates with Ethernet connectivity in a
    SpiNNaker machine.

    Specifically, generates the coordinates for the Ethernet connected chips of
    SpiNN-5 boards arranged in a standard torus topology.

    .. warning::

        In general, applications should use
        :py:class:`rig.machine_control.MachineController.get_system_info` and
        :py:meth:`~rig.machine_control.machine_controller.SystemInfo.ethernet_connected_chips`
        to gather the coordinates of Ethernet connected chips which are
        actually functioning. For example::

            >> from rig.machine_control import MachineController
            >> mc = MachineController("my-machine")
            >> si = mc.get_system_info()
            >> print(list(si.ethernet_connected_chips()))
            [((0, 0), "1.2.3.4"), ((4, 8), "1.2.3.5"), ((8, 4), "1.2.3.6")]

    Parameters
    ----------
    width, height : int
        Width and height of the system in chips.
    root_x, root_y : int
        The coordinates of the root chip (i.e. the chip used to boot the
        machine), e.g. from
        :py:attr:`rig.machine_control.MachineController.root_chip`.
    """
    # In oddly-shaped machines where chip (0, 0) does not exist, we must offset
    # the coordinates returned in accordance with the root chip's location.
    root_x %= 12
    root_x %= 12

    # Internally, work with the width and height rounded up to the next
    # multiple of 12
    w = ((width + 11) // 12) * 12
    h = ((height + 11) // 12) * 12

    for x in range(0, w, 12):
        for y in range(0, h, 12):
            for dx, dy in ((0, 0), (4, 8), (8, 4)):
                nx = (x + dx + root_x) % w
                ny = (y + dy + root_y) % h
                # Skip points which are outside the range available
                if nx < width and ny < height:
                    yield (nx, ny)


def spinn5_local_eth_coord(x, y, w, h, root_x=0, root_y=0):
    """Get the coordinates of a chip's local ethernet connected chip.

    Returns the coordinates of the ethernet connected chip on the same board as
    the supplied chip.

    .. note::
        This function assumes the system is constructed from SpiNN-5 boards

    .. warning::

        In general, applications should interrogate the machine to determine
        which Ethernet connected chip is considered 'local' to a particular
        SpiNNaker chip, e.g. using
        :py:class:`rig.machine_control.MachineController.get_system_info`::

            >> from rig.machine_control import MachineController
            >> mc = MachineController("my-machine")
            >> si = mc.get_system_info()
            >> print(si[(3, 2)].local_ethernet_chip)
            (0, 0)

        :py:func:`.spinn5_local_eth_coord` will always produce the coordinates
        of the Ethernet-connected SpiNNaker chip on the same SpiNN-5 board as
        the supplied chip. In future versions of the low-level system software,
        some other method of choosing local Ethernet connected chips may be
        used.

    Parameters
    ----------
    x, y : int
        Chip whose coordinates are of interest.
    w, h : int
        Width and height of the system in chips.
    root_x, root_y : int
        The coordinates of the root chip (i.e. the chip used to boot the
        machine), e.g. from
        :py:attr:`rig.machine_control.MachineController.root_chip`.
    """
    dx, dy = SPINN5_ETH_OFFSET[(y - root_y) % 12][(x - root_x) % 12]
    return ((x + int(dx)) % w), ((y + int(dy)) % h)


SPINN5_ETH_OFFSET = np.array([
    [(vx - x, vy - y) for x, (vx, vy) in enumerate(row)]
    for y, row in enumerate([
        # Below is an enumeration of the absolute coordinates of the nearest
        # ethernet connected chip. Note that the above list comprehension
        # changes these into offsets to the nearest chip.
        # X:   0         1         2         3         4         5         6         7         8         9        10        11     # noqa Y:
        [(+0, +0), (+0, +0), (+0, +0), (+0, +0), (+0, +0), (+4, -4), (+4, -4), (+4, -4), (+4, -4), (+4, -4), (+4, -4), (+4, -4)],  # noqa  0
        [(+0, +0), (+0, +0), (+0, +0), (+0, +0), (+0, +0), (+0, +0), (+4, -4), (+4, -4), (+4, -4), (+4, -4), (+4, -4), (+4, -4)],  # noqa  1
        [(+0, +0), (+0, +0), (+0, +0), (+0, +0), (+0, +0), (+0, +0), (+0, +0), (+4, -4), (+4, -4), (+4, -4), (+4, -4), (+4, -4)],  # noqa  2
        [(+0, +0), (+0, +0), (+0, +0), (+0, +0), (+0, +0), (+0, +0), (+0, +0), (+0, +0), (+4, -4), (+4, -4), (+4, -4), (+4, -4)],  # noqa  3
        [(-4, +4), (+0, +0), (+0, +0), (+0, +0), (+0, +0), (+0, +0), (+0, +0), (+0, +0), (+8, +4), (+8, +4), (+8, +4), (+8, +4)],  # noqa  4
        [(-4, +4), (-4, +4), (+0, +0), (+0, +0), (+0, +0), (+0, +0), (+0, +0), (+0, +0), (+8, +4), (+8, +4), (+8, +4), (+8, +4)],  # noqa  5
        [(-4, +4), (-4, +4), (-4, +4), (+0, +0), (+0, +0), (+0, +0), (+0, +0), (+0, +0), (+8, +4), (+8, +4), (+8, +4), (+8, +4)],  # noqa  6
        [(-4, +4), (-4, +4), (-4, +4), (-4, +4), (+0, +0), (+0, +0), (+0, +0), (+0, +0), (+8, +4), (+8, +4), (+8, +4), (+8, +4)],  # noqa  7
        [(-4, +4), (-4, +4), (-4, +4), (-4, +4), (+4, +8), (+4, +8), (+4, +8), (+4, +8), (+4, +8), (+8, +4), (+8, +4), (+8, +4)],  # noqa  8
        [(-4, +4), (-4, +4), (-4, +4), (-4, +4), (+4, +8), (+4, +8), (+4, +8), (+4, +8), (+4, +8), (+4, +8), (+8, +4), (+8, +4)],  # noqa  9
        [(-4, +4), (-4, +4), (-4, +4), (-4, +4), (+4, +8), (+4, +8), (+4, +8), (+4, +8), (+4, +8), (+4, +8), (+4, +8), (+8, +4)],  # noqa 10
        [(-4, +4), (-4, +4), (-4, +4), (-4, +4), (+4, +8), (+4, +8), (+4, +8), (+4, +8), (+4, +8), (+4, +8), (+4, +8), (+4, +8)]   # noqa 11
    ])
], dtype=int)
"""SpiNN-5 ethernet connected chip lookup.

Used by :py:func:`.spinn5_local_eth_coord`. Given an x and y chip position
modulo 12, return the offset of the board's bottom-left chip from the chip's
position.

Note: the order of indexes: ``SPINN5_ETH_OFFSET[y][x]``!
"""


def spinn5_chip_coord(x, y, root_x=0, root_y=0):
    """Get the coordinates of a chip on its board.

    Given the coordinates of a chip in a multi-board system, calculates the
    coordinates of the chip within its board.

    .. note::
        This function assumes the system is constructed from SpiNN-5 boards

    Parameters
    ----------
    x, y : int
        The coordinates of the chip of interest
    root_x, root_y : int
        The coordinates of the root chip (i.e. the chip used to boot the
        machine), e.g. from
        :py:attr:`rig.machine_control.MachineController.root_chip`.
    """
    dx, dy = SPINN5_ETH_OFFSET[(y - root_y) % 12][(x - root_x) % 12]
    return (-int(dx), -int(dy))


