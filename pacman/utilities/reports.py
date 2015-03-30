import os
import time
import logging

from pacman.model.partitionable_graph.multi_cast_partitionable_edge\
    import MultiCastPartitionableEdge
from pacman.model.placements import placement
from pacman import exceptions

from spinn_machine.sdram import SDRAM

logger = logging.getLogger(__name__)


def tag_allocator_report(report_folder, tag_infos):
    pass


def placer_reports(report_folder, hostname, graph, graph_mapper,
                   placements, machine):
    placement_report_by_vertex(report_folder, hostname, graph,
                               graph_mapper, placements)
    placement_by_core(report_folder, hostname, placements, machine,
                      graph_mapper)
    sdram_usage_per_chip(report_folder, hostname, placements, machine,
                         graph_mapper, graph)


def router_reports(report_folder, hostname, graph, graph_to_sub_graph_mapper,
                   placements, routing_tables, routing_info, machine,
                   include_dat_based=False):
    router_report_from_router_tables(report_folder, routing_tables)
    if include_dat_based:
        router_report_from_dat_file(report_folder)


def routing_info_reports(report_folder, subgraph, routing_infos):
    routing_info_report(report_folder, subgraph, routing_infos)


def partitioner_reports(report_folder, hostname, graph,
                        graph_to_subgraph_mapper):
    partitioner_report(report_folder, hostname,
                       graph, graph_to_subgraph_mapper)


def partitioner_report(report_folder, hostname, graph,
                       graph_mapper):
    """
    Generate report on the placement of sub-vertices onto cores.
    """
    # Cycle through all vertices, and foreach cycle through its sub-vertices.
    # For each sub-vertex, describe its core mapping.
    file_name = os.path.join(report_folder, "placement_by_vertex.rpt")
    f_place_by_vertex = None
    try:
        f_place_by_vertex = open(file_name, "w")
    except IOError:
        logger.error("Generate_placement_reports: Can't open file {} for"
                     " writing.".format(file_name))

    f_place_by_vertex.write(
        "        Placement Information by Vertex\n")
    f_place_by_vertex.write("        ===============================\n\n")
    time_date_string = time.strftime("%c")
    f_place_by_vertex.write("Generated: {}".format(time_date_string))
    f_place_by_vertex.write(" for target machine '{}'".format(hostname))
    f_place_by_vertex.write("\n\n")

    for v in graph.vertices:
        vertex_name = v.label
        vertex_model = v.model_name
        num_atoms = v.n_atoms
        f_place_by_vertex.write(
            "**** Vertex: '{}'\n".format(vertex_name))
        f_place_by_vertex.write("Model: {}\n".format(vertex_model))
        f_place_by_vertex.write("Pop sz: {}\n".format(num_atoms))
        f_place_by_vertex.write("Sub-vertices: \n")

        for sv in graph_mapper.get_subvertices_from_vertex(v):
            lo_atom = graph_mapper.get_subvertex_slice(sv).lo_atom
            hi_atom = graph_mapper.get_subvertex_slice(sv).hi_atom
            num_atoms = hi_atom - lo_atom + 1
            my_string = "  Slice {}:{} ({} atoms) \n"\
                        .format(lo_atom, hi_atom, num_atoms)
            f_place_by_vertex.write(my_string)
        f_place_by_vertex.write("\n")
    # Close file:
    f_place_by_vertex.close()


