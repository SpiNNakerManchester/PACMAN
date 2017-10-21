from collections import OrderedDict


class MulticastRoutingTableByPartition(object):
    """ A set of multicast routing path objects
    """

    __slots__ = [
        # dict mapping (x,y) -> dict mapping (partition) -> routing table entry
        "_router_to_entries_map"
    ]

    def __init__(self):
        self._router_to_entries_map = OrderedDict()

    def add_path_entry(self, entry, router_x, router_y, partition):
        """ Adds a multicast routing path entry

        :param entry: the entry to add
        :param router_x: the x coord of the router
        :param router_y: the y coord of the router
        :param partition: the partition containing the machine edge
        :type partition: \
            :py:class:`pacman.model.graphs.AbstractOutgoingEdgePartition`
        """

        # update router_to_entries_map
        key = (router_x, router_y)
        if key not in self._router_to_entries_map:
            self._router_to_entries_map[key] = OrderedDict()

        if partition not in self._router_to_entries_map[key]:
            self._router_to_entries_map[key][partition] = entry
        else:
            self._router_to_entries_map[key][partition] = entry.merge_entry(
                self._router_to_entries_map[key][partition])

    def get_routers(self):
        """ Get the coordinates of all stored routers
        """
        return self._router_to_entries_map.iterkeys()

    def get_entries_for_router(self, router_x, router_y):
        """ Get the set of multicast path entries assigned to this router

        :param router_x: the x coord of the router
        :param router_y: the y coord of the router
        :return: return all router_path_entries for the router.
        """
        key = (router_x, router_y)
        if key not in self._router_to_entries_map:
            return ()
        else:
            return self._router_to_entries_map[key]

    def get_entry_on_coords_for_edge(self, partition, router_x, router_y):
        """ Get an entry from a specific coordinate

        """
        entries = self.get_entries_for_router(router_x, router_y)
        if partition in entries:
            return entries[partition]
        else:
            return None
