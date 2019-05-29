"""Utility functions which may be of value to router implementations.

Based on
https://github.com/project-rig/rig/blob/master/rig/place_and_route/route/utils.py
"""


from pacman.operations.rig_algorithms.links import Links


def longest_dimension_first(vector, start=(0, 0), width=None, height=None):
    """List the (x, y) steps on a longest-dimension first route.

    Parameters
    ----------
    vector : (x, y, z)
        The vector which the path should cover.
    start : (x, y)
        The coordinates from which the path should start (note this is a 2D
        coordinate).
    width : int or None
        The width of the topology beyond which we wrap around (0 <= x < width).
        If None, no wrapping on the X axis will occur.
    height : int or None
        The height of the topology beyond which we wrap around (0 <= y <
        height).  If None, no wrapping on the Y axis will occur.

    Returns
    -------
    [(:py:class:`~rig.links.Links`, (x, y)), ...]
        Produces (in order) a (direction, (x, y)) pair for every hop along the
        longest dimension first route. The direction gives the direction to
        travel in from the previous step to reach the current step.
        The first generated value is that of the first hop
        after the starting position, the last generated value is the
        destination position.
    """
    x, y = start

    out = []

    for dimension, magnitude in sorted(enumerate(vector),
                                       key=(lambda x:
                                            abs(x[1])),
                                       reverse=True):
        if magnitude == 0:
            break

        # Advance in the specified direction
        sign = 1 if magnitude > 0 else -1
        for _ in range(abs(magnitude)):
            if dimension == 0:
                dx, dy = sign, 0
            elif dimension == 1:
                dx, dy = 0, sign
            elif dimension == 2:  # pragma: no branch
                dx, dy = -sign, -sign

            x += dx
            y += dy

            # Wrap-around if required
            if width is not None:
                x %= width
            if height is not None:
                y %= height

            direction = Links.from_vector((dx, dy))

            out.append((direction, (x, y)))

    return out


def links_between(a, b, machine):
    """Get the set of working links connecting chips a and b.

    Parameters
    ----------
    a : (x, y)
    b : (x, y)
    machine : :py:class:`~rig.place_and_route.Machine`

    Returns
    -------
    set([:py:class:`~rig.links.Links`, ...])
    """
    ax, ay = a
    bx, by = b
    return set(link for link, (dx, dy) in ((l, l.to_vector()) for l in Links)
               if (ax + dx) % machine.width == bx and
               (ay + dy) % machine.height == by and
               (ax, ay, link) in machine)
