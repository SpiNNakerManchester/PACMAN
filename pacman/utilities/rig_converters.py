from rig.netlist import Net
from rig.machine import Machine, Links
from rig.routing_table import Routes
from rig.place_and_route.routing_tree import RoutingTree
from rig.place_and_route.constraints import \
    LocationConstraint, ReserveResourceConstraint, RouteEndpointConstraint

from collections import defaultdict
from six import iteritems

from pacman.utilities import constants
from pacman.model.constraints.placer_constraints\
    .placer_chip_and_core_constraint import PlacerChipAndCoreConstraint
from pacman.model.constraints.placer_constraints\
    .placer_radial_placement_from_chip_constraint \
    import PlacerRadialPlacementFromChipConstraint
from pacman.model.placements.placements import Placements
from pacman.model.placements.placement import Placement
from pacman.model.routing_table_by_partition\
    .multicast_routing_table_by_partition \
    import MulticastRoutingTableByPartition
from pacman.model.routing_table_by_partition\
    .multicast_routing_table_by_partition_entry  \
    import MulticastRoutingTableByPartitionEntry
from pacman.model.abstract_classes.virtual_partitioned_vertex \
    import VirtualPartitionedVertex


# A lookup from link name (string) to Links enum entry.
LINK_LOOKUP = {l.name: l for l in Links}
ROUTE_LOOKUP = {"core_{}".format(r.core_num) if r.is_core else r.name: r
                for r in Routes}

CHIP_HOMOGENIOUS_CORES = 18
CHIP_HOMOGENIOUS_SDRAM = 119275520
CHIP_HOMOGENIOUS_SRAM = 24320
CHIP_HOMOGENIOUS_TAGS = 0
ROUTER_MAX_NUMBER_OF_LINKS = 6
ROUTER_HOMOGENIOUS_ENTRIES = 1023

N_CORES_PER_VERTEX = 1


def convert_to_rig_machine(machine):

    chip_resources = dict()
    chip_resources['cores'] = CHIP_HOMOGENIOUS_CORES
    chip_resources['sdram'] = CHIP_HOMOGENIOUS_SDRAM
    chip_resources['sram'] = CHIP_HOMOGENIOUS_SRAM
    chip_resources["router_entries"] = ROUTER_HOMOGENIOUS_ENTRIES
    chip_resources['tags'] = CHIP_HOMOGENIOUS_TAGS

    # handle exceptions
    dead_chips = list()
    dead_links = list()
    chip_resource_exceptions = list()

    # write dead chips
    for x_coord in range(0, machine.max_chip_x + 1):
        for y_coord in range(0, machine.max_chip_y + 1):
            if (not machine.is_chip_at(x_coord, y_coord) or
                    machine.get_chip_at(x_coord, y_coord).virtual):
                dead_chips.append([x_coord, y_coord])
            else:
                chip = machine.get_chip_at(x_coord, y_coord)

                # write dead links
                for link_id in range(0, ROUTER_MAX_NUMBER_OF_LINKS):
                    router = chip.router
                    if not router.is_link(link_id):
                        dead_links.append(
                            [x_coord, y_coord, "{}".format(
                             constants.EDGES(link_id).name.lower())])

                # Fix the number of processors when there are less
                resource_exceptions = dict()
                n_processors = len([
                    processor for processor in chip.processors])
                if n_processors < CHIP_HOMOGENIOUS_CORES:
                    resource_exceptions["cores"] = n_processors

                # Add tags if Ethernet chip
                if chip.ip_address is not None:
                    resource_exceptions["tags"] = len(chip.tag_ids)

                if len(resource_exceptions) > 0:
                    chip_resource_exceptions.append(
                        (x_coord, y_coord, resource_exceptions))

    return Machine(
        width=machine.max_chip_x + 1,
        height=machine.max_chip_y + 1,
        chip_resources=chip_resources,
        chip_resource_exceptions={
            (x, y): {
                resource: r.get(
                    resource, chip_resources[resource])
                for resource in chip_resources}
            for x, y, r in chip_resource_exceptions},
        dead_chips=set((x, y) for x, y in dead_chips),
        dead_links=set(
            (x, y, LINK_LOOKUP[link])
            for x, y, link in dead_links))


