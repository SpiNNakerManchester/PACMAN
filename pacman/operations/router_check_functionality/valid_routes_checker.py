from pacman103.core import exceptions
import logging
logger = logging.getLogger(__name__)


class ValidRouteChecker(object):

    def __init__(self, partitioned_graph, placements, routing_infos,
                 routing_tables):
        self._partitioned_graph = partitioned_graph
        self._placements = placements
        self._routing_infos = routing_infos
        self._routing_tables = routing_tables

    def validate_routes(self):
        for placement in self._placements.placements:
            outgoing_edges_for_partitioned_vertex = \
                self._partitioned_graph.outgoing_subedges_from_subvertex(
                    placement.subvertex)
            #locate all placements to which this placement/subvertex will
            # communicate with
            destination_placements = list()
            for outgoing_edge in outgoing_edges_for_partitioned_vertex:
                dest_placement = self._placements.get_placement_of_subvertex(
                    outgoing_edge.post_subvertex)
                destination_placements.append(dest_placement)
            #check that the routing elements for this placement work as expected
            self._search_route(placement, destination_placements,
                               outgoing_edges_for_partitioned_vertex)

    def _search_route(self, source_placement, dest_placements, outgoing_edges):
        """entrance method to locate if the routing tables work for the
        source to desks as defined

        :param source_placement:
        :param dest_placements:
        :param outgoing_edges:
        :return:
        """
        key = self._check_keys(outgoing_edges)
        output_string = ""
        for dest in dest_placements:
            logger.debug("[{}:{}:{}]".format(dest.x, dest.y, dest.p))

        self._retrace_via_routing_tables(source_placement, dest_placements, key)
        if len(dest_placements) != 0:
            output_string = ""
            for dest in dest_placements:
                output_string += "[{}:{}:{}]".format(dest.x, dest.y, dest.p)
            source_processor = "[{}:{}:{}]".format(
                source_placement.x, source_placement.y, source_placement.p)
            raise Exception(
                "failed to locate all dstinations with subvertex {} on "
                "processor {} with key {} as it didnt reach dests {}"
                .format(source_placement.subvertex.label, source_processor, key,
                        output_string))
        else:
            logger.debug("successful test between {} and {}"
                         .format(source_placement.subvertex.label,
                                 dest_placements))

    def _retrace_via_routing_tables(self, source_placement, dest_placements,
                                    key):
        """
        tries to retrace from the source to all dests and sees if one of them
        is the dest subvert
        """
        current_router = \
            self._routing_tables.get_routing_table_for_chip(source_placement.x,
                                                            source_placement.y)
        visited_routers = set()
        visited_routers.add(current_router)
        #get src router
        entry = self._locate_routing_entry(current_router, key)
        self._trace_to_dests(entry, dest_placements, current_router,
                             key, visited_routers)

    # locates the next dest pos to check
    def _trace_to_dests(self, entry, dest_placements, current_router, key,
                        visited_routers):
        #determine where the route takes us
        chip_links = entry.link_ids
        processor_values = entry.processor_ids
        if len(chip_links) > 0:  # if goes downa chip link
            if len(processor_values) > 0:  # also goes to a processor
                self._check_processor(dest_placements, processor_values,
                                      current_router)
            # only goes to new chip
            for link_id in chip_links:
                #locate next chips router
                link = current_router.get_link(link_id)
                next_router = \
                    self._routing_tables.get_routing_table_for_chip(
                        link.destination_x, link.destination_y)
                #check that we've not visited this router before
                self._check_visited_routers(next_router, visited_routers)
                #locate next entry
                entry = self._locate_routing_entry(next_router, key)
                # get next route value from the new router
                self._trace_to_dests(entry, dest_placements,
                                     next_router, key, visited_routers)
        elif len(processor_values) > 0:  # only goes to a processor
            self._check_processor(dest_placements, processor_values,
                                  current_router)

    @staticmethod
    def _check_visited_routers(next_router, visited_routers):
        visited_routers_router = (next_router.chip.x, next_router.chip.y)
        if visited_routers_router in visited_routers:
            raise Exception("visited this router before, there is"
                            "a cycle here")
        else:
            visited_routers.add(visited_routers_router)

    def _check_keys(self, outgoing_subedges_from_a_placement):
        """checks that all the subedges handed to the algorithum have the
        same key

        :param outgoing_subedges_from_a_placement:  the subegdes to check
        :return :None
        :raises Exception: when the keymask_combo is different between the
        subedges
        """
        key = None
        for sub_edge in outgoing_subedges_from_a_placement:
            current_key = self._routing_infos.get_key_from_subedge(sub_edge)
            if key is None:
                key = current_key
            elif key != current_key:
                raise Exception("the keys from this placement do not match."
                                " Please rectify and retry")
        return key

    @staticmethod
    def _check_processor(dest_placements, processor_ids, current_router):
        to_delete = list()
        for dest_placement in dest_placements:
            if (current_router.x == dest_placement.x
                    and current_router.y == dest_placement.y):
                #in correct chip
                for processor_id in processor_ids:
                    if processor_id == dest_placement.p:
                        to_delete.append(dest_placement)
        #delete dests
        for deleted_dest in to_delete:
            dest_placements.remove(deleted_dest)

    @staticmethod
    def _locate_routing_entry(current_router, key):
        """
        loate the entry from the router based off the subedge
        """
        for entry in current_router.multicast_routing_entries:
            key_combo = entry.mask & key
            if key_combo == entry.key_combo:
                return entry
        else:
            raise exceptions.RouterException("no entry located")