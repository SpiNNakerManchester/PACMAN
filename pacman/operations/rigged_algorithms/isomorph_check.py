import os
import logging


class IsomorphicChecker(object):
    """
    A short algorithm to check if there is an isomorphism of the placement
    of vertices by two separate placement algorithms. One of the
    algorithms must output to memory placements_copy in its method and
    <param_type>MemoryPlacements2</param_type> in
    algorithms_metadata.xml."""

    def __call__(self, report_folder, placements, placements_copy):
        """Outputs the result of the isomorphic check to a report file.

        :param report_folder: the folder to which the reports are being written
        :return placement_isomorph.rpt
        :rtype report file
        """

        file_name = os.path.join(report_folder, "placement_isomorph.rpt")
        report = None
        try:
            report = open(file_name, "w")
        except IOError:
            logging.getLogger().error(
                "Generate_isomorph_report: Can't open file {} for "
                "writing.".format(file_name))
        if self.check(placements, placements_copy):
            report.write(
                "The two algorithms called have the same set of placements.")
        else:
            report.write("The two algorithms have different placements data.")
        report.flush()
        report.close()

    def check(self, placements, placements_copy):
        """Checks if the placements on each processor are the same for
        two placement algorithms.

        :param placements: Placements of vertices on the machine
        :type :py:class:`pacman.model.placements.placements.Placements`
        :param placements_copy: memory copy of placements of vertices \
            on the machine
        :type :py:class:`pacman.model.placements.placements.Placements`
        :return True if the placements are the same
        :rtype bool
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
        return chip_vertices != chip_vertices_copy
