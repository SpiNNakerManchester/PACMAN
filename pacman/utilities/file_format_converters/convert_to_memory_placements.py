
# pacman imports
from pacman.model.placements.placement import Placement
from pacman.model.placements.placements import Placements
from pacman import exceptions
from pacman.utilities import file_format_schemas
from pacman.utilities import constants

# general imports
import os
import json
import jsonschema


class ConvertToMemoryPlacements(object):
    """ Takes the file-based placements, machine, partitioned graph and\
        constraints and builds a memory placements object
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
        file_placements, core_allocations, constraints = \
            self._load_json_files(placements, allocations, constraints)

        # validate the json files against the schemas
        self._validate_file_read_data(
            file_placements, core_allocations, constraints)

        # drop the type and allocations bit of core allocations
        # (makes lower code simpler)
        core_allocations = core_allocations['allocations']

        memory_placements = Placements()

        # process placements
        for vertex_repr in file_placements:
            subvertex = \
                partitioned_graph.get_subvertex_with_repr(vertex_repr)
            if vertex_repr not in core_allocations:
                if subvertex is not None:
                    # virtual chip or tag chip
                    constraints_for_vertex = self._locate_constraints(
                        vertex_repr, constraints)
                    external_device_constraints = \
                        self._valid_constraints_for_external_device(
                            constraints_for_vertex)
                    if len(external_device_constraints) != 0:

                        # get data for virtual chip
                        route_constraint = \
                            external_device_constraints['end_point']
                        route_direction = constants.EDGES(
                            route_constraint['direction'].upper())
                        placement_constraint = \
                            external_device_constraints['placement']
                        coords = placement_constraint['location']

                        # locate virtual chip
                        link = extended_machine.get_chip_at(
                            coords[0], coords[1]).router.get_link(
                            route_direction.value)
                        destination_chip = extended_machine.get_chip_at(
                            link.destination_x, link.destination_y)

                        # create placement
                        placements.add_placement(Placement(
                            subvertex, destination_chip.x, destination_chip.y,
                            None))
                    else:
                        raise exceptions.PacmanConfigurationException(
                            "I don't recognise this pattern of constraints for"
                            " a vertex which does not have a placement")
            else:
                if subvertex is None:
                    raise exceptions.PacmanConfigurationException(
                        "Failed to locate the partitioned vertex in the "
                        "partitioned graph with label {}".format(vertex_repr))
                else:
                    memory_placements.add_placement(
                        Placement(x=file_placements[vertex_repr][0],
                                  y=file_placements[vertex_repr][1],
                                  p=core_allocations[vertex_repr][0],
                                  subvertex=subvertex))

        # return the file format
        return {"placements": memory_placements}

    @staticmethod
    def _load_json_files(placements, allocations, constraints):
        """
        reads in the 3 json files needed for the conversion
        :param placements:
        :param allocations:
        :param constraints:
        :return:
        """

        placments_file = open(placements, "r")
        allocations_file = open(allocations, "r")
        constraints_file = open(constraints, "r")

        file_placements = json.load(placments_file)
        core_allocations = json.load(allocations_file)
        constraints = json.load(constraints_file)

        return file_placements, core_allocations, constraints

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
        if (found_placement_constraint is not None and
                found_route_end_point is not None):
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

        jsonschema.validate(
            file_placements, placements_schema)
        jsonschema.validate(
            file_allocations, core_allocations_schema)
        jsonschema.validate(
            constraints, constraints_schema)

    @staticmethod
    def _locate_constraints(vertex_label, constraints):
        found_constraints = []
        for constraint in constraints:
            if "vertex" in constraint and constraint['vertex'] == vertex_label:
                found_constraints.append(constraint)
        return found_constraints
