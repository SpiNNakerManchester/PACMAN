from collections import defaultdict

from rig.machine import Machine, Links
from rig.netlist import Net
from rig.place_and_route.constraints import \
    LocationConstraint, ReserveResourceConstraint, RouteEndpointConstraint
from rig.place_and_route.routing_tree import RoutingTree
from rig.routing_table import Routes
from six import iteritems

from pacman.model.constraints.placer_constraints\
    import PlacerChipAndCoreConstraint, PlacerRadialPlacementFromChipConstraint
from pacman.model.graphs import AbstractFPGAVertex, AbstractVirtualVertex
from pacman.model.graphs import AbstractSpiNNakerLinkVertex
from rig.place_and_route.constraints import SameChipConstraint
from pacman.utilities.algorithm_utilities import placer_algorithm_utilities
from pacman.model.placements import Placement, Placements
from pacman.model.routing_table_by_partition\
    .multicast_routing_table_by_partition \
    import MulticastRoutingTableByPartition
from pacman.model.routing_table_by_partition\
    .multicast_routing_table_by_partition_entry  \
    import MulticastRoutingTableByPartitionEntry
from pacman.utilities import constants

# A lookup from link name (string) to Links enum entry.
LINK_LOOKUP = {l.name: l for l in Links}
ROUTE_LOOKUP = {"core_{}".format(r.core_num) if r.is_core else r.name: r
                for r in Routes}

CHIP_HOMOGENEOUS_CORES = 18
CHIP_HOMOGENEOUS_SDRAM = 119275520
CHIP_HOMOGENEOUS_SRAM = 24320
CHIP_HOMOGENEOUS_TAGS = 0
ROUTER_MAX_NUMBER_OF_LINKS = 6
ROUTER_HOMOGENEOUS_ENTRIES = 1023

N_CORES_PER_VERTEX = 1


def convert_to_rig_machine(machine):

    chip_resources = dict()
    chip_resources['cores'] = CHIP_HOMOGENEOUS_CORES
    chip_resources['sdram'] = CHIP_HOMOGENEOUS_SDRAM
    chip_resources['sram'] = CHIP_HOMOGENEOUS_SRAM
    chip_resources["router_entries"] = ROUTER_HOMOGENEOUS_ENTRIES
    chip_resources['tags'] = CHIP_HOMOGENEOUS_TAGS

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
                    is_dead = False
                    if not router.is_link(link_id):
                        is_dead = True
                    else:
                        link = router.get_link(link_id)
                        if not machine.is_chip_at(
                                link.destination_x, link.destination_y):
                            is_dead = True
                        else:
                            dest_chip = machine.get_chip_at(
                                link.destination_x, link.destination_y)
                            if dest_chip.virtual:
                                is_dead = True
                    if is_dead:
                        dead_links.append(
                            [x_coord, y_coord, "{}".format(
                             constants.EDGES(link_id).name.lower())])

                # Fix the number of processors when there are less
                resource_exceptions = dict()
                n_processors = len([
                    processor for processor in chip.processors])
                if n_processors < CHIP_HOMOGENEOUS_CORES:
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


def convert_to_rig_graph(machine_graph):

    vertices_resources = dict()
    edges_resources = defaultdict()

    for vertex in machine_graph.vertices:

        # handle external devices
        if isinstance(vertex, AbstractVirtualVertex):
            vertex_resources = dict()
            vertices_resources[vertex] = vertex_resources
            vertex_resources["cores"] = 0

        # handle standard vertices
        else:
            vertex_resources = dict()
            vertices_resources[vertex] = vertex_resources
            vertex_resources["cores"] = N_CORES_PER_VERTEX
            vertex_resources["sdram"] = int(
                vertex.resources_required.sdram.get_value())
        vertex_outgoing_partitions = \
            machine_graph.get_outgoing_edge_partitions_starting_at_vertex(
                vertex)

        # handle the vertex edges
        for partition in vertex_outgoing_partitions:
            hyper_edge_dict = dict()
            edges_resources[partition] = hyper_edge_dict
            hyper_edge_dict["source"] = vertex

            sinks = list()
            weight = 0
            for edge in partition.edges:
                sinks.append(edge.post_vertex)
                weight += edge.traffic_weight
            hyper_edge_dict['sinks'] = sinks
            hyper_edge_dict["weight"] = weight
            hyper_edge_dict["type"] = partition.traffic_type.name.lower()

    net_names = {
        Net(edge["source"], edge["sinks"], edge["weight"]): name
        for name, edge in iteritems(edges_resources)
    }
    nets = list(net_names)

    return vertices_resources, nets, net_names


