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


def placer_reports_with_partitionable_graph(
        report_folder, hostname, graph, graph_mapper, placements, machine):
    """
    reports producable from placement given a partitionable graph's existence
    :param report_folder: the folder to which the reports are being written
    :param hostname: the machiens hostname to which the placer worked on
    :param graph: the partitionable graph to which placements were built
    :param graph_mapper: the mapping between partitionable and partitioned graphs
    :param placements: the placements objects built by the placer.
    :param machine: the python spinnmanchine object
    :return None
    """
    placement_report_with_partitionable_graph_by_vertex(
        report_folder, hostname, graph, graph_mapper, placements)
    placement_report_with_partitionable_graph_by_core(
        report_folder, hostname, placements, machine, graph_mapper)
    sdram_usage_report_per_chip(
        report_folder, hostname, placements, machine)

def placer_reports_without_partitionable_graph(
        report_folder, hostname, sub_graph, placements, machine):
    """
    reports producable from placement given a partitionable graph's existence
    :param report_folder: the folder to which the reports are being written
    :param hostname: the machiens hostname to which the placer worked on
    :param placements: the placements objects built by the placer.
    :param machine: the python spinnmanchine object
    :param sub_graph: the partitioned graph to which the reports are to operate
    on
    :return None
    """
    placement_report_without_partitionable_graph_by_vertex(
        report_folder, hostname, placements, sub_graph)
    placement_report_without_partitionable_graph_by_core(
        report_folder, hostname, placements, machine)
    sdram_usage_report_per_chip(
        report_folder, hostname, placements, machine)



def router_reports(report_folder, routing_paths, hostname):
    router_report_from_paths(report_folder, routing_paths, hostname)


def routing_info_reports(report_folder, subgraph, routing_infos, routing_tables,
                         include_dat_based=False):
    routing_info_report(report_folder, subgraph, routing_infos)
    router_report_from_router_tables(report_folder, routing_tables)
    if include_dat_based:
        router_report_from_dat_file(report_folder)


def partitioner_reports(report_folder, hostname, graph,
                        graph_to_subgraph_mapper):
    partitioner_report(report_folder, hostname,
                       graph, graph_to_subgraph_mapper)


def router_report_from_paths(report_folder, routing_paths, hostname):
    """
    reads the router paths and generates a text file sayign how everything fits
    togehter
    :param routing_paths:
    :return:
    """
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

    link_labels = {0: 'E', 1: 'NE', 2: 'N', 3: 'W', 4: 'SW', 5: 'S'}

    for e in routing_paths.all_subedges():
        text = "**** SubEdge '{}', from vertex: '{}' to vertex: '{}'"\
                 .format(e.label, e.pre_subvertex.label, e.post_subvertex.label)
        f_routing.write(text)
        f_routing.write("\n")

        path_entries = routing_paths.get_entries_for_edge(e)
        first = True
        for entry in path_entries:
            if not first:
                text = "--->"
            else:
                text = ""
            if entry.incoming_processor is not None:
                text = text + "P{}".format(entry.incoming_processor)
            else:
                text = "(L:{}".format(link_labels[entry.incoming_link])
            link = entry.router.links.next()
            text += "->{}:{}".format(link.source_x, link.source_y)
            if entry.defaultable:
                text += ":D"
            if entry.out_going_processors is not None:
                for processor in entry.out_going_processors:
                    text = text + "->P{}".format(processor)
            if entry.out_going_links is not None:
                for link in entry.out_going_links:
                    text += "->{}".format(link_labels[link])
            f_routing.write(text)
        f_routing.write("\n")

        text = "{} has route length: {}\n".format(e.label, len(path_entries))
        f_routing.write(text)
        # End one entry:
        f_routing.write("\n")
    f_routing.flush()
    f_routing.close()


def partitioner_report(report_folder, hostname, graph,
                       graph_mapper):
    """
    Generate report on the placement of sub-vertices onto cores.
    """
    # Cycle through all vertices, and foreach cycle through its sub-vertices.
    # For each sub-vertex, describe its core mapping.
    file_name = os.path.join(report_folder, "partitioned_by_vertex.rpt")
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

    vertices = sorted(graph.vertices, key=lambda x: x.label)
    for v in vertices:
        vertex_name = v.label
        vertex_model = v.model_name
        num_atoms = v.n_atoms
        f_place_by_vertex.write(
            "**** Vertex: '{}'\n".format(vertex_name))
        f_place_by_vertex.write("Model: {}\n".format(vertex_model))
        f_place_by_vertex.write("Pop sz: {}\n".format(num_atoms))
        f_place_by_vertex.write("Sub-vertices: \n")

        partitioned_vertices = \
            sorted(graph_mapper.get_subvertices_from_vertex(v),
                   key=lambda x: x.label)
        partitioned_vertices = \
            sorted(partitioned_vertices,
                   key=lambda x: graph_mapper.get_subvertex_slice(x).lo_atom)
        for sv in partitioned_vertices:
            lo_atom = graph_mapper.get_subvertex_slice(sv).lo_atom
            hi_atom = graph_mapper.get_subvertex_slice(sv).hi_atom
            num_atoms = hi_atom - lo_atom + 1
            my_string = "  Slice {}:{} ({} atoms) \n"\
                        .format(lo_atom, hi_atom, num_atoms)
            f_place_by_vertex.write(my_string)
            f_place_by_vertex.flush()
        f_place_by_vertex.write("\n")
    # Close file:
    f_place_by_vertex.close()


