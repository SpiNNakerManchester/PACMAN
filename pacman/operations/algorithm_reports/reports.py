import os
import time
import logging

from pacman.model.placements import placement
from pacman import exceptions
from pacman.utilities.utility_objs.progress_bar import ProgressBar
from spinn_machine.sdram import SDRAM

logger = logging.getLogger(__name__)


def tag_allocator_report(report_folder, tag_infos):
    pass


def placer_reports_with_partitionable_graph(
        report_folder, hostname, graph, graph_mapper, placements, machine):
    """ Reports that can be produced from placement given a partitionable\
        graph's existence
    :param report_folder: the folder to which the reports are being written
    :param hostname: the machine's hostname to which the placer worked on
    :param graph: the partitionable graph to which placements were built
    :param graph_mapper: the mapping between partitionable and partitioned \
                graphs
    :param placements: the placements objects built by the placer.
    :param machine: the python machine object
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
    :param report_folder: the folder to which the reports are being written
    :param hostname: the machine's hostname to which the placer worked on
    :param placements: the placements objects built by the placer.
    :param machine: the python machine object
    :param sub_graph: the partitioned graph to which the reports are to\
             operate on
    :return None
    """
    placement_report_without_partitionable_graph_by_vertex(
        report_folder, hostname, placements, sub_graph)
    placement_report_without_partitionable_graph_by_core(
        report_folder, hostname, placements, machine)
    sdram_usage_report_per_chip(
        report_folder, hostname, placements, machine)


def router_report_from_paths(
        report_folder, routing_paths, hostname, partitioned_graph):
    """ Generates a text file of routing paths

    :param routing_paths:
    :param report_folder:
    :param hostname:
    :param partitioned_graph:
    :return:
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

    progress_bar = ProgressBar(len(partitioned_graph.subedges),
                               "Generating Routing path report")
    """
    for e in partitioned_graph.subedges:
        text = "**** SubEdge '{}', from vertex: '{}' to vertex: '{}'".format(
            e.label, e.pre_subvertex.label, e.post_subvertex.label)
        f_routing.write(text)
        f_routing.write("\n")

        path_entries = locate_routing_table_entries()
        path_entries = routing_paths.get_entries_for_edge(e)
        first = True
        for entry in path_entries:
            if not first:
                text = "--->"
            else:
                text = ""
            if len(entry.incoming_processor) != 0:
                text = text + "P{}".format(entry.incoming_processor)
            else:
                text = "(L:{}".format(link_labels[entry.incoming_link])
            text += "->{}:{}".format(entry.router_x, entry.router_y)
            if entry.defaultable:
                text += ":D"
            if len(entry.out_going_processors) != 0:
                for processor in entry.out_going_processors:
                    text = text + "->P{}".format(processor)
            if len(entry.out_going_links) != 0:
                for link in entry.out_going_links:
                    text += "->{}".format(link_labels[link])
            f_routing.write(text)
        f_routing.write("\n")

        text = "{} has route length: {}\n".format(e.label, len(path_entries))
        f_routing.write(text)

        # End one entry:
        f_routing.write("\n")
        progress_bar.update()
    f_routing.flush()
    f_routing.close()
    """
    progress_bar.end()


def partitioner_report(report_folder, hostname, graph, graph_mapper):
    """ Generate report on the placement of sub-vertices onto cores.
    """

    # Cycle through all vertices, and for each cycle through its sub-vertices.
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
    progress_bar = ProgressBar(len(vertices),
                               "Generating partitioner report")
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
        progress_bar.update()

    # Close file:
    f_place_by_vertex.close()
    progress_bar.end()


def placement_report_with_partitionable_graph_by_vertex(
        report_folder, hostname, graph, graph_mapper, placements):
    """ Generate report on the placement of sub-vertices onto cores by vertex.

    :param report_folder: the folder to which the reports are being written
    :param hostname: the machine's hostname to which the placer worked on
    :param graph: the partitionable graph to which placements were built
    :param graph_mapper: the mapping between partitionable and partitioned\
            graphs
    :param placements: the placements objects built by the placer.
    """

    # Cycle through all vertices, and for each cycle through its sub-vertices.
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
    progress_bar = ProgressBar(len(vertices),
                               "Generating placement report")
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
                   key=lambda vert:
                   graph_mapper.get_subvertex_slice(vert).lo_atom)
        for sv in partitioned_vertices:
            lo_atom = graph_mapper.get_subvertex_slice(sv).lo_atom
            hi_atom = graph_mapper.get_subvertex_slice(sv).hi_atom
            num_atoms = hi_atom - lo_atom + 1
            cur_placement = placements.get_placement_of_subvertex(sv)
            x, y, p = cur_placement.x, cur_placement.y, cur_placement.p
            key = "{},{}".format(x, y)
            if key in used_processors_by_chip:
                used_pros = used_processors_by_chip[key]
            else:
                used_pros = list()
                used_sdram_by_chip.update({key: 0})
            subvertex_by_processor["{},{},{}".format(x, y, p)] = sv
            new_pro = [p, cur_placement]
            used_pros.append(new_pro)
            used_processors_by_chip.update({key: used_pros})
            my_string = "  Slice {}:{} ({} atoms) on core ({}, {}, {}) \n"\
                        .format(lo_atom, hi_atom, num_atoms, x, y, p)
            f_place_by_vertex.write(my_string)
        f_place_by_vertex.write("\n")
        progress_bar.update()

    # Close file:
    f_place_by_vertex.close()
    progress_bar.end()


def placement_report_without_partitionable_graph_by_vertex(
        report_folder, hostname, placements, partitioned_graph):
    """ Generate report on the placement of sub-vertices onto cores by vertex.
    :param report_folder: the folder to which the reports are being written
    :param hostname: the machine's hostname to which the placer worked on
    :param placements: the placements objects built by the placer.
    :param partitioned_graph: the partitioned graph generated by the end user
    """

    # Cycle through all vertices, and for each cycle through its sub-vertices.
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
    progress_bar = ProgressBar(len(vertices),
                               "Generating placement report")
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
            used_pros = used_processors_by_chip[key]
        else:
            used_pros = list()
            used_sdram_by_chip.update({key: 0})
        subvertex_by_processor["{},{},{}".format(x, y, p)] = v
        new_pro = [p, cur_placement]
        used_pros.append(new_pro)
        used_processors_by_chip.update({key: used_pros})
        my_string = " Placed on core ({}, {}, {}) \n".format(x, y, p)
        f_place_by_vertex.write(my_string)
        f_place_by_vertex.write("\n")
        progress_bar.update()

    # Close file:
    f_place_by_vertex.close()
    progress_bar.end()


def placement_report_with_partitionable_graph_by_core(
        report_folder, hostname, placements, machine, graph_mapper):
    """ Generate report on the placement of sub-vertices onto cores by core.

    :param report_folder: the folder to which the reports are being written
    :param hostname: the machine's hostname to which the placer worked on
    :param graph_mapper: the mapping between partitionable and partitioned\
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
    progress_bar = ProgressBar(len(list(machine.chips)),
                               "Generating placement by core report")
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
                pro_id = processor.processor_id
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
                             pro_id, vertex_label, vertex_atoms))
                f_place_by_core.write(p_str)
                p_str = ("              Slice on this core: {}:{} ({} atoms)\n"
                         .format(lo_atom, hi_atom, num_atoms))
                f_place_by_core.write(p_str)
                p_str = "              Model: {}\n\n".format(vertex_model)
                f_place_by_core.write(p_str)
                f_place_by_core.write("\n")
        progress_bar.update()

    # Close file:
    f_place_by_core.close()
    progress_bar.end()


