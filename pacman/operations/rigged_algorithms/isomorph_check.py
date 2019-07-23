import os
import logging
from spinn_utilities.log import FormatAdapter

logger = FormatAdapter(logging.getLogger())
_REPORT_FILENAME = "placement_isomorph.rpt"


class IsomorphicChecker(object):
    """ A short algorithm to check if there is an isomorphism of the placement\
        of vertices by two separate placement algorithms. One of the\
        algorithms must output to memory placements_copy in its method and\
        <param_type>MemoryPlacements2</param_type> in\
        algorithms_metadata.xml.
    """

    def __call__(self, report_folder, placements, placements_copy):
        """ Outputs the result of the isomorphic check to a file.

        :param report_folder: the folder to which the reports are being written
        :return: None
        """

        file_name = os.path.join(report_folder, _REPORT_FILENAME)
        try:
            with open(file_name, "w") as f:
                eq, first, second = self.check(placements, placements_copy)
                if eq:
                    f.write(
                        "The two algorithms called have the same set of "
                        "placements.\n")
                else:
                    f.write(
                        "The two algorithms have different placements data.\n")
                if first:
                    f.write("\nVertices present only in first placements:\n")
                    f.write("\t" + (",".join(first)) + "\n")
                if second:
                    f.write("\nVertices present only in second placements:\n")
                    f.write("\t" + (",".join(second)) + "\n")
        except IOError:
            logger.exception(
                "Generate_isomorph_report: Can't open file {} for writing.",
                file_name)

    def check(self, placements, placements_copy):
        """ Checks if the placements on each processor are the same for\
            two placement algorithms.

        :param placements: Placements of vertices on the machine
        :type placements: \
            :py:class:`pacman.model.placements.Placements`
        :param placements_copy: \
            memory copy of placements of vertices on the machine
        :type placements_copy: \
            :py:class:`pacman.model.placements.Placements`
        :return: True if the placements are the same
        :rtype: bool
        """

        chip_vertices = set()
        chip_vertices_copy = set()
        chips = set()

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

        # if the two sets are not
        return (chip_vertices != chip_vertices_copy,
                chip_vertices - chip_vertices_copy,
                chip_vertices_copy - chip_vertices)
