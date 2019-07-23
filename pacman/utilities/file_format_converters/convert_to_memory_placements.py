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

import json
from six import text_type
from pacman.model.placements import Placement, Placements
from pacman.exceptions import PacmanConfigurationException
from pacman.utilities.constants import EDGES
from pacman.utilities.file_format_schemas import validate


class ConvertToMemoryPlacements(object):
    """ Takes the file-based placements, machine, machine graph and\
        constraints and builds a memory placements object
    """

    __slots__ = []

    def __call__(self, extended_machine, placements, allocations,
                 constraints, vertex_by_id):
        """
        :param placements:
        :param allocations:
        :param extended_machine:
        :param constraints:
        """

        # load the json files
        file_placements, core_allocations, constraints = \
            self._load_json_files(placements, allocations, constraints)

        # validate the json files against the schemas
        self._validate_file_read_data(
            file_placements, core_allocations, constraints)

        memory_placements = Placements()

        # process placements
        for vertex_id in file_placements:
            if str(vertex_id) not in vertex_by_id:
                if text_type(vertex_id) not in core_allocations:
                    raise PacmanConfigurationException(
                        "I don't recognise this pattern of constraints for"
                        " a vertex which does not have a placement")
                else:
                    raise PacmanConfigurationException(
                        "Failed to locate the vertex in the "
                        "graph with id {}".format(vertex_id))

            if text_type(vertex_id) in core_allocations:
                memory_placements.add_placement(Placement(
                    x=file_placements[vertex_id][0],
                    y=file_placements[vertex_id][1],
                    p=core_allocations[vertex_id][0],
                    vertex=vertex_by_id[str(vertex_id)]))
            else:
                # virtual chip or tag chip
                external_device_constraints = \
                    self._valid_constraints_for_external_device(
                        self._locate_constraints(vertex_id, constraints))
                if external_device_constraints:
                    placements.add(self._make_virtual_placement(
                        extended_machine, vertex_by_id[str(vertex_id)],
                        external_device_constraints))

        # return the file format
        return memory_placements

    @staticmethod
    def _make_virtual_placement(machine, vertex, constraints):
        # get data for virtual chip
        route_constraint = constraints['end_point']
        route_direction = EDGES(route_constraint['direction'].upper())
        placement_constraint = constraints['placement']
        coords = placement_constraint['location']

        # locate virtual chip
        link = machine.get_chip_at(
            coords[0], coords[1]).router.get_link(
            route_direction.value)
        destination_chip = machine.get_chip_at(
            link.destination_x, link.destination_y)

        # create placement
        return Placement(vertex, destination_chip.x, destination_chip.y, None)

    @staticmethod
    def _load_json_files(placements, allocations, constraints):
        """ Read in the 3 JSON files needed for the conversion

        :param placements:
        :param allocations:
        :param constraints:
        """
        with open(placements, "r") as f:
            placements_obj = json.load(f)
        with open(allocations, "r") as f:
            allocations_obj = json.load(f)
        with open(constraints, "r") as f:
            constraints_obj = json.load(f)

        return placements_obj, allocations_obj, constraints_obj

    @staticmethod
    def _valid_constraints_for_external_device(constraints_for_vertex):
        """ Search for the constraint pattern which represents an external\
            device

        :param constraints_for_vertex: constraints for a vertex
        :rtype: bool
        """
        route_end_point = None
        placement_constraint = None
        for constraint in constraints_for_vertex:
            if constraint['type'] == "location":
                placement_constraint = constraint
            if constraint['type'] == "route_endpoint":
                route_end_point = constraint
        if placement_constraint is None or route_end_point is None:
            return {}
        return {'end_point': route_end_point,
                'placement': placement_constraint}

    @staticmethod
    def _validate_file_read_data(
            placements_obj, allocations_obj, constraints_obj):
        # verify that the files meet the schemas.
        validate(placements_obj, "placements.json")
        validate(allocations_obj, "core_allocations.json")
        validate(constraints_obj, "constraints.json")

    @staticmethod
    def _locate_constraints(vertex_label, constraints):
        found_constraints = []
        for constraint in constraints:
            if "vertex" in constraint and constraint['vertex'] == vertex_label:
                found_constraints.append(constraint)
        return found_constraints
