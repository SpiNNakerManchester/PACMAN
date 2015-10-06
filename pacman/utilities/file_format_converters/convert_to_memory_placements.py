"""

"""
from pacman.model.placements.placement import Placement
from pacman.model.placements.placements import Placements
from pacman import exceptions
from pacman.utilities import file_format_schemas

import os
import json
import validictory


class ConvertToMemoryPlacements(object):
    """
    ConvertToMemoryPlacements: takes the fileplacemenmts, machine,
    partitioned graph and constraints and builds a memory placements object
    """

    def __call__(self, placements, allocations, partitioned_graph,
                 extended_machine, constraints):
        """

        :param placements:
        :param allocations:
        :param partitioned_graph:
        :param extended_machine:
        :param constraints:
        :return:
        """

        # load the json files
        file_placements = json.load(placements)
        core_allocations = json.load(allocations)
        constraints = json.load(constraints)

        self._validate_file_read_data(
            file_placements, core_allocations, constraints)

        memory_placements = Placements()

        # process placements
        for vertex_label in file_placements:
            subvertex = partitioned_graph.get_subvertex_with_label(vertex_label)
            if vertex_label not in core_allocations:
                if subvertex is not None:
                    # virtual chip or tag chip
                    constraints_for_vertex = self._locate_constraints(
                        vertex_label, constraints)
                    external_device_constraints = \
                        self._valid_constraints_for_external_device(
                            constraints_for_vertex)
                    if len(external_device_constraints) != 0:
                        route_constraint = \
                            external_device_constraints['end_point']
                        route_direction = route_constraint['direction']


                    else:
                        raise exceptions.PacmanConfigurationException(
                            "I dont recongise this pattern of constraints for a"
                            "vertex which does not have a placement")
            else:
                if subvertex is None:
                    raise exceptions.PacmanConfigurationException(
                        "Failed to locate the partitioned vertex in the "
                        "partitioned graph with label {}".format(vertex_label))
                else:
                    memory_placements.add_placement(
                        Placement(x=file_placements[vertex_label][0],
                                  y=file_placements[vertex_label][1],
                                  p=core_allocations[vertex_label][0],
                                  subvertex=subvertex))

        # return the file format
        return {"MemoryPlacements": memory_placements}

    @staticmethod
    def _valid_constraints_for_external_device(constraints_for_vertex):
        """
        search for the constraint pattern which represetns a external device
        :param constraints_for_vertex: constraints for a vertex
        :return: bool
        """
        found_route_end_point = None
        found_placement_constraint = None
        for constraint in constraints_for_vertex:
            if constraint['type'] == "location":
                found_placement_constraint = constraint
            if constraint['type'] == "route_endpoint":
                found_route_end_point = constraint
        if (found_placement_constraint is not None
                and found_route_end_point is not None):
            return {'end_point': found_route_end_point,
                    'placement': found_placement_constraint}
        else:
            return {}

    @staticmethod
    def _validate_file_read_data(
            file_placements, file_allocations, constraints):
        # verify that the files meet the schema.
        # locate schemas
        file_placements_schema_file_path = os.path.join(
            os.path.dirname(file_format_schemas.__file__), "placements.json"
        )
        file_allocations_schema_file_path = os.path.join(
            os.path.dirname(file_format_schemas.__file__),
            "core_allocations.json"
        )
        file_constraints_schema_file_path = os.path.join(
            os.path.dirname(file_format_schemas.__file__), "constraints.json"
        )

        # open readers for schemas and read in schema
        file_to_read = open(file_placements_schema_file_path, "r")
        placements_schema = json.load(file_to_read)

        file_to_read = open(file_allocations_schema_file_path, "r")
        core_allocations_schema = json.load(file_to_read)

        file_to_read = open(file_constraints_schema_file_path, "r")
        constraints_schema = json.load(file_to_read)

        validictory.validate(
            file_placements, placements_schema)
        validictory.validate(
            file_allocations, core_allocations_schema)
        validictory.validate(
            constraints, constraints_schema)

    @staticmethod
    def _locate_constraints(vertex_label, constraints):
        found_constraints = []
        for constraint in constraints:
            if "vertex" in constraint and constraint['vertex'] == vertex_label:
                found_constraints.append(constraint)
        return found_constraints