def placement_report_by_vertex(report_folder, hostname, graph,
                               graph_mapper, placements):
    """
    Generate report on the placement of sub-vertices onto cores.
    """
    # Cycle through all vertices, and foreach cycle through its sub-vertices.
    # For each sub-vertex, describe its core mapping.
    file_name = os.path.join(report_folder, "placement_by_vertex.rpt")
    f_place_by_vertex = None
    try:
        f_place_by_vertex = open(file_name, "w")
    except IOError:
        logger.error("Generate_placement_reports: Can't open file {} for"
                     " writing.".format(file_name))

    f_place_by_vertex.write(
        "        Placement Information by Vertex\n")
    f_place_by_vertex.write("        ===============================\n\n")
    time_date_string = time.strftime("%c")
    f_place_by_vertex.write("Generated: {}".format(time_date_string))
    f_place_by_vertex.write(" for target machine '{}'".format(hostname))
    f_place_by_vertex.write("\n\n")

    used_processors_by_chip = dict()
    used_sdram_by_chip = dict()
    subvertex_by_processor = dict()

    for v in graph.vertices:
        vertex_name = v.label
        vertex_model = v.model_name
        num_atoms = v.n_atoms
        f_place_by_vertex.write(
            "**** Vertex: '{}'\n".format(vertex_name))
        f_place_by_vertex.write("Model: {}\n".format(vertex_model))
        f_place_by_vertex.write("Pop sz: {}\n".format(num_atoms))
        f_place_by_vertex.write("Sub-vertices: \n")

        for sv in graph_mapper.get_subvertices_from_vertex(v):
            lo_atom = graph_mapper.get_subvertex_slice(sv).lo_atom
            hi_atom = graph_mapper.get_subvertex_slice(sv).hi_atom
            num_atoms = hi_atom - lo_atom + 1
            cur_placement = placements.get_placement_of_subvertex(sv)
            x, y, p = cur_placement.x, cur_placement.y, cur_placement.p
            key = "{},{}".format(x, y)
            if key in used_processors_by_chip:
                used_procs = used_processors_by_chip[key]
            else:
                used_procs = list()
                used_sdram_by_chip.update({key: 0})
            subvertex_by_processor["{},{},{}".format(x, y, p)] = sv
            new_proc = [p, cur_placement]
            used_procs.append(new_proc)
            used_processors_by_chip.update({key: used_procs})
            my_string = "  Slice {}:{} ({} atoms) on core ({}, {}, {}) \n"\
                        .format(lo_atom, hi_atom, num_atoms, x, y, p)
            f_place_by_vertex.write(my_string)
        f_place_by_vertex.write("\n")
    # Close file:
    f_place_by_vertex.close()


def placement_by_core(report_folder, hostname, placements, machine,
                      graph_mapper):

    # File 2: Placement by core.
    # Cycle through all chips and by all cores within each chip.
    # For each core, display what is held on it.
    file_name = os.path.join(report_folder, "placement_by_core.rpt")
    f_place_by_core = None
    try:
        f_place_by_core = open(file_name, "w")
    except IOError:
        logger.error("Generate_placement_reports: Can't open file {} for "
                     "writing.".format(file_name))

    f_place_by_core.write("        Placement Information by Core\n")
    f_place_by_core.write("        =============================\n\n")
    time_date_string = time.strftime("%c")
    f_place_by_core.write("Generated: {}".format(time_date_string))
    f_place_by_core.write(" for target machine '{}'".format(hostname))
    f_place_by_core.write("\n\n")

    for chip in machine.chips:
        written_header = False
        for processor in chip.processors:
            if placements.is_subvertex_on_processor(chip.x, chip.y,
                                                    processor.processor_id):
                if not written_header:
                    f_place_by_core.write("**** Chip: ({}, {})\n"
                                          .format(chip.x, chip.y))
                    f_place_by_core.write("Application cores: {}\n"
                                          .format(len(list(chip.processors))))
                    written_header = True
                proc_id = processor.processor_id
                subvertex = \
                    placements.get_subvertex_on_processor(
                        chip.x, chip.y, processor.processor_id)
                vertex = \
                    graph_mapper\
                    .get_vertex_from_subvertex(subvertex)
                vertex_label = vertex.label
                vertex_model = vertex.model_name
                vertex_atoms = vertex.n_atoms
                lo_atom = graph_mapper.get_subvertex_slice(subvertex).lo_atom
                hi_atom = graph_mapper.get_subvertex_slice(subvertex).hi_atom
                num_atoms = hi_atom - lo_atom + 1
                p_str = ("  Processor {}: Vertex: '{}',"
                         " pop sz: {}\n".format(
                             proc_id, vertex_label, vertex_atoms))
                f_place_by_core.write(p_str)
                p_str = ("              Slice on this core: {}:{} ({} atoms)\n"
                         .format(lo_atom, hi_atom, num_atoms))
                f_place_by_core.write(p_str)
                p_str = "              Model: {}\n\n".format(vertex_model)
                f_place_by_core.write(p_str)
                f_place_by_core.write("\n")
    # Close file:
    f_place_by_core.close()


