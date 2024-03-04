# Copyright (c) 2017 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
An explicit representation of a routing tree in a machine.

This representation of a route explicitly describes a tree-structure and the
complete path taken by a route. This is used during place and route in
preference to a set of RoutingTableEntry tuples since it is more easily
verified and more accurately represents the problem at hand.

Based on
https://github.com/project-rig/rig/blob/master/rig/place_and_route/routing_tree.py
"""
from __future__ import annotations
from collections import deque
from typing import (
    Deque, Iterable, Iterator, List, Optional, Set, Tuple, Union,
    TYPE_CHECKING)
from spinn_utilities.typing.coords import XY
if TYPE_CHECKING:
    from pacman.model.graphs.machine import MachineVertex


class RoutingTree(object):
    """
    Explicitly defines a multicast route through a SpiNNaker machine.

    Each instance represents a single hop in a route and recursively refers to
    following steps.
    """

    # A *lot* of instances of this data structure are created and so its memory
    # consumption is a sensitive matter. The following optimisations have been
    # made:
    # * Using __slots__ hugely reduces the size of instances of this class
    #   object
    # * Storing the chip coordinate as two values (_chip_x and _chip_y) rather
    #   than a tuple saves 56 bytes per instance.
    __slots__ = ("_chip_x", "_chip_y", "_children", "_label")

    def __init__(self, chip: XY, label: Optional[str] = None):
        """
        :param tuple(int,int) chip:
            The chip the route is currently passing through.
        """
        self._chip_x, self._chip_y = chip
        self._children: List[
            Tuple[int, Union[RoutingTree, MachineVertex]]] = []
        self._label = label

    @property
    def label(self) -> Optional[str]:
        """
        The label value provided to the init (if applicable).

        :rtype: str or None
        """
        return self._label

    @property
    def chip(self) -> XY:
        """
        The chip the route is currently passing through.

        :rtype: tuple(int,int)
        """
        return (self._chip_x, self._chip_y)

    @property
    def children(self) -> Iterable[
            Tuple[int, Union[RoutingTree, MachineVertex]]]:
        """
        A :py:class:`iterable` of the next steps in the route represented by a
        (route, object) tuple.

        .. note::
            Up until Rig 1.5.1, this structure used :py:class:`set`\\ s to
            store children. This was changed to :py:class:`list`\\ s since
            sets incur a large memory overhead and in practice the set-like
            behaviour of the list of children is not useful.

        The object indicates the intended destination of this step in the
        route. It may be one of:

        * :py:class:`RoutingTree`
          representing the continuation of the routing tree after following a
          given link.
        * A vertex (i.e. some other Python object) when the route terminates
          at the supplied vertex.

        .. note::
            The direction may be `None` and so additional logic may be required
            to determine what core to target to reach the vertex.

        :rtype: iterable(tuple(int, RoutingTree or MachineVertex))
        """
        yield from self._children

    def append_child(
            self, child: Tuple[int, Union[RoutingTree, MachineVertex]]):
        """
        :param child:
        :type child: tuple(int, RoutingTree or MachineVertex)
        """
        self._children.append(child)

    def remove_child(
            self, child: Tuple[int, Union[RoutingTree, MachineVertex]]):
        """
        :param child:
        :type child: tuple(int, RoutingTree or MachineVertex)
        """
        self._children.remove(child)

    @property
    def is_leaf(self) -> bool:
        """
        Detect if this is a leaf node, which is one with no children.
        :return:
        """
        return not self._children

    def __iter__(self) -> Iterator[Union[RoutingTree, MachineVertex]]:
        """
        Iterate over this node and then all its children, recursively and in
        no specific order. This iterator iterates over the child *objects*
        (i.e. not the route part of the child tuple).
        """
        yield self

        for _route, obj in self._children:
            if isinstance(obj, RoutingTree):
                yield from obj
            else:
                yield obj

    def __repr__(self) -> str:
        return f"<RoutingTree at {self.chip} with {len(self._children)}" \
               f" {'child' if len(self._children) == 1 else 'children'}>"

    def traverse(self) -> Iterable[Tuple[Optional[int], XY, Set[int]]]:
        """
        Traverse the tree yielding the direction taken to a node, the
        coordinates of that node and the directions leading from the Node.

        :return:
            A sequence of (direction, (x, y), set(route)) describing the route
            taken. At each step, we have the
            direction taken to reach a Node in the tree, the (x, y) coordinate
            of that Node and routes leading to children of the Node.
        :rtype: iterable(tuple(int, tuple(int,int), set(int)))
        """
        # A queue of (direction, node) to visit. The direction is the Links
        # entry which describes the direction in which we last moved to reach
        # the node (or None for the root).
        to_visit: Deque[
            Tuple[Optional[int], RoutingTree]] = deque(((None, self), ))
        while to_visit:
            direction, node = to_visit.popleft()

            # Determine the set of directions we must travel to reach the
            # children
            out_directions: Set[int] = set()
            # pylint:disable=protected-access
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
