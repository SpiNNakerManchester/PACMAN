# pacman imports
from pacman import exceptions


class MulticastRoutingPaths(object):
    """ A set of multicast routing path objects
    """

    def __init__(self):
        self._router_to_entries_map = dict()

    def add_path_entry(self, entry, router_x, router_y):
        """ Adds a multicast routing path entry

        :param entry: the entry to add
        :param router_x: the x coord of the router
        :param router_y: the y coord of the router
        :return:
        """

        # update router_to_entries_map
        key = (router_x, router_y)
        if key not in self._router_to_entries_map:
            self._router_to_entries_map[key] = list()
        self._router_to_entries_map[key].append(entry)

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

        :param partition:
        :param router_x
        :param router_y
        :return:
        """
        entries = self.get_entries_for_router(router_x, router_y)
        for entry in entries:
            if entry.partition == partition:
                return entry
        return None
