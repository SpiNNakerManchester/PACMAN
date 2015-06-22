"""
MulticastRoutingPaths
"""

# pacman imports
from pacman import exceptions


class MulticastRoutingPaths(object):
    """
    a class that contains paths for edges though the machine via routers
    """

    def __init__(self):
        self._edge_to_routing_path_map = dict()
        self._router_to_entries_map = dict()

    def add_path_entry(self, entry):
        """ adds a multicast routing path entry to the paths

        :param entry: the entry to add
        :return:
        """
        # update edge_to_routing_path_map
        if entry.edge not in self._edge_to_routing_path_map:
            self._edge_to_routing_path_map[entry.edge] = list()
        self._edge_to_routing_path_map[entry.edge].append(entry)

        # update router_to_entries_map
        key = (entry.router_x, entry.router_y)
        if key not in self._router_to_entries_map:
            self._router_to_entries_map[key] = list()
        self._router_to_entries_map[key].append(entry)

    def get_entries_for_router(self, router_x, router_y):
        """
        returns the set of mutlicast path entries assigned to this router
        :param router:
        :return:
        """
        key = (router_x, router_y)
        if key not in self._router_to_entries_map:
            return ()
        else:
            return self._router_to_entries_map[key]

    def get_entries_for_edge(self, edge):
        """
        returns the netries for a given edge
        :param edge:
        :return:
        """
        if edge not in self._edge_to_routing_path_map:
            raise exceptions.PacmanNotExistException(
                "edge {} does not exist in the list".format(edge))
        else:
            return self._edge_to_routing_path_map[edge]

    def get_entry_on_coords_for_edge(self, edge, router_x, router_y):
        """
        returns a entry from a spefici coord if possible
        :param edge:
        :param router_x
        :param router_y
        :return:
        """
        entries = self.get_entries_for_router(router_x, router_y)
        for entry in entries:
            if entry.edge == edge:
                return entry
        return None

    def all_subedges(self):
        """
        returns all the subedges contained within this multicast routing path
        :return: a iterable of subedges
        """
        return self._edge_to_routing_path_map.keys()