def placement_report_without_partitionable_graph_by_core(
        report_folder, hostname, placements, machine):
    """ Generate report on the placement of sub-vertices onto cores by core.

    :param report_folder: the folder to which the reports are being written
    :param hostname: the machine's hostname to which the placer worked on
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

    progress_bar = ProgressBar(len(list(machine.chips)),
                               "Generating placement by core report")
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
                pro_id = processor.processor_id
                subvertex = \
                    placements.get_subvertex_on_processor(
                        chip.x, chip.y, processor.processor_id)

                vertex_label = subvertex.label
                vertex_model = subvertex.model_name

                p_str = ("  Processor {}: AbstractConstrainedVertex: '{}' \n"
                         .format(pro_id, vertex_label))
                f_place_by_core.write(p_str)
                f_place_by_core.write(p_str)
                p_str = "              Model: {}\n\n".format(vertex_model)
                f_place_by_core.write(p_str)
                f_place_by_core.write("\n")
        progress_bar.update()

    # Close file:
    f_place_by_core.close()
    progress_bar.end()


def sdram_usage_report_per_chip(report_folder, hostname, placements, machine):
    """ Reports the SDRAM used per chip

    :param report_folder: the folder to which the reports are being written
    :param hostname: the machine's hostname to which the placer worked on
    :param placements: the placements objects built by the placer.
    :param machine: the python machine object
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

    progress_bar = ProgressBar(len(placements) + len(list(machine.chips)),
                               "Generating sdram usage report")
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
        progress_bar.update()

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
            progress_bar.update()
        except KeyError:

            # Do Nothing
            pass

    # Close file:
    f_mem_used_by_core.close()
    progress_bar.end()


