import os
import time
import logging
from pacman.utilities.sdram_tracker import SDRAMTracker

from spinn_machine.sdram import SDRAM

logger = logging.getLogger(__name__)


def placer_report(report_folder, hostname, graph, graph_to_subgraph_mapper,
                  placements, machine):
    placement_report_by_vertex(report_folder, hostname, graph,
                               graph_to_subgraph_mapper, placements)
    placement_by_core(report_folder, hostname, placements, machine,
                      graph_to_subgraph_mapper)
    sdram_usage_per_chip(report_folder, hostname, placements, machine,
                         graph_to_subgraph_mapper, graph)


def router_report(report_folder, hostname, graph, graph_to_sub_graph_mapper,
                  placements, include_dat_based=False):
    router_report_from_router_tables(report_folder)
    router_edge_information(report_folder, hostname, graph,
                            graph_to_sub_graph_mapper, placements)
    if include_dat_based:
        router_report_from_dat_file(report_folder)


def routing_info_report(report_folder):
    pass


def partitioner_report(report_folder, hostname, graph,
                       graph_to_subgraph_mapper):
    """
    Generate report on the placement of sub-vertices onto cores.
    """
    # Cycle through all vertices, and foreach cycle through its sub-vertices.
    # For each sub-vertex, describe its core mapping.
    file_name = report_folder + os.sep + "placement_by_vertex.rpt"
    f_place_by_vertex = None
    try:
        f_place_by_vertex = open(file_name, "w")
    except IOError:
        logger.error("Generate_placement_reports: Can't open file {} for"
                     " writing.".format(file_name))

    f_place_by_vertex.write("        Placement Information by Vertex\n")
    f_place_by_vertex.write("        ===============================\n\n")
    time_date_string = time.strftime("%c")
    f_place_by_vertex.write("Generated: {}".format(time_date_string))
    f_place_by_vertex.write(" for target machine '{}'".format(hostname))
    f_place_by_vertex.write("\n\n")

    for v in graph._vertices:
        vertex_name = v.label
        vertex_model = v.model_name
        num_atoms = v.n_atoms
        f_place_by_vertex.write("**** Vertex: '{}'\n".format(vertex_name))
        f_place_by_vertex.write("Model: {}\n".format(vertex_model))
        f_place_by_vertex.write("Pop sz: {}\n".format(num_atoms))
        f_place_by_vertex.write("Sub-vertices: \n")

        for sv in graph_to_subgraph_mapper.get_subvertices_from_vertex(v):
            lo_atom = sv.lo_atom
            hi_atom = sv.hi_atom
            num_atoms = hi_atom - lo_atom + 1
            my_string = "  Slice {}:{} ({} atoms) \n"\
                        .format(lo_atom, hi_atom, num_atoms)
            f_place_by_vertex.write(my_string)
        f_place_by_vertex.write("\n")
    # Close file:
    f_place_by_vertex.close()


def placement_report_by_vertex(report_folder, hostname, graph,
                               graph_to_subgraph_mapper, placements):
    """
    Generate report on the placement of sub-vertices onto cores.
    """
    # Cycle through all vertices, and foreach cycle through its sub-vertices.
    # For each sub-vertex, describe its core mapping.
    file_name = report_folder + os.sep + "placement_by_vertex.rpt"
    f_place_by_vertex = None
    try:
        f_place_by_vertex = open(file_name, "w")
    except IOError:
        logger.error("Generate_placement_reports: Can't open file {} for"
                     " writing.".format(file_name))

    f_place_by_vertex.write("        Placement Information by Vertex\n")
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
        f_place_by_vertex.write("**** Vertex: '{}'\n".format(vertex_name))
        f_place_by_vertex.write("Model: {}\n".format(vertex_model))
        f_place_by_vertex.write("Pop sz: {}\n".format(num_atoms))
        f_place_by_vertex.write("Sub-vertices: \n")

        for sv in graph_to_subgraph_mapper.get_subvertices_from_vertex(v):
            lo_atom = sv.lo_atom
            hi_atom = sv.hi_atom
            num_atoms = hi_atom - lo_atom + 1
            placement = placements.get_placement_of_subvertex(sv)
            x, y, p = placement.x, placement.y, placement.p
            key = "{},{}".format(x, y)
            if key in used_processors_by_chip.keys():
                used_procs = used_processors_by_chip[key]
            else:
                used_procs = list()
                used_sdram_by_chip.update({key: 0})
            subvertex_by_processor["{},{},{}".format(x, y, p)] = sv
            new_proc = [p, placement]
            used_procs.append(new_proc)
            used_processors_by_chip.update({key: used_procs})
            my_string = "  Slice {}:{} ({} atoms) on core ({}, {}, {}) \n"\
                        .format(lo_atom, hi_atom, num_atoms, x, y, p)
            f_place_by_vertex.write(my_string)
        f_place_by_vertex.write("\n")
    # Close file:
    f_place_by_vertex.close()


