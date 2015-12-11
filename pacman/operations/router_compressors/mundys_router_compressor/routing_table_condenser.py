
# pacman imports
from pacman.model.routing_tables.multicast_routing_table import \
    MulticastRoutingTable
from pacman.model.routing_tables.multicast_routing_tables import \
    MulticastRoutingTables
from pacman import exceptions

# general imports
import collections

from pacman.operations.router_compressors.mundys_router_compressor.\
    complete_mask_generator import CompleteMaskGenerator
from spinn_machine.multicast_routing_entry import MulticastRoutingEntry


class MundyRouterCompressor(object):

    KeyMask = collections.namedtuple('KeyMask', 'key mask')
    RoutingEntry = collections.namedtuple('RoutingEntry',
                                          'key mask route defaultable')

    def __call__(self, router_tables):
        compressed_pacman_router_tables = MulticastRoutingTables()
        for router_table in router_tables.routing_tables:
            entries, masks = \
                self._convert_to_mundy_format(router_table)
            compressed_router_table_entries = \
                self.reduce_routing_table(entries, masks)
            compressed_pacman_table = self._convert_to_pacman_router_table(
                compressed_router_table_entries, router_table.x, router_table.y)
            compressed_pacman_router_tables.add_routing_table(
                compressed_pacman_table)

        return {'routing_tables': compressed_pacman_router_tables}

    def _convert_to_mundy_format(self, pacman_router_table):
        """

        :param pacman_router_table:
        :return:
        """
        entries = list()
        masks = None

        # handle entires
        for router_entry in pacman_router_table.multicast_routing_entries:
            route_entry = 0
            for processor_id in router_entry.processor_ids:
                if processor_id > 26 or processor_id < 0:
                    raise exceptions.PacmanInvalidParameterException(
                        "route.processor_ids", str(router_entry.processor_ids),
                        "Processor ids must be between 0 and 26")
                route_entry |= (1 << (6 + processor_id))
            for link_id in router_entry.link_ids:
                if link_id > 5 or link_id < 0:
                    raise exceptions.PacmanInvalidParameterException(
                        "route.link_ids", str(router_entry.link_ids),
                        "Link ids must be between 0 and 5")
                route_entry |= (1 << link_id)
            entries.append(self.RoutingEntry(
                router_entry.routing_entry_key, router_entry.mask,
                route_entry, router_entry.defaultable))

        # handle masks
        return entries, masks

    @staticmethod
    def _convert_to_pacman_router_table(
            mundy_compressed_router_table_entries, router_x_coord,
            router_y_coord):
        """

        :param mundy_compressed_router_table_entries:
        :param router_x_coord:
        :param router_y_coord:
        :return:
        """

        table = MulticastRoutingTable(router_x_coord, router_y_coord)
        for entry in mundy_compressed_router_table_entries:
            route = entry.route
            links = list()
            processors = list()
            for link in range(0, 5):
                value = (route >> link) & 1
                if value == 1:
                    links.append(link)
            for processor in range(0, 26):
                value = (route >> (6 + processor)) & 1
                if value == 1:
                    processors.append(processor)

            table.add_mutlicast_routing_entry(MulticastRoutingEntry(
                entry.key, entry.mask, processors, links, entry.defaultable))
        return table

    @staticmethod
    def create_mask(msb, lsb):
        """Generate a mask with the MSB-LSB bits set to 0."""
        return ~(int(2**(msb + 1 - lsb) - 1) << lsb)


    def generate_mask(self, msb, lsb):
        """:py:func:`create_mask` as a generator."""
        yield self.create_mask(msb, lsb)


    def generate_increasing_lsb_masks(self, msb, lsb):
        """Generate a series of masks with LSB increasing toward MSB."""
        while lsb > msb:
            lsb += 1
            yield self.create_mask(msb + 1, lsb)


    def generate_decreasing_msb_masks(self, msb, lsb):
        """Generate a series of masks with MSB decreasing toward LSB."""
        while msb > lsb:
            yield self.create_mask(msb, lsb)
            msb -= 1

    @staticmethod
    def get_matching_entries(key, mask, entries):
        """Return entries whose keys match against the given key and mask."""
        return [e for e in entries if (e.key ^ key) & mask == 0]

    @staticmethod
    def get_routed_entries(key, entries):
        return [e for e in entries if (e.key ^ key) & e.mask == 0]

    def get_possible_nonordered_merges(self, mask, entries):
        """Return a mapping of new keys and masks to old entries.

        Applies the given mask to each key and mask in the provided set of
        routing entries.  Sets of entries that may be combined into a single
        entry given by the new key and mask are returned as a dictionary
        index by the new keys and masks.  Potential entries (masked keys and
        masks) that may not be merged (i.e., they would result in functionally
        altering the routing table) are not included.

        :param int mask: Mask to apply to each key and mask in the list of
        routes.
        :param list entries: A list of routing entries.
        :returns: A dictionary of KeyMasks mapped to lists of routing entries.
        """
        possible_merges = dict()
        failed_merges = list()

        for entry in entries:
            # Get the masked key and mask
            km = self.KeyMask(entry.key & mask, entry.mask & mask)
            if km in possible_merges or km in failed_merges:
                # We've already considered or rejected this merge, so continue
                #  onto the next entry.
                continue

            # Find all entries which would match against this proposed key
            # and mask combination.
            matches = self.get_matching_entries(km.key, km.mask, entries)

            # If there are multiple different routes in the list of matches
            # then we reject this merge.
            if len(set(m.route for m in matches)) > 1:
                failed_merges.append(km)
                continue

            # Otherwise retain this as a possible merge.
            possible_merges[km] = matches

        return possible_merges

    def get_best_nonordered_merge(self, mask, entries, routing_entry_type):
        """Return data required to make the best merge doesn't rely on table
        order.

        :returns: A tuple of merged key and mask (as a KeyMask), a list of the
                  entries to remove from the routing table and a list of new
                  entries to add to the routing table.
        :raises: :py:exc:`~._NoMergeException`
        """
        # Get the possible merges, then weight them according to the net
        # reduction they would have on the number of routing entries.  Raise a
        # _NoMergeException if there are no merges at all.
        possible_merges = self.get_possible_nonordered_merges(mask, entries)

        if len(possible_merges) == 0:
            raise exceptions.PacmanNoMergeException()

        m_weights = {km: len([e for e in es if not e.defaultable]) - 1
                     for (km, es) in possible_merges.iteritems()}
        (bkm, bes) = max(possible_merges.items(),
                         key=lambda (k, _): m_weights[k])

        # If the weight of the best merge is <= 0 then don't bother merging and
        # raise _NoMergeException to indicate that there are no possible merges.
        if m_weights[bkm] <= 0:
            raise exceptions.PacmanNoMergeException()

        # Generate the new routing entry
        new_entry = routing_entry_type(bkm.key, bkm.mask, bes[0].route, False)

        # Return the merge key and mask, the old entries and the new entry (as a
        # list)
        return bkm, bes, [new_entry]

    def reduce_routing_table(
            self, entries, masks, routing_entry_type=RoutingEntry,
            max_entries=1024, mask_generators=None,
            get_best_merge=get_best_nonordered_merge):
        """Reduce the size of a routing table by applying (variations) of masks.

        Takes a list of routing entries and applies a variety of masks (and
        variations of those masks) to the entries in an attempt to combine them.

        Routing entries are expected to have a key, mask and route attribute: the
        key and mask are expected to be integers, we don't care what the route is
        provided that it can be hashed.  The type of routing entry returned may be
        changed by calling this function with the appropriate type specified.
        Additional ways of generating masks can also be supplied.

        Masks to apply are specified as a list of tuples (msb, lsb).  Mask
        generators (functions which take a msb and lsb and YIELD a series of
        variations of these masks) may be specified. Currently the mask itself,
        masks with increasing LSB (i.e., 0b1111, 0b1110, 0b1100...) and decreasing
        MSB (e.g., 0b1111, 0b0111, ...) are the defaults.  Merging stops when the
        number of entries is smaller than the specified max.

        :param list entries:  A list of routing entries where each entry has `key`,
                              `mask` and `route` attributes.
        :param list masks: A list of (msb, lsb) tuples for regions we should try
                           masking out of routing entries.
        :param routing_entry_type: A `type` that accepts the arguments (key, mask,
                                   route, defaultable) and returns a new routing
                                   entry of the desired type.
        :param max_entries: The number of entries to target.
        :param list mask_generators: List of functions which accept a MSB and LSB
                                     and yield bitstrings with zeros between the
                                     MSB and LSB and ones elsewhere.
        :param func get_best_merge: Function to determine the best merge and return
                                    the new key and mask, the list of entries to
                                    remove and an ordered list of entries to add to
                                    the routing table.
        :returns: A reduced list of routing entries that is not guaranteed to be
                  below the maximum number of entries.
        """

        if mask_generators is None or len(mask_generators) == 0:
            mask_generators = list()
            mask_generators.append(self.generate_mask)
            mask_generators.append(self.generate_increasing_lsb_masks)
            mask_generators.append(self.generate_decreasing_msb_masks)
        # Create a merged generator for the masks
        all_masks = CompleteMaskGenerator(masks, mask_generators)

        # Perform merging for all generated masks in turn, if the number of
        #  entries drops below the max allowed then finish.
        for mask in all_masks:
            if len(entries) <= max_entries:
                break

            while len(entries) > max_entries:
                # Generate a mapping of masked keys and masks to unique routes.
                # A route may be found in multiple lists, we select the best
                # possible merge and perform it before regenerating the list.
                try:
                    mkm, old_entries, new_entries =\
                        get_best_merge(mask, entries, routing_entry_type)
                except exceptions.PacmanNoMergeException:
                    # If no merges are worth doing then move onto the next mask
                    break

                # Perform the best merge: remove all matching entries then add
                #  the new entry.
                for entry in old_entries:
                    entries.remove(entry)

                # Ensure that we HAVE removed all matching entries
                matches = self.get_matching_entries(mkm.key, mkm.mask, entries)
                assert len(matches) == 0

                # Add the merged entries.
                entries.extend(new_entries)

        # Return the new set of entries
        return entries