def convert_to_rig_partitioned_graph(partitioned_graph):

    vertices_resources = dict()
    edges_resources = defaultdict()

    for vertex in partitioned_graph.subvertices:
        vid = str(id(vertex))

        # handle external devices
        if isinstance(vertex, VirtualPartitionedVertex):
            vertex_resources = dict()
            vertices_resources[vid] = vertex_resources
            vertex_resources["cores"] = 0

        # handle standard vertices
        else:
            vertex_resources = dict()
            vertices_resources[vid] = vertex_resources
            vertex_resources["cores"] = N_CORES_PER_VERTEX
            vertex_resources["sdram"] = int(
                vertex.resources_required.sdram.get_value())
        vertex_outgoing_partitions = \
            partitioned_graph.outgoing_edges_partitions_from_vertex(vertex)

        # handle the vertex edges
        for partition_id in vertex_outgoing_partitions:
            partition = vertex_outgoing_partitions[partition_id]
            hyper_edge_dict = dict()
            edges_resources[str(id(partition))] = hyper_edge_dict
            hyper_edge_dict["source"] = vid

            sinks = list()
            weight = 0
            for edge in partition.edges:
                sinks.append(str(id(edge.post_subvertex)))
                weight += edge.weight
            hyper_edge_dict['sinks'] = sinks
            hyper_edge_dict["weight"] = weight
            hyper_edge_dict["type"] = partition.type.name.lower()

    net_names = {
        Net(edge["source"], edge["sinks"], edge["weight"]): name
        for name, edge in iteritems(edges_resources)
    }
    nets = list(net_names)

    return vertices_resources, nets, net_names


def create_rig_partitioned_graph_constraints(partitioned_graph, machine):

    constraints = []
    for vertex in partitioned_graph.subvertices:
        for constraint in vertex.constraints:
            if isinstance(constraint, (
                    PlacerChipAndCoreConstraint,
                    PlacerRadialPlacementFromChipConstraint)):
                constraints.append(LocationConstraint(
                    str(id(vertex)), (constraint.x, constraint.y)))

        if isinstance(vertex, VirtualPartitionedVertex):
            constraints.append(LocationConstraint(
                str(id(vertex)), (vertex.real_chip_x, vertex.real_chip_y)))
            constraints.append(RouteEndpointConstraint(
                str(id(vertex)),
                LINK_LOOKUP[constants.EDGES(vertex.real_link).name.lower()]))
    return constraints


def create_rig_machine_constraints(machine):
    constraints = []
    for chip in machine.chips:
        for processor in chip.processors:
            if processor.is_monitor:
                constraints.append(ReserveResourceConstraint(
                    "cores",
                    slice(processor.processor_id, processor.processor_id + 1),
                    (chip.x, chip.y)))
    return constraints


def convert_to_rig_placements(placements):
    rig_placements = {
        str(id(p.subvertex)): (p.x, p.y)
        if not isinstance(p.subvertex, VirtualPartitionedVertex)
        else (p.subvertex.real_chip_x, p.subvertex.real_chip_y)
        for p in placements.placements}

    core_allocations = {
        str(id(p.subvertex)): {"cores": slice(p.p, p.p + 1)}
        for p in placements.placements
        if not isinstance(p.subvertex, VirtualPartitionedVertex)}

    return rig_placements, core_allocations


def convert_from_rig_placements(
        rig_placements, rig_allocations, partitioned_graph):
    placements = Placements()
    for vertex_id in rig_placements:
        vertex = partitioned_graph.get_subvertex_by_id(vertex_id)
        if vertex is not None:
            if isinstance(vertex, VirtualPartitionedVertex):
                placements.add_placement(Placement(
                    vertex, vertex.virtual_chip_x, vertex.virtual_chip_y,
                    None))
            else:
                x, y = rig_placements[vertex_id]
                p = rig_allocations[vertex_id]["cores"].start
                placements.add_placement(Placement(vertex, x, y, p))

    return placements


def convert_from_rig_routes(rig_routes, partitioned_graph):
    routing_tables = MulticastRoutingTableByPartition()
    for partition_id in rig_routes:
        partition = partitioned_graph.get_partition_by_id(partition_id)
        if partition is not None:
            partition_route = rig_routes[partition_id]
            _convert_next_route(
                routing_tables, partition, 0, None, partition_route)
    return routing_tables


def _convert_next_route(
        routing_tables, partition, incoming_processor, incoming_link,
        partition_route):
    x, y = partition_route.chip

    next_hops = list()
    processor_ids = list()
    link_ids = list()
    for (route, next_hop) in partition_route.children:
        if route is not None:
            link = None
            if isinstance(route, Routes):
                if route.is_core:
                    processor_ids.append(route.core_num)
                else:
                    link = route.value
                    link_ids.append(link)
            elif isinstance(route, Links):
                link = route.value
                link_ids.append(link)
            if isinstance(next_hop, RoutingTree):
                next_incoming_link = None
                if link is not None:
                    next_incoming_link = (link + 3) % 6
                next_hops.append((next_hop, next_incoming_link))

    routing_tables.add_path_entry(MulticastRoutingTableByPartitionEntry(
        link_ids, processor_ids, incoming_processor,
        incoming_link), x, y, partition)

    for next_hop, next_incoming_link in next_hops:
        _convert_next_route(
            routing_tables, partition, None, next_incoming_link, next_hop)