def create_rig_graph_constraints(machine_graph, machine):

    constraints = []
    for vertex in machine_graph.vertices:
        if isinstance(vertex, AbstractVirtualVertex):
            link_data = None
            if isinstance(vertex, AbstractFPGAVertex):
                link_data = machine.get_fpga_link_with_id(
                    vertex.fpga_id, vertex.fpga_link_id, vertex.board_address)
            elif isinstance(vertex, AbstractSpiNNakerLinkVertex):
                link_data = machine.get_spinnaker_link_with_id(
                    vertex.spinnaker_link_id, vertex.board_address)
            constraints.append(LocationConstraint(
                vertex,
                (link_data.connected_chip_x, link_data.connected_chip_y)))
            constraints.append(RouteEndpointConstraint(
                vertex,
                LINK_LOOKUP[constants.EDGES(
                    link_data.connected_link).name.lower()]))
        else:
            for constraint in vertex.constraints:
                if isinstance(constraint, (
                        PlacerChipAndCoreConstraint,
                        PlacerRadialPlacementFromChipConstraint)):
                    constraints.append(LocationConstraint(
                        vertex, (constraint.x, constraint.y)))

    vertices_on_same_chip = \
        placer_algorithm_utilities.get_same_chip_vertex_groups(
            machine_graph.vertices)
    for group in vertices_on_same_chip.values():
        if len(group) > 1:
            constraints.append(SameChipConstraint(group))
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


def convert_to_rig_placements(placements, machine):
    rig_placements = dict()
    for placement in placements:
        if not isinstance(placement.vertex, AbstractVirtualVertex):
            rig_placements[placement.vertex] = (placement.x, placement.y)
        else:
            link_data = None
            vertex = placement.vertex
            if isinstance(vertex, AbstractFPGAVertex):
                link_data = machine.get_fpga_link_with_id(
                    vertex.fpga_id, vertex.fpga_link_id, vertex.board_address)
            elif isinstance(vertex, AbstractSpiNNakerLinkVertex):
                link_data = machine.get_spinnaker_link_with_id(
                    vertex.spinnaker_link_id, vertex.board_address)
            rig_placements[placement.vertex] = (
                link_data.connected_chip_x, link_data.connected_chip_y
            )

    core_allocations = {
        p.vertex: {"cores": slice(p.p, p.p + 1)}
        for p in placements.placements
        if not isinstance(p.vertex, AbstractVirtualVertex)}

    return rig_placements, core_allocations


def convert_from_rig_placements(
        rig_placements, rig_allocations, machine_graph):
    placements = Placements()
    for vertex in rig_placements:
        if isinstance(vertex, AbstractVirtualVertex):
            placements.add_placement(Placement(
                vertex, vertex.virtual_chip_x, vertex.virtual_chip_y,
                None))
        else:
            x, y = rig_placements[vertex]
            p = rig_allocations[vertex]["cores"].start
            placements.add_placement(Placement(vertex, x, y, p))

    return placements


def convert_from_rig_routes(rig_routes, machine_graph):
    routing_tables = MulticastRoutingTableByPartition()
    for partition in rig_routes:
        partition_route = rig_routes[partition]
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