def routing_info_report(report_folder, partitioned_graph, routing_infos):
    """ Generates a report which says which keys is being allocated to each\
        subvertex
    :param report_folder: the
    :param partitioned_graph:
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
    progress_bar = ProgressBar(len(partitioned_graph.subvertices),
                               "Generating Routing info report")
    for subvert in partitioned_graph.subvertices:
        output.write("Subvert: {} \n".format(subvert))
        partitions = \
            partitioned_graph.outgoing_edges_partitions_from_vertex(subvert)
        for partition in partitions.values():
            keys_and_masks = \
                routing_infos.get_keys_and_masks_from_partition(partition)
            for subedge in partition.edges:
                output.write("subedge:{}, keys_and_masks:{} \n".format(
                    subedge, keys_and_masks))
        output.write("\n\n")
        progress_bar.update()
    progress_bar.end()
    output.flush()
    output.close()


def router_report_from_router_tables(report_folder, routing_tables):
    """

    :param report_folder:
    :param routing_tables:
    :return:
    """

    top_level_folder = os.path.join(report_folder, "routing_tables_generated")
    if not os.path.exists(top_level_folder):
        os.mkdir(top_level_folder)
    progress_bar = ProgressBar(len(routing_tables.routing_tables),
                               "Generating Router table report")

    for routing_table in routing_tables.routing_tables:
        if routing_table.number_of_entries > 0:
            _generate_routing_table(routing_table, top_level_folder)
        progress_bar.update()
    progress_bar.end()


def router_report_from_compressed_router_tables(report_folder, routing_tables):
    """

    :param report_folder:
    :param routing_tables:
    :return:
    """

    top_level_folder = os.path.join(report_folder,
                                    "compressed_routing_tables_generated")
    if not os.path.exists(top_level_folder):
        os.mkdir(top_level_folder)
    progress_bar = ProgressBar(len(routing_tables.routing_tables),
                               "Generating compressed router table report")

    for routing_table in routing_tables.routing_tables:
        if routing_table.number_of_entries > 0:
            _generate_routing_table(routing_table, top_level_folder)
        progress_bar.update()
    progress_bar.end()


def _generate_routing_table(routing_table, top_level_folder):
    file_sub_name = "routing_table_{}_{}.rpt".format(
        routing_table.x, routing_table.y)
    file_name = os.path.join(top_level_folder, file_sub_name)
    output = None
    try:
        output = open(file_name, "w")
    except IOError:
        logger.error("Generate_placement_reports: Can't open file"
                     " {} for writing.".format(file_name))

    output.write("router contains {} entries \n "
                 "\n".format(routing_table.number_of_entries))
    output.write("  Index   Key(hex)    Mask(hex)    Route(hex)"
                 "    Src. Core -> [Cores][Links]\n")
    output.write("----------------------------------------------"
                 "--------------------------------\n")

    entry_count = 0
    n_defaultable = 0
    for entry in routing_table.multicast_routing_entries:
        index = entry_count & 0xFFFF
        key = entry.routing_entry_key
        mask = entry.mask
        hex_route = _reduce_route_value(entry.processor_ids,
                                        entry.link_ids)
        hex_key = _uint_32_to_hex_string(key)
        hex_mask = _uint_32_to_hex_string(mask)
        route_txt = _expand_route_value(entry.processor_ids,
                                        entry.link_ids)
        entry_str = (
            "    {}     {}       {}      {}         {}        {}\n".format(
                index, hex_key, hex_mask, hex_route, entry.defaultable,
                route_txt))
        entry_count += 1
        if entry.defaultable:
            n_defaultable += 1
        output.write(entry_str)
    output.write("{} Defaultable entries\n".format(n_defaultable))
    output.flush()
    output.close()


def generate_comparison_router_report(
        report_folder, routing_tables, compressed_routing_tables):
    """
    makes a report on comparision of the compressed and uncompressed
    routing tables
    :param report_folder:
    :param routing_tables:
    :param compressed_routing_tables:
    :return:
    """
    file_name = os.path.join(
        report_folder, "comparison_of_compressed_uncompressed_routing_tables")

    output = None
    try:
        output = open(file_name, "w")
    except IOError:
        logger.error("Generate_router_comparison_reports: Can't open file"
                     " {} for writing.".format(file_name))

    progress_bar = ProgressBar(len(routing_tables.routing_tables),
                               "Generating comparison of router table report")

    for uncompressed_table in routing_tables.routing_tables:
        x = uncompressed_table.x
        y = uncompressed_table.y
        compressed_table = compressed_routing_tables.\
            get_routing_table_for_chip(x, y)

        n_entries_un_compressed = uncompressed_table.number_of_entries
        n_entries_compressed = compressed_table.number_of_entries
        percentage = ((float(n_entries_un_compressed - n_entries_compressed)) /
                      float(n_entries_un_compressed)) * 100

        output.write(
            "Uncompressed table at {}:{} has {} entries whereas compressed "
            "table has {} entries. This is a decrease of {} %\n".format(
                x, y, n_entries_un_compressed, n_entries_compressed,
                percentage))
        progress_bar.update()
    progress_bar.end()
    output.flush()
    output.close()


def _reduce_route_value(processors_ids, link_ids):
    value = 0
    for link in link_ids:
        value += 1 << link
    for processor in processors_ids:
        value += 1 << (processor + 6)
    return _uint_32_to_hex_string(value)


def _uint_32_to_hex_string(number):
    """ Convert a 32-bit unsigned number into a hex string.
    """
    return "0x{:08X}".format(number)


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
        routing_table.get_multicast_routing_entry_by_routing_entry_key(
            key_combo, mask)

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
