# Copyright (c) 2017-2019 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import logging
from spinn_utilities.log import FormatAdapter

logger = FormatAdapter(logging.getLogger())
_REPORT_FILENAME = "placement_isomorph.rpt"


class IsomorphicChecker(object):
    """ A short algorithm to check if there is an isomorphism of the placement\
        of vertices by two separate placement algorithms. One of the\
        algorithms must output to memory placements_copy in its method and\
        ``<param_type>MemoryPlacements2</param_type>`` in\
        ``algorithms_metadata.xml``.
    """

    def __call__(self, report_folder, placements, placements_copy):
        """ Outputs the result of the isomorphic check to a file.

        :param str report_folder:
            the folder to which the reports are being written
        :param Placements placements:
        :param Placements placements_copy:
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

        :param Placements placements: Placements of vertices on the machine
        :param Placements placements_copy: \
            memory copy of placements of vertices on the machine
        :return: True if the placements are the same
        :rtype: tuple(bool, set(MachineVertex), set(MachineVertex))
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
