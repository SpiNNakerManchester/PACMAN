# Copyright (c) 2017-2019 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""An explicit representation of a routing tree in a machine.

This representation of a route explicitly describes a tree-structure and the
complete path taken by a route. This is used during place and route in
preference to a set of RoutingTableEntry tuples since it is more easily
verified and more accurately represents the problem at hand.

Based on
https://github.com/project-rig/rig/blob/master/rig/place_and_route/routing_tree.py
"""
from collections import deque


class RoutingTree(object):
    """Explicitly defines a multicast route through a SpiNNaker machine.

    Each instance represents a single hop in a route and recursively refers to
    following steps.
    """  # noqa W605

    # A *lot* of instances of this data structure are created and so its memory
    # consumption is a sensitive matter. The following optimisations have been
    # made:
    # * Using __slots__ hugely reduces the size of instances of this class
    #   object
    # * Storing the chip coordinate as two values (_chip_x and _chip_y) rather
    #   than a tuple saves 56 bytes per instance.
    __slots__ = ["_chip_x", "_chip_y", "_children"]

    def __init__(self, chip):
        """
        :param chip: The chip the route is currently passing through.
        :type chip: tuple(int,int)
        """
        self.chip = chip
        self._children = []

    @property
    def chip(self):
        """The chip the route is currently passing through.

        :rtype: tuple(int,int)
        """
        return (self._chip_x, self._chip_y)

    @chip.setter
    def chip(self, chip):
        self._chip_x, self._chip_y = chip

    @property
    def children(self):
        """
        A :py:class:`iterable` of the next steps in the route represented by a\
        (route, object) tuple.

        .. note::

            Up until Rig 1.5.1, this structure used :py:class:`set`\\ s to \
            store children. This was changed to :py:class:`list`\\ s since \
            sets incur a large memory overhead and in practice the set-like \
            behaviour of the list of children is not useful.

        The object indicates the intended destination of this step in the \
        route. It may be one of:

        * :py:class:`RoutingTree` \
          representing the continuation of the routing tree after following a \
          given link.
        * A vertex (i.e. some other Python object) when the route terminates \
          at the supplied vertex. Note that the direction may be None and so \
          additional logic may be required to determine what core to target to\
          reach the vertex.

        :rtype: iterable
        """
        for child in self._children:
            yield child

    def append_child(self, child):
        self._children.append(child)

    def remove_child(self, child):
        self._children.remove(child)

    def __iter__(self):
        """Iterate over this node and then all its children, recursively and in
        no specific order. This iterator iterates over the child *objects*
        (i.e. not the route part of the child tuple).
        """
        yield self

        for _route, obj in self._children:
            if isinstance(obj, RoutingTree):
                for subchild in obj:
                    yield subchild
            else:
                yield obj

    def __repr__(self):
        return "<RoutingTree at {} with {} {}>".format(
            self.chip,
            len(self._children),
            "child" if len(self._children) == 1 else "children")

    def traverse(self):
        """ Traverse the tree yielding the direction taken to a node, the
        coordinates of that node and the directions leading from the Node.

        :return: (direction, (x, y), set(route)) \
            Direction taken to reach a Node in the tree, the (x, y) coordinate\
            of that Node and routes leading to children of the Node.

        """
        # A queue of (direction, node) to visit. The direction is the Links
        # entry which describes the direction in which we last moved to reach
        # the node (or None for the root).
        to_visit = deque([(None, self)])
        while to_visit:
            direction, node = to_visit.popleft()

            # Determine the set of directions we must travel to reach the
            # children
            out_directions = set()
            for child_direction, child in node._children:
                # Note that if the direction is unspecified, we simply
                # (silently) don't add a route for that child.
                if child_direction is not None:
                    out_directions.add(child_direction)

                # Search the next steps of the route too
                if isinstance(child, RoutingTree):
                    assert child_direction is not None
                    to_visit.append((child_direction, child))

            # Yield the information pertaining to this Node
            yield direction, node.chip, out_directions