def sdram_usage_per_chip(report_folder, hostname, placements, machine,
                         graph_mapper, graph):
    file_name = os.path.join(report_folder, "chip_sdram_usage_by_core.rpt")
    f_mem_used_by_core = None
    try:
        f_mem_used_by_core = open(file_name, "w")
    except IOError:
        logger.error("Generate_placement_reports: Can't open file {} for "
                     "writing.".format(file_name))

    f_mem_used_by_core.write("        Memory Usage by Core\n")
    f_mem_used_by_core.write("        ====================\n\n")
    time_date_string = time.strftime("%c")
    f_mem_used_by_core.write("Generated: %s" % time_date_string)
    f_mem_used_by_core.write(" for target machine '{}'".format(hostname))
    f_mem_used_by_core.write("\n\n")
    used_sdram_by_chip = dict()

    for cur_placement in placements.placements:
        subvert = cur_placement.subvertex
        vertex = graph_mapper.get_vertex_from_subvertex(subvert)

        vertex_slice = graph_mapper.get_subvertex_slice(subvert)
        requirements = \
            vertex.get_resources_used_by_atoms(vertex_slice, graph)

        x, y, p = cur_placement.x, cur_placement.y, cur_placement.p
        f_mem_used_by_core.write(
            "SDRAM requirements for core ({},{},{}) is {} KB\n".format(
                x, y, p, int(requirements.sdram.get_value() / 1024.0)))
        if (x, y) not in used_sdram_by_chip:
            used_sdram_by_chip[(x, y)] = requirements.sdram.get_value()
        else:
            used_sdram_by_chip[(x, y)] += requirements.sdram.get_value()

    for chip in machine.chips:
        try:
            used_sdram = used_sdram_by_chip[(chip.x, chip.y)]
            if used_sdram != 0:
                f_mem_used_by_core.write(
                    "**** Chip: ({}, {}) has total memory usage of"
                    " {} KB out of a max of "
                    "{} MB \n\n".format(chip.x, chip.y,
                                        int(used_sdram / 1024.0),
                                        int(SDRAM.DEFAULT_SDRAM_BYTES /
                                            (1024.0 * 1024.0))))
        except KeyError:

            # Do Nothing
            pass

    # Close file:
    f_mem_used_by_core.close()


def routing_info_report(report_folder, subgraph, routing_infos):
    file_name = os.path.join(report_folder,
                             "virtual_key_space_information_report.rpt")
    output = None
    try:
        output = open(file_name, "w")
    except IOError:
        logger.error("generate virtual key space information report: "
                     "Can't open file {} for writing.".format(file_name))

    for subvert in subgraph.subvertices:
        output.write("Subvert: {} \n".format(subvert))
        outgoing_subedges = subgraph.outgoing_subedges_from_subvertex(subvert)
        for outgoing_subedge in outgoing_subedges:
            subedge_routing_info = routing_infos.\
                get_subedge_information_from_subedge(outgoing_subedge)
            output.write("{} \n".format(subedge_routing_info))
        output.write("\n\n")
    output.flush()
    output.close()