def placement_by_core(report_folder, hostname, placements, machine,
                      graph_to_subgraph_mapper):

    # File 2: Placement by core.
    # Cycle through all chips and by all cores within each chip.
    # For each core, display what is held on it.
    file_name = report_folder + os.sep + "placement_by_core.rpt"
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
            if placements.get_subvertex_on_processor(chip.x, chip.y,
                                                     processor.processor_id) \
               is not None:
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
                    graph_to_subgraph_mapper\
                    .get_vertex_from_subvertex(subvertex)
                vertex_label = vertex.label
                vertex_model = vertex.model_name
                vertex_atoms = vertex.n_atoms
                lo_atom = subvertex.lo_atom
                hi_atom = subvertex.hi_atom
                num_atoms = hi_atom - lo_atom + 1
                p_str = "  Processor {}: Vertex: '{}', pop sz: {}\n"\
                        .format(proc_id, vertex_label, vertex_atoms)
                f_place_by_core.write(p_str)
                p_str = "               Slice on this core: {}:{} ({} atoms)\n"\
                        .format(lo_atom, hi_atom, num_atoms)
                f_place_by_core.write(p_str)
                p_str = "               Model: {}\n\n".format(vertex_model)
                f_place_by_core.write(p_str)
                f_place_by_core.write("\n")
    # Close file:
    f_place_by_core.close()


def sdram_usage_per_chip(report_folder, hostname, placements, machine,
                         graph_to_subgraph_mapper, graph):
    file_name = report_folder + os.sep + "chip_sdram_usage_by_core.rpt"
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
    used_sdram_by_chip = SDRAMTracker()

    for placement in placements.placements:
        subvert = placement.subvertex
        vertex = graph_to_subgraph_mapper.get_vertex_from_subvertex(subvert)
        vertex_in_edges = graph.incoming_edges_to_vertex(vertex)
        requirements = \
            vertex.get_resources_used_by_atoms(subvert.lo_atom, subvert.hi_atom,
                                               vertex_in_edges)

        x, y, p = placement.x, placement.y, placement.p
        f_mem_used_by_core.write(
            "SDRAM requirements for core ({},{},{}) is {} KB\n".format(
            x, y, p, int(requirements.sdram.get_value() / 1024.0)))
        used_sdram_by_chip.add_usage(x, y, requirements.sdram.get_value())

    for chip in machine.chips:
        try:
            used_sdram = used_sdram_by_chip.get_usage(chip.x, chip.y)
            if used_sdram != 0:
                f_mem_used_by_core.write(
                    "**** Chip: ({}, {}) has total memory usage of"
                    " {} KB out of a max of "
                    "{} MB \n\n".format(chip.x, chip.y, int(used_sdram / 1024.0),
                                        int(SDRAM.DEFAULT_SDRAM_BYTES /
                                            (1024.0 * 1024.0))))
        except KeyError:
            # Do Nothing
            pass
    # Close file:
    f_mem_used_by_core.close()


def router_report_from_router_tables(report_folder):
    pass


def router_report_from_dat_file(report_folder):
    pass


#ToDO NOT CHECKED YET
def router_edge_information(report_folder, hostname, graph,
                            graph_to_subgraph_mapper, placements):
    """
    Generate report on the routing of sub-edges across the machine.
    """
    file_name = report_folder + os.sep + "edge_routing_info.rpt"
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

    for e in graph.edges:
        from_v, to_v = e.pre_vertex, e.post_vertex
        from_v_sz, to_v_sz = from_v.n_atoms, to_v.n_atoms
        fr_v_name, to_v_name = from_v.label, to_v.label
        string = "**** Edge '{}', from vertex: '{}' (size: {})"\
                 .format(e.label, fr_v_name, from_v_sz)
        string = "{}, to vertex: '{}' (size: {})\n"\
                 .format(string, to_v_name, to_v_sz)
        f_routing.write(string)
        subedges = graph_to_subgraph_mapper.get_subedges_from_edge(e)
        f_routing.write("Sub-edges: {}\n".format(len(subedges)))

        for se in subedges:
            fr_sv, to_sv = se.pre_subvertex, se.post_subvertex
            fr_placement = placements.get_placement_of_subvertex(fr_sv)
            to_placement = placements.get_placement_of_subvertex(to_sv)
            if se.routing is not None:
                route_steps = se.routing.routing_entries
                route_len = len(route_steps)
                fr_core = "(%d, %d, %d)" % (fr_proc.get_coordinates())
                to_core = "(%d, %d, %d)" % (to_proc.get_coordinates())
                fr_atoms = "%d:%d" % (fr_sv.lo_atom, fr_sv.hi_atom)
                to_atoms = "%d:%d" % (to_sv.lo_atom, to_sv.hi_atom)
                string = "Sub-edge from core %s, atoms %s," % (fr_core, fr_atoms)
                string = "%s to core %s, atoms %s has route length: %d\n" % \
                          (string, to_core, to_atoms, route_len)
                f_routing.write(string)
                # Print route info:
                count_on_this_line = 0
                total_step_count = 0
                for step in route_steps:
                    if total_step_count == 0:
                       entry_str = "((%d, %d, %d)) -> " % (fr_proc.get_coordinates())
                       f_routing.write(entry_str)
                    chip_id = step.router.chip
                    entry_str = "(%d, %d) -> " % (chip_id.x, chip_id.y)
                    f_routing.write(entry_str)
                    if total_step_count == (route_len-1):
                       entry_str = "((%d, %d, %d))" % (to_proc.get_coordinates())
                       f_routing.write(entry_str)

                    total_step_count   += 1
                    count_on_this_line += 1
                    if count_on_this_line == 5:
                        f_routing.write("\n")
                        count_on_this_line = 0
                f_routing.write("\n")

        # End one entry:
        f_routing.write("\n")
    f_routing.flush()
    f_routing.close()