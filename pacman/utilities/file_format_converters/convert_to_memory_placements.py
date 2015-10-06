"""

"""
from pacman.model.placements.placement import Placement
from pacman.model.placements.placements import Placements
from pacman import exceptions
from pacman.utilities import file_format_schemas

import os
import json
import validictory
from



class ConvertToMemoryPlacements(object):
    """

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
        file_allocations = json.load(allocations)
        constraints = json.load(constraints)

        self._validate_file_read_data(
            file_placements, file_allocations, constraints)

        memory_placements = Placements()

        # process placements
        for vertex_label in file_placements:
            subvertex = partitioned_graph.get_subvertex_with_label(vertex_label)
            if subvertex is None:
                raise exceptions.PacmanConfigurationException(
                    "Failed to locate the partitioned vertex in the "
                    "partitioned graph with label {}".format(vertex_label))
            if vertex_label not in file_allocations:
                # virtual chip or tag chip
                constraints_for_vertex = self._locate_constraints(
                    vertex_label, constraints)
                if self._valid_constraints_for_external_device(
                        constraints_for_vertex):


                elif self._valid_constraints_for_tag(constraints_for_vertex):



                else:
                    raise exceptions.PacmanConfigurationException(
                        "I dont recongise this pattern of constraints for a"
                        "vertex which does not have a placement")
            else:
                memory_placements.add_placement(
                    Placement(x=file_placements[vertex_label][0],
                              y=file_placements[vertex_label][1],
                              p=file_allocations[vertex_label][0],
                              subvertex=subvertex))

        # return the file format
        return {"MemoryPlacements": memory_placements}

    @staticmethod
    def _valid_constraints_for_tag(constraints_for_vertex):
        """

        :param constraints_for_vertex:
        :return:
        """
        for constraint in constraints_for_vertex:
            if constraint['type'] == "reserve_resource" and

    @staticmethod
    def _valid_constraints_for_external_device(constraints_for_vertex):
        """
        search for the constraint pattern which represetns a external device
        :param constraints_for_vertex: constraints for a vertex
        :return: bool
        """
        found_route_end_point = False
        found_placement_constraint = False
        for constraint in constraints_for_vertex:
            if constraint['type'] == "location":
                found_placement_constraint = True
            if constraint['type'] == "route_endpoint":
                found_route_end_point = True
        if found_placement_constraint and found_route_end_point:
            return True
        else:
            return False

    @staticmethod
    def _validate_file_read_data(
            file_placements, file_allocations, constraints):
        # verify that the files meet the schema.
        # validate the schema
        file_placements_schema_file_path = os.path.join(
            file_format_schemas.__file__, "placements.json"
        )
        file_allocations_schema_file_path = os.path.join(
            file_format_schemas.__file__, "core_allocations.json"
        )
        file_constraints_schema_file_path = os.path.join(
            file_format_schemas.__file__, "constraints.json"
        )

        validictory.validate(
            file_placements, file_placements_schema_file_path)
        validictory.validate(
            file_allocations, file_allocations_schema_file_path)
        validictory.validate(
            constraints, file_constraints_schema_file_path)

    @staticmethod
    def _locate_constraints(vertex_label, constraints):
        found_constraints = []
        for constraint in constraints:
            if "vertex" in constraint and constraint['vertex'] == vertex_label:
                found_constraints.append(constraint)
        return found_constraints