def router_report_from_router_tables(report_folder, routing_tables):
    top_level_folder = os.path.join(report_folder, "routing_tables_generated")
    if not os.path.exists(top_level_folder):
        os.mkdir(top_level_folder)
    for routing_table in routing_tables.routing_tables:
        if routing_table.number_of_entries > 0:
            file_sub_name = "routing_table_{}_{}.rpt"\
                .format(routing_table.x, routing_table.y)
            file_name = os.path.join(top_level_folder, file_sub_name)
            try:
                output = open(file_name, "w")
            except IOError:
                logger.error("Generate_placement_reports: Can't open file"
                             " {} for writing.".format(file_name))

            output.write("router contains {} entries \n "
                         "\n".format(routing_table.number_of_entries))
            output.write("  Index   Key(hex)    Mask(hex)    Route(hex)"
                         "    Src. Core -> [Cores][Links]\n")
            output.write("----------------------------------------------------"
                         "--------------------------\n")

            entry_count = 0
            for entry in routing_table.multicast_routing_entries:
                index = entry_count & 0xFFFF
                key = entry.key_combo
                mask = entry.mask
                hex_route = _reduce_route_value(entry.processor_ids,
                                                entry.link_ids)
                hex_key = _uint_32_to_hex_string(key)
                hex_mask = _uint_32_to_hex_string(mask)
                route_txt = _expand_route_value(entry.processor_ids,
                                                entry.link_ids)
                core_id = "({}, {}, {})"\
                    .format((key >> 24 & 0xFF), (key >> 16 & 0xFF),
                            (key >> 11 & 0xF))
                entry_str = ("    {}     {}       {}      {}         {}     "
                             " {}\n".format(index, hex_key, hex_mask,
                                            hex_route, core_id, route_txt))
                entry_count += 1
                output.write(entry_str)
            output.flush()
            output.close()


def router_report_from_dat_file(report_folder):
    pass


# TODO NOT CHECKED YET
def router_edge_information(report_folder, hostname, graph, routing_tables,
                            graph_mapper, placements, routing_info,
                            machine):
    """
    Generate report on the routing of sub-edges across the machine.
    """
    file_name = os.path.join(report_folder, "edge_routing_info.rpt")
    f_routing = None
    try:
        f_routing = open(file_name, "w")
    except IOError:
        logger.error("Generate_routing_reports: Can't open file {} for "
                     "writing.".format(file_name))

    f_routing.write("        Edge Routing Report\n")
    f_routing.write("        ===================\n\n")
    time_date_string = time.strftime("%c")
    f_routing.write("Generated: {}".format(time_date_string))
    f_routing.write(" for target machine '{}'".format(hostname))
    f_routing.write("\n\n")

    for e in filter(lambda edge: isinstance(edge, MultiCastPartitionableEdge),
                    graph.edges):
        from_v, to_v = e.pre_vertex, e.post_vertex
        from_v_sz, to_v_sz = from_v.n_atoms, to_v.n_atoms
        fr_v_name, to_v_name = from_v.label, to_v.label
        string = "**** Edge '{}', from vertex: '{}' (size: {})"\
                 .format(e.label, fr_v_name, from_v_sz)
        string = "{}, to vertex: '{}' (size: {})\n"\
                 .format(string, to_v_name, to_v_sz)
        f_routing.write(string)
        subedges = graph_mapper.get_partitioned_edges_from_partitionable_edge(
            e)
        f_routing.write("Sub-edges: {}\n".format(len(subedges)))

        for se in subedges:
            fr_sv, to_sv = se.pre_subvertex, se.post_subvertex
            fr_placement = placements.get_placement_of_subvertex(fr_sv)
            to_placement = placements.get_placement_of_subvertex(to_sv)
            routing_data = routing_info.get_subedge_information_from_subedge(
                se)
            associated_chips = _get_associated_routing_entries_from(
                fr_placement, to_placement, routing_tables, routing_data,
                machine)

            route_len = len(associated_chips)
            fr_core = "({}, {}, {})".format(fr_placement.x, fr_placement.y,
                                            fr_placement.p)
            to_core = "({}, {}, {})".format(to_placement.x, to_placement.y,
                                            to_placement.p)
            fr_atoms = "{}:{}".format((graph_mapper.get_subvertex_slice(
                                       fr_placement.subvertex).lo_atom),
                                      (graph_mapper.get_subvertex_slice(
                                       fr_placement.subvertex).hi_atom))
            to_atoms = "{}:{}".format(to_placement.subvertex.lo_atom,
                                      to_placement.subvertex.hi_atom)
            string = "Sub-edge from core {}, atoms {},".format(fr_core,
                                                               fr_atoms)
            string = "{} to core {}, atoms {} has route length: {}\n".format(
                string, to_core, to_atoms, route_len)
            f_routing.write(string)

            # Print route info:
            count_on_this_line = 0
            total_step_count = 0
            for step in associated_chips:
                if total_step_count == 0:
                    entry_str = "(({}, {}, {})) -> ".format(
                        fr_placement.x, fr_placement.y, fr_placement.p)
                    f_routing.write(entry_str)
                entry_str = "({}, {}) -> ".format(step['x'], step['y'])
                f_routing.write(entry_str)
                if total_step_count == (route_len - 1):
                    entry_str = "(({}, {}, {}))".format(
                        to_placement.x, to_placement.y, to_placement.p)
                    f_routing.write(entry_str)
                total_step_count += 1
                count_on_this_line += 1
                if count_on_this_line == 5:
                    f_routing.write("\n")
                    count_on_this_line = 0
            f_routing.write("\n")
        # End one entry:
        f_routing.write("\n")
    f_routing.flush()
    f_routing.close()


