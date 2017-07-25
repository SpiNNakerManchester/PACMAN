"""A short algorithm to check if there is an isomorphism of the placement of
vertices by two separate placement algorithms. One of the algorithms must
output to memory placements_copy and
<param_type>MemoryPlacements2</param_type> in the algorithms_metadata.xml."""

import os
import logging


class IsomorphicChecker(object):

    def check(self, placements, placements_copy):
        chip_vertices = set()
        chip_vertices_copy = set()
        chips = set()
        correct = True

        # create a list of processors with assigned vertices
        for x, y, p in placements.get_placed_processors():
            chips.add((x, y))
        # create sets of the vertices on each processor and compare them
        for (x, y) in chips:
            for p in range(0, 18):
                if placements.is_processor_occupied(x, y, p):
                    chip_vertices.add(placements.get_vertex_on_processor(
                        x, y, p))
                if placements_copy.is_processor_occupied(x, y, p):
                    chip_vertices_copy.add(
                        placements_copy.get_vertex_on_processor(x, y, p))
        if chip_vertices != chip_vertices_copy:
            correct = False
        print chips
        return correct

    def __call__(self, report_folder, placements,
                 placements_copy):
        file_name = os.path.join(report_folder, "placement_isomorph.rpt")
        f = None
        try:
            f = open(file_name, "w")
        except IOError:
            logging.getLogger().error("Generate_isomorph_report: Can't open "
                                      "file {} for writing.".format(file_name))
        if self.check(placements, placements_copy):
            f.write("The two algorithms called have the same set of "
                    "placements.")
        else:
            f.write("The two algorithms have different placements data.")
        f.flush()
        f.close()