def placement_report_with_partitionable_graph_by_vertex(
        report_folder, hostname, graph, graph_mapper, placements):
    """
    Generate report on the placement of sub-vertices onto cores by vertex.
    :param report_folder: the folder to which the reports are being written
    :param hostname: the machiens hostname to which the placer worked on
    :param graph: the partitionable graph to which placements were built
    :param graph_mapper: the mapping between partitionable and partitioned
    graphs
    :param placements: the placements objects built by the placer.
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

    vertices = sorted(graph.vertices, key=lambda x: x.label)
    for v in vertices:
        vertex_name = v.label
        vertex_model = v.model_name
        num_atoms = v.n_atoms
        f_place_by_vertex.write(
            "**** Vertex: '{}'\n".format(vertex_name))
        f_place_by_vertex.write("Model: {}\n".format(vertex_model))
        f_place_by_vertex.write("Pop sz: {}\n".format(num_atoms))
        f_place_by_vertex.write("Sub-vertices: \n")

        partitioned_vertices = \
            sorted(graph_mapper.get_subvertices_from_vertex(v),
                   key=lambda vert: vert.label)
        partitioned_vertices = \
            sorted(partitioned_vertices,
                   key=lambda pvert:
                   graph_mapper.get_subvertex_slice(pvert).lo_atom)
        for sv in partitioned_vertices:
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


def placement_report_without_partitionable_graph_by_vertex(
        report_folder, hostname, placements, partitioned_graph):
    """
    Generate report on the placement of sub-vertices onto cores by vertex.
    :param report_folder: the folder to which the reports are being written
    :param hostname: the machiens hostname to which the placer worked on
    :param placements: the placements objects built by the placer.
    :param partitioned_graph: the partitioned graph generated by the end user
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
        "        Placement Information by AbstractConstrainedVertex\n")
    f_place_by_vertex.write("        ===============================\n\n")
    time_date_string = time.strftime("%c")
    f_place_by_vertex.write("Generated: {}".format(time_date_string))
    f_place_by_vertex.write(" for target machine '{}'".format(hostname))
    f_place_by_vertex.write("\n\n")

    used_processors_by_chip = dict()
    used_sdram_by_chip = dict()
    subvertex_by_processor = dict()

    vertices = sorted(partitioned_graph.subvertices, key=lambda sub: sub.label)
    for v in vertices:
        vertex_name = v.label
        vertex_model = v.model_name
        f_place_by_vertex.write(
            "**** AbstractConstrainedVertex: '{}'\n".format(vertex_name))
        f_place_by_vertex.write("Model: {}\n".format(vertex_model))

        cur_placement = placements.get_placement_of_subvertex(v)
        x, y, p = cur_placement.x, cur_placement.y, cur_placement.p
        key = "{},{}".format(x, y)
        if key in used_processors_by_chip:
            used_procs = used_processors_by_chip[key]
        else:
            used_procs = list()
            used_sdram_by_chip.update({key: 0})
        subvertex_by_processor["{},{},{}".format(x, y, p)] = v
        new_proc = [p, cur_placement]
        used_procs.append(new_proc)
        used_processors_by_chip.update({key: used_procs})
        my_string = " Placed on core ({}, {}, {}) \n".format(x, y, p)
        f_place_by_vertex.write(my_string)
        f_place_by_vertex.write("\n")
    # Close file:
    f_place_by_vertex.close()


def placement_report_with_partitionable_graph_by_core(
        report_folder, hostname, placements, machine, graph_mapper):
    """
    Generate report on the placement of sub-vertices onto cores by core.
    :param report_folder: the folder to which the reports are being written
    :param hostname: the machiens hostname to which the placer worked on
    :param graph_mapper: the mapping between partitionable and partitioned
    graphs
    :param machine: the spinnaker machine object
    :param placements: the placements objects built by the placer.
    """

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


def placement_report_without_partitionable_graph_by_core(
        report_folder, hostname, placements, machine):
    """
    Generate report on the placement of sub-vertices onto cores by core.
    :param report_folder: the folder to which the reports are being written
    :param hostname: the machiens hostname to which the placer worked on
    :param machine: the spinnaker machine object
    :param placements: the placements objects built by the placer.
    """

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

                vertex_label = subvertex.label
                vertex_model = subvertex.model_name

                p_str = ("  Processor {}: AbstractConstrainedVertex: '{}' \n"
                         .format(proc_id, vertex_label))
                f_place_by_core.write(p_str)
                f_place_by_core.write(p_str)
                p_str = "              Model: {}\n\n".format(vertex_model)
                f_place_by_core.write(p_str)
                f_place_by_core.write("\n")
    # Close file:
    f_place_by_core.close()


def sdram_usage_report_per_chip(report_folder, hostname, placements, machine):
    """
    reports the sdram used per chip
    :param report_folder: the folder to which the reports are being written
    :param hostname: the machiens hostname to which the placer worked on
    :param placements: the placements objects built by the placer.
    :param machine: the python spinnmanchine object
    :return None
    """

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

    placements = sorted(placements.placements, key=lambda x: x.subvertex.label)

    for cur_placement in placements:
        subvert = cur_placement.subvertex
        requirements = subvert.resources_required

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
    """
    generates a report whcih says which keys is being allocated to each
    subvertex
    :param report_folder: the
    :param subgraph:
    :param routing_infos:
    """
    file_name = os.path.join(report_folder,
                             "virtual_key_space_information_report.rpt")
    output = None
    try:
        output = open(file_name, "w")
    except IOError:
        logger.error("generate virtual key space information report: "
                     "Can't open file {} for writing.".format(file_name))

    partitioned_vertices = sorted(subgraph.subvertices, key=lambda x: x.label)
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