def _reduce_route_value(processors_ids, link_ids):
    value = 0
    for link in link_ids:
        value += 1 << link
    for processor in processors_ids:
        value += 1 << (processor + 6)
    return _uint_32_to_hex_string(value)


def _uint_32_to_hex_string(number):
    """
    Convert a 32-bit unsigned number into a hex string.
    """
    bottom = number & 0xFFFF
    top = (number >> 16) & 0xFFFF
    hex_string = "{:x}{:x}".format(top, bottom)
    return hex_string


def _expand_route_value(processors_ids, link_ids):
    """ Convert a 32-bit route word into a string which lists the target cores\
        and links.
    """

    # Convert processor targets to readable values:
    route_string = "["
    first = True
    for processor in processors_ids:
        if first:
            route_string += "{}".format(processor)
            first = False
        else:
            route_string += ", {}".format(processor)

    route_string += "] ["
    # Convert link targets to readable values:
    link_labels = {0: 'E', 1: 'NE', 2: 'N', 3: 'W', 4: 'SW', 5: 'S'}

    first = True
    for link in link_ids:
        if first:
            route_string += "{}".format(link_labels[link])
            first = False
        else:
            route_string += ", {}".format(link_labels[link])
    route_string += "]"
    return route_string


def _get_associated_routing_entries_from(
        fr_placement, to_placement, routing_tables, routing_data, machine):

    routing_table = routing_tables.get_routing_table_for_chip(
        to_placement.x, to_placement.y)
    key_combo = routing_data.key_combo
    mask = routing_data.mask
    destinations = \
        routing_table.get_multicast_routing_entry_by_key_combo(key_combo, mask)

    if fr_placement.x == to_placement.x and fr_placement.y == to_placement.y:

        # check that the last route matches the destination core in the
        # to_placement add the destination core to the associated chips list
        # and return the associated chip list
        processors = destinations.processor_ids()
        if to_placement.p in processors:
            associated_chips = list()
            step = dict()
            step['x'] = fr_placement.x
            step['y'] = fr_placement.y
            associated_chips.append(step)
            return associated_chips
        else:
            raise exceptions.PacmanRoutingException(
                "Although routing path with key_combo {0:X} reaches chip"
                " ({1:d}, {2:d}), it does not reach processor {3:d} as"
                " requested by the destination placement".format(
                    key_combo, to_placement.x, to_placement.y, to_placement.p))
    else:
        links = destinations.link_ids()
        current_x = fr_placement.x
        current_y = fr_placement.y
        current_chip = machine.get_chip_at(current_x, current_y)
        current_router = current_chip.router
        for i in links:
            next_link = current_router.get_link(i)
            next_x = next_link.destination_x
            next_y = next_link.destination_y
            next_placement = placement.Placement(None, next_x, next_y, None)
            associated_chips = _get_associated_routing_entries_from(
                next_placement, to_placement, routing_tables, routing_data,
                machine)
            if associated_chips is not None:
                step = dict()
                step['x'] = current_x
                step['y'] = current_y
                associated_chips.insert(0, step)
                return associated_chips
            else:
                return None
