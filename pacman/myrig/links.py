"""A datastructure representing links in a SpiNNaker machine.
"""

from six import iteritems

from enum import IntEnum

#from rig.utils.docstrings import add_int_enums_to_docstring


#@add_int_enums_to_docstring
class Links(IntEnum):
    """Enumeration of links from a SpiNNaker chip.

    Note that the numbers chosen have two useful properties:

    * The integer values assigned are chosen to match the numbers used to
      identify the links in the low-level software API and hardware registers.
    * The links are ordered consecutively in anticlockwise order meaning the
      opposite link is `(link+3)%6`.

    .. note::

        In early versions of Rig this object was called ``rig.machine.Links``.
    """

    east = 0
    north_east = 1
    north = 2
    west = 3
    south_west = 4
    south = 5

    @classmethod
    def from_vector(cls, vector):
        """Given a vector from one node to a neighbour, get the link direction.

        Note that any vector whose magnitude in any given dimension is greater
        than 1 will be assumed to use a machine's wrap-around links.

        Note that this method assumes a system larger than 2x2. If a 2x2, 2xN
        or Nx2 (for N > 2) system is provided the link selected will
        arbitrarily favour either wrap-around or non-wrap-around links. This
        function is not meaningful for 1x1 systems.

        Parameters
        ----------
        vector : (x, y)
            The vector from one node to its logical neighbour.

        Returns
        -------
        :py:class:`~rig.links.Links`
            The link direction to travel in the direction indicated by the
            vector.
        """
        x, y = vector

        # Vectors must be mapped to a form (x, y) where x and y are -1, 0 or 1.
        # When a vector is between two neighbouring nodes which are not
        # connected by a wrap-around link this is already the case. When
        # wrapping around on a given dimension, however, the element of the
        # vector corresponding with that dimension will be outside this range.
        #
        # For example, in a 4x4 system, the vector between nodes (3, 1) and (0,
        # 1) comes out as (-3, 0). In this case we wrap around on the X axis
        # going from the right-hand-side to the left-hand-side. The logical
        # direction vector should just be (1, 0) since we're logically
        # travelling East. Notice that the sign of the wrapped-around element
        # is flipped and the magnitude forced to 1.
        if abs(x) > 1:
            x = -1 if x > 0 else 1
        if abs(y) > 1:
            y = -1 if y > 0 else 1

        return _link_direction_lookup[(x, y)]

    def to_vector(self):
        """Given a link direction, return the equivalent vector."""
        return _direction_link_lookup[self]

    @property
    def opposite(self):
        """Get the opposite link to the one given."""
        return Links((self + 3) % 6)


_link_direction_lookup = {
    (+1, +0): Links.east,
    (-1, +0): Links.west,
    (+0, +1): Links.north,
    (+0, -1): Links.south,
    (+1, +1): Links.north_east,
    (-1, -1): Links.south_west,
}
_direction_link_lookup = {l: v for (v, l) in iteritems(_link_direction_lookup)}

# Special case: Lets assume we've got a 2xN or Nx2 system (N >= 2) where we can
# "spiral" around the Z axis to reach places which normally wouldn't be
# accessible.
#
# (x+1, 0) <-> (x+0, 1)        (1, y+0) <-> (0, y+1)
#           /                        |   |   |
#     --+--/+---+--                  +---+---+
#       | . |   |                    | . |   |/
#     --+---+---+--                  /---+---/
#       |   | . |                   /|   | . |
#     --+---+/--+--                  +---+---+
#           /                        |   |   |
_link_direction_lookup[(+1, -1)] = Links.south_west
_link_direction_lookup[(-1, +1)] = Links.north_east